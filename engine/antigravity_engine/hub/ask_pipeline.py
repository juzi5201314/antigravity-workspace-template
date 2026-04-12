"""Ask pipeline — answer questions about the project.

Extracted from ``pipeline.py`` to separate the refresh and ask
workflows into dedicated modules.
"""
from __future__ import annotations

import ast
import asyncio
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

from antigravity_engine.hub._constants import SKIP_DIRS
from antigravity_engine.hub.contracts import (
    ClaimVerification,
    ModuleClaim,
    ModuleFactsDocument,
    ModuleRegistryEntry,
    RefreshStatus,
    VerificationResult,
    WorkerEvidence,
)

logger = logging.getLogger(__name__)


async def ask_pipeline(workspace: Path, question: str) -> str:
    """Answer a question about the project.

    Args:
        workspace: Project root directory.
        question: Natural language question.

    Returns:
        Answer string.

    Notes:
        MCP servers are only auto-connected when both ``MCP_ENABLED=true`` and
        ``AG_ALLOW_MCP=true`` are set in the runtime environment.
    """
    from agents import set_tracing_disabled

    set_tracing_disabled(True)

    structured_enabled = os.environ.get("AG_ASK_FORCE_LEGACY", "").strip().lower() not in {
        "1",
        "true",
        "yes",
    }
    if structured_enabled and _structured_artifacts_available(workspace):
        print("[1/4] Loading structured module facts...", file=sys.stderr)
        structured_answer = await _ask_with_structured_facts(workspace, question)
        if structured_answer is not None:
            return structured_answer
        print("[1/4] Structured facts were insufficient; falling back to legacy swarm.", file=sys.stderr)

    return await _ask_with_legacy_swarm(workspace, question)


async def _ask_with_legacy_swarm(workspace: Path, question: str) -> str:
    """Run the legacy multi-agent ask workflow.

    Args:
        workspace: Project root directory.
        question: Natural language question about the project.

    Returns:
        Answer string from the reviewer swarm.
    """

    from antigravity_engine.config import get_settings
    from antigravity_engine.hub.agents import build_reviewer_agent, create_model

    settings = get_settings()
    model = create_model(settings)

    print("[1/3] Gathering project context...", file=sys.stderr)

    # Retrieval-assisted: gather code evidence and feed it to the LLM
    # as additional context rather than returning it directly.  Set
    # AG_ASK_RETRIEVAL_FIRST=2 to restore the old "return immediately" mode.
    retrieval_mode = os.environ.get("AG_ASK_RETRIEVAL_FIRST", "1").strip().lower()
    retrieval_evidence: str | None = None
    if retrieval_mode in {"1", "true", "yes", "2"}:
        retrieval_evidence = _build_retrieval_semantic_answer(workspace, question)
        if retrieval_evidence and retrieval_mode == "2":
            # Legacy mode: return retrieval result directly without LLM.
            print("[2/3] Retrieval-first answer hit; skipping LLM.", file=sys.stderr)
            return retrieval_evidence

    context = _build_ask_context(workspace, question)
    graph_skill_context = None
    if _is_structure_query(question):
        graph_skill_context = _build_graph_skill_context(workspace, question)

    prompt_parts = [f"Project context:\n{context}"]
    if retrieval_evidence:
        prompt_parts.append(f"Code evidence (from retrieval):\n{retrieval_evidence}")
    if graph_skill_context:
        prompt_parts.append(graph_skill_context)
    prompt_parts.append(f"Question: {question}")
    prompt = "\n\n".join(prompt_parts)

    mcp_tools: dict | None = None
    mcp_manager = None
    mcp_runtime_opt_in = os.environ.get("AG_ALLOW_MCP", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    if settings.MCP_ENABLED and mcp_runtime_opt_in:
        print("[…] Connecting to MCP servers...", file=sys.stderr)
        try:
            from antigravity_engine.mcp_client import MCPClientManager

            mcp_manager = MCPClientManager()
            await mcp_manager.initialize()
            mcp_tools = mcp_manager.get_all_tools_as_callables()
            if mcp_tools:
                logger.info("MCP tools loaded: %s", list(mcp_tools.keys()))
            else:
                logger.info("MCP enabled but no tools discovered")
        except Exception as exc:
            logger.warning("MCP initialization failed: %s", exc)
            print(f"  ⚠ MCP init failed: {exc}", file=sys.stderr)
            mcp_manager = None
    elif settings.MCP_ENABLED:
        logger.info(
            "MCP is enabled in settings but AG_ALLOW_MCP is not set; skipping MCP server autoconnection"
        )

    agent = build_reviewer_agent(model, workspace=workspace, mcp_tools=mcp_tools)
    try:
        from agents import Runner
    except ImportError:
        raise ImportError(
            "OpenAI Agent SDK not found. Install: pip install antigravity-engine"
        ) from None

    print("[2/3] Analyzing with multi-agent swarm...", file=sys.stderr)

    ask_timeout = float(os.environ.get("AG_ASK_TIMEOUT_SECONDS", "45"))
    try:
        try:
            if ask_timeout > 0:
                result = await asyncio.wait_for(
                    Runner.run(agent, prompt, max_turns=12),
                    timeout=ask_timeout,
                )
            else:
                result = await Runner.run(agent, prompt, max_turns=12)
        finally:
            if mcp_manager is not None:
                try:
                    await mcp_manager.shutdown()
                except Exception as exc:
                    logger.warning("MCP shutdown error: %s", exc)
    except TimeoutError:
        return _build_timeout_fallback_answer(workspace, question)

    print("[3/3] Synthesizing answer...", file=sys.stderr)

    return result.final_output


# ---------------------------------------------------------------------------
# Structured facts path
# ---------------------------------------------------------------------------

def _structured_artifacts_available(workspace: Path) -> bool:
    """Return whether structured refresh artifacts exist.

    Args:
        workspace: Project root directory.

    Returns:
        True when registry, status, and at least one facts artifact exist.
    """
    ag_dir = workspace / ".antigravity"
    modules_dir = ag_dir / "modules"
    return (
        (ag_dir / "module_registry.json").is_file()
        and (ag_dir / "status.json").is_file()
        and modules_dir.is_dir()
        and any(modules_dir.glob("*.facts.json"))
    )


async def _ask_with_structured_facts(workspace: Path, question: str) -> str | None:
    """Answer a question from structured module facts when possible.

    Args:
        workspace: Project root directory.
        question: Natural language question.

    Returns:
        Structured answer string, or ``None`` if the facts path cannot answer
        confidently enough and should fall back to the legacy swarm.
    """
    registry_entries = _load_registry_entries(workspace)
    refresh_status = _load_refresh_status(workspace)
    candidates = _select_candidate_modules(question, registry_entries)
    if not candidates:
        return None

    print(
        f"[2/4] Pre-routing to structured modules: {', '.join(entry.module for entry in candidates)}",
        file=sys.stderr,
    )

    documents: dict[str, ModuleFactsDocument] = {}
    worker_outputs: list[WorkerEvidence] = []
    verification_reports: list[VerificationResult] = []

    for entry in candidates:
        document = _load_module_facts(workspace, entry.module)
        if document is None:
            continue
        worker_output = _build_worker_evidence(question, entry, document, refresh_status)
        if not worker_output.claims_used:
            continue
        verification = _verify_worker_evidence(
            workspace=workspace,
            question=question,
            document=document,
            worker_output=worker_output,
        )
        documents[entry.module] = document
        worker_outputs.append(worker_output)
        verification_reports.append(verification)

    if not verification_reports:
        return None

    print("[3/4] Verifying structured claims...", file=sys.stderr)
    answer = _synthesize_structured_answer(
        question=question,
        entries=candidates,
        documents=documents,
        worker_outputs=worker_outputs,
        verification_reports=verification_reports,
    )
    if answer is None:
        return None

    print("[4/4] Returning evidence-backed structured answer.", file=sys.stderr)
    return answer


def _load_registry_entries(workspace: Path) -> list[ModuleRegistryEntry]:
    """Load machine-readable module registry entries.

    Args:
        workspace: Project root directory.

    Returns:
        Parsed registry entries.
    """
    registry_path = workspace / ".antigravity" / "module_registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    return [ModuleRegistryEntry.model_validate(item) for item in payload]


def _load_refresh_status(workspace: Path) -> RefreshStatus:
    """Load refresh health status from ``.antigravity/status.json``.

    Args:
        workspace: Project root directory.

    Returns:
        Parsed refresh status document.
    """
    status_path = workspace / ".antigravity" / "status.json"
    return RefreshStatus.model_validate_json(status_path.read_text(encoding="utf-8"))


def _load_module_facts(
    workspace: Path,
    module: str,
) -> ModuleFactsDocument | None:
    """Load facts for a single module.

    Args:
        workspace: Project root directory.
        module: Module identifier.

    Returns:
        Parsed facts document, or ``None`` when missing or invalid.
    """
    facts_path = workspace / ".antigravity" / "modules" / f"{module}.facts.json"
    if not facts_path.is_file():
        return None
    try:
        return ModuleFactsDocument.model_validate_json(
            facts_path.read_text(encoding="utf-8")
        )
    except Exception:
        return None


def _select_candidate_modules(
    question: str,
    registry_entries: list[ModuleRegistryEntry],
) -> list[ModuleRegistryEntry]:
    """Select the top candidate modules for a question.

    Args:
        question: Natural language question.
        registry_entries: Machine-readable module registry entries.

    Returns:
        Up to three candidate modules ordered by score.
    """
    question_tokens = _question_tokens(question)
    scored: list[tuple[int, ModuleRegistryEntry]] = []
    for entry in registry_entries:
        score = _score_registry_entry(question_tokens, question.lower(), entry)
        if score <= 0:
            continue
        scored.append((score, entry))

    scored.sort(
        key=lambda item: (
            -item[0],
            item[1].status != "success",
            item[1].module,
        )
    )
    return [entry for _, entry in scored[:3]]


def _question_tokens(question: str) -> list[str]:
    """Tokenize a user question for routing and claim matching.

    Args:
        question: Natural language question.

    Returns:
        Lowercase tokens with lightweight normalization.
    """
    tokens = re.findall(r"[a-zA-Z0-9_]{2,}", question.lower())
    return [token for token in tokens if token not in {"the", "and", "for", "how", "what"}]


def _score_registry_entry(
    question_tokens: list[str],
    question_lower: str,
    entry: ModuleRegistryEntry,
) -> int:
    """Score a registry entry against the current question.

    Args:
        question_tokens: Tokenized question terms.
        question_lower: Raw question lowercased.
        entry: Candidate module registry entry.

    Returns:
        Integer match score.
    """
    score = 0
    routing_tokens = set(entry.keywords)
    routing_tokens.update(_question_tokens(entry.summary))
    for path in entry.top_paths:
        routing_tokens.update(_question_tokens(path.replace("/", " ").replace(".", " ")))

    for token in question_tokens:
        if token in routing_tokens:
            score += 3
        if token in entry.module.lower():
            score += 5
        if any(token in path.lower() for path in entry.top_paths):
            score += 4

    if entry.module.lower() in question_lower:
        score += 8
    return score


def _build_worker_evidence(
    question: str,
    entry: ModuleRegistryEntry,
    document: ModuleFactsDocument,
    refresh_status: RefreshStatus,
) -> WorkerEvidence:
    """Select module claims to answer a question.

    Args:
        question: Natural language question.
        entry: Selected module registry entry.
        document: Module facts document.
        refresh_status: Global refresh status.

    Returns:
        Structured worker evidence payload.
    """
    selected_claims = _select_claims_for_question(question, document)
    claim_ids = [claim.claim_id for claim in selected_claims]
    draft_lines = [claim.statement for claim in selected_claims[:3]]
    module_state = refresh_status.modules.get(entry.module, entry.status)
    return WorkerEvidence(
        module=entry.module,
        draft_answer=" ".join(draft_lines),
        claims_used=claim_ids,
        verification_required=module_state != "success",
    )


def _select_claims_for_question(
    question: str,
    document: ModuleFactsDocument,
) -> list[ModuleClaim]:
    """Pick the most relevant claims for a question.

    Args:
        question: Natural language question.
        document: Module facts document.

    Returns:
        Ordered list of relevant claims.
    """
    question_tokens = set(_question_tokens(question))
    scored: list[tuple[int, ModuleClaim]] = []
    for claim in document.claims:
        score = _score_claim(question_tokens, claim)
        if score <= 0:
            continue
        scored.append((score, claim))

    if not scored:
        fallback = sorted(
            document.claims,
            key=lambda claim: (
                {"high": 0, "medium": 1, "low": 2}.get(claim.importance, 3),
                claim.claim_id,
            ),
        )
        return fallback[:3]

    scored.sort(key=lambda item: (-item[0], item[1].claim_id))
    return [claim for _, claim in scored[:5]]


def _score_claim(question_tokens: set[str], claim: ModuleClaim) -> int:
    """Score one claim for relevance to the question.

    Args:
        question_tokens: Tokenized question terms.
        claim: Candidate module claim.

    Returns:
        Integer relevance score.
    """
    claim_tokens = set(_question_tokens(claim.statement))
    claim_tokens.update(_question_tokens(claim.claim_type.replace("_", " ")))
    for rel_path in claim.source_files:
        claim_tokens.update(_question_tokens(rel_path.replace("/", " ").replace(".", " ")))
    overlap = len(question_tokens & claim_tokens)
    score = overlap * 4
    if claim.importance == "high":
        score += 3
    elif claim.importance == "medium":
        score += 2
    else:
        score += 1
    return score


def _verify_worker_evidence(
    workspace: Path,
    question: str,
    document: ModuleFactsDocument,
    worker_output: WorkerEvidence,
) -> VerificationResult:
    """Verify the worker's selected claims against source evidence.

    Args:
        workspace: Project root directory.
        question: Original user question.
        document: Module facts document.
        worker_output: Structured worker evidence payload.

    Returns:
        Verification report for the selected claims.
    """
    claim_lookup = {claim.claim_id: claim for claim in document.claims}
    verifications: list[ClaimVerification] = []

    for claim_id in worker_output.claims_used[:5]:
        claim = claim_lookup.get(claim_id)
        if claim is None:
            verifications.append(
                ClaimVerification(
                    claim_id=claim_id,
                    state="unverified",
                    notes="Claim was referenced by the worker but not found in module facts.",
                )
            )
            continue

        evidence_results: list[str] = []
        inspected_evidence: list = []
        for evidence in claim.evidence[:2]:
            inspected_evidence.append(evidence)
            file_path = workspace / evidence.file
            if not file_path.is_file():
                evidence_results.append("missing")
                continue
            try:
                lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                evidence_results.append("missing")
                continue

            snippet = "\n".join(
                lines[evidence.start_line - 1 : min(len(lines), evidence.end_line)]
            ).strip()
            if snippet and evidence.excerpt and snippet == evidence.excerpt.strip():
                evidence_results.append("verified")
            elif snippet:
                evidence_results.append("partial")
            else:
                evidence_results.append("missing")

        if "verified" in evidence_results:
            state = "verified"
            notes = "Evidence excerpt still matches the referenced source lines."
        elif "partial" in evidence_results:
            state = "partially_verified"
            notes = "Source lines were found, but the stored excerpt no longer matches exactly."
        else:
            state = "unverified"
            notes = "Referenced evidence could not be confirmed from current source files."

        verifications.append(
            ClaimVerification(
                claim_id=claim.claim_id,
                state=state,
                notes=notes,
                evidence=inspected_evidence,
            )
        )

    return VerificationResult(
        question=question,
        module=worker_output.module,
        claims=verifications,
        verification_required=worker_output.verification_required,
    )


def _synthesize_structured_answer(
    question: str,
    entries: list[ModuleRegistryEntry],
    documents: dict[str, ModuleFactsDocument],
    worker_outputs: list[WorkerEvidence],
    verification_reports: list[VerificationResult],
) -> str | None:
    """Compose a final answer from verified structured facts.

    Args:
        question: Original user question.
        entries: Routed registry entries.
        documents: Loaded module facts documents by module id.
        worker_outputs: Worker claim selections.
        verification_reports: Verification reports for the selections.

    Returns:
        Final answer string, or ``None`` if no supported claims remain.
    """
    entry_lookup = {entry.module: entry for entry in entries}
    doc_lookup = documents
    verification_lookup = {report.module: report for report in verification_reports}
    worker_lookup = {worker.module: worker for worker in worker_outputs}

    lines: list[str] = []
    verified_count = 0
    partial_count = 0

    for module, report in verification_lookup.items():
        document = doc_lookup.get(module)
        if document is None:
            continue
        claim_lookup = {claim.claim_id: claim for claim in document.claims}
        entry = entry_lookup[module]
        worker_output = worker_lookup[module]
        module_lines: list[str] = []

        if entry.status != "success":
            module_lines.append(f"`{module}` module knowledge is incomplete ({entry.status}).")

        for claim_verification in report.claims:
            claim = claim_lookup.get(claim_verification.claim_id)
            if claim is None:
                continue
            citation = _format_claim_citation(claim_verification)
            if claim_verification.state == "verified":
                verified_count += 1
                module_lines.append(f"- {claim.statement}{citation}")
            elif claim_verification.state == "partially_verified":
                partial_count += 1
                module_lines.append(f"- Possibly: {claim.statement}{citation}")

        if not module_lines and worker_output.draft_answer:
            module_lines.append(worker_output.draft_answer)

        if module_lines:
            lines.append(f"Module `{module}`:")
            lines.extend(module_lines)

    if verified_count == 0 and partial_count == 0:
        return None

    summary = [
        f"Question: {question}",
        "",
        *lines,
        "",
        f"Verification summary: {verified_count} verified, {partial_count} partially verified.",
    ]
    return "\n".join(summary).strip()


def _format_claim_citation(claim_verification: ClaimVerification) -> str:
    """Format the first evidence span for inline answer citations.

    Args:
        claim_verification: Verification result for one claim.

    Returns:
        Short citation string, or an empty string when no evidence exists.
    """
    if not claim_verification.evidence:
        return ""
    evidence = claim_verification.evidence[0]
    return f" ({evidence.file}:{evidence.start_line}-{evidence.end_line})"


# ---------------------------------------------------------------------------
# Context builders
# ---------------------------------------------------------------------------

def _read_context_file(path: Path, label: str) -> str | None:
    """Read a context file and wrap it with a label for prompt injection."""
    if not path.exists() or not path.is_file():
        return None

    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None

    if not content:
        return None

    return f"--- {label} ---\n{content}"


def _build_ask_context(workspace: Path, question: str = "") -> str:
    """Collect project context for Q&A with structure-first priority.

    The ordering has been adjusted so that the most universally useful
    sources (structure map, conventions, knowledge graph) come first,
    while niche indexes (media, data) are loaded only when budget
    remains.  When a *question* is provided, a lightweight keyword
    filter boosts sources whose labels overlap with the query.

    Args:
        workspace: Project root directory.
        question: Optional user question for relevance filtering.

    Returns:
        Concatenated context string.
    """
    context_parts: list[str] = []
    max_chars = int(os.environ.get("AG_ASK_CONTEXT_MAX_CHARS", "30000"))

    # Sources ordered by general usefulness (structure > conventions > graph > docs > data > media)
    prioritized_sources = [
        (
            workspace / ".antigravity" / "structure.md",
            ".antigravity/structure.md",
        ),
        (
            workspace / ".antigravity" / "conventions.md",
            ".antigravity/conventions.md",
        ),
        (
            workspace / ".antigravity" / "knowledge_graph.md",
            ".antigravity/knowledge_graph.md",
        ),
        (workspace / ".antigravity" / "rules.md", ".antigravity/rules.md"),
        (
            workspace / ".antigravity" / "decisions" / "log.md",
            ".antigravity/decisions/log.md",
        ),
        (workspace / "CONTEXT.md", "CONTEXT.md"),
        (workspace / "AGENTS.md", "AGENTS.md"),
        (
            workspace / ".antigravity" / "document_index.md",
            ".antigravity/document_index.md",
        ),
        (
            workspace / ".antigravity" / "data_overview.md",
            ".antigravity/data_overview.md",
        ),
        (
            workspace / ".antigravity" / "media_manifest.md",
            ".antigravity/media_manifest.md",
        ),
    ]

    # Lightweight keyword relevance: if the question mentions "media", "data",
    # "document", etc., boost matching sources to the front.
    if question:
        q_lower = question.lower()
        boost_keywords = {
            "media": "media_manifest",
            "image": "media_manifest",
            "video": "media_manifest",
            "data": "data_overview",
            "csv": "data_overview",
            "json": "data_overview",
            "document": "document_index",
            "doc": "document_index",
            "readme": "document_index",
        }
        boosted: set[str] = set()
        for kw, label_fragment in boost_keywords.items():
            if kw in q_lower:
                boosted.add(label_fragment)
        if boosted:
            top: list[tuple[Path, str]] = []
            rest: list[tuple[Path, str]] = []
            for entry in prioritized_sources:
                if any(b in entry[1] for b in boosted):
                    top.append(entry)
                else:
                    rest.append(entry)
            prioritized_sources = top + rest

    for path, label in prioritized_sources:
        rendered = _read_context_file(path, label)
        if rendered:
            if sum(len(p) for p in context_parts) + len(rendered) > max_chars:
                break
            context_parts.append(rendered)

    memory_dir = workspace / ".antigravity" / "memory"
    if memory_dir.exists():
        for memory_file in sorted(memory_dir.glob("*.md")):
            rendered = _read_context_file(
                memory_file,
                f".antigravity/memory/{memory_file.name}",
            )
            if rendered:
                if sum(len(p) for p in context_parts) + len(rendered) > max_chars:
                    break
                context_parts.append(rendered)

    return "\n\n".join(context_parts) if context_parts else "(no context available)"


def _is_structure_query(question: str) -> bool:
    """Heuristic for topology/structure/dependency style questions."""
    q = question.lower()
    keywords = {
        "依赖", "关系", "调用", "结构", "拓扑", "子图", "知识图谱", "谁调用", "路径",
        "dependency", "dependencies", "relation", "relations", "calls", "called by",
        "graph", "topology", "structure", "ownership", "impact",
    }
    return any(k in q for k in keywords)


def _build_graph_skill_context(workspace: Path, question: str) -> str | None:
    """Invoke Graph Skill and convert output to prompt-ready context block."""
    from antigravity_engine.skills.loader import load_skills

    tools: dict = {}
    load_skills(tools)
    query_graph = tools.get("query_graph")
    if not callable(query_graph):
        return None

    try:
        result = query_graph(question, max_hops=2, workspace=str(workspace))
    except Exception:  # noqa: BLE001
        return None

    max_chars = int(os.environ.get("AG_GRAPH_CONTEXT_MAX_CHARS", "8000"))
    max_chars = max(1000, max_chars)

    if isinstance(result, dict):
        payload = json.dumps(result, ensure_ascii=False, indent=2)
        if len(payload) > max_chars:
            payload = payload[:max_chars] + "\n... [truncated by AG_GRAPH_CONTEXT_MAX_CHARS]"
        return "--- graph_skill_context ---\n" + payload
    return f"--- graph_skill_context ---\n{result}"


# ---------------------------------------------------------------------------
# Retrieval / code-search helpers
# ---------------------------------------------------------------------------

def _iter_python_files(workspace: Path) -> list[Path]:
    """Collect python files under workspace with lightweight skip rules."""
    skip_dirs = SKIP_DIRS | {"data", "logs"}
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(workspace):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
        for fname in filenames:
            if fname.endswith(".py"):
                files.append(Path(dirpath) / fname)
    return files


def _iter_shell_files(workspace: Path) -> list[Path]:
    """Collect shell script files under workspace with lightweight skip rules."""
    skip_dirs = SKIP_DIRS | {"data", "logs"}
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(workspace):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and not d.startswith(".")]
        for fname in filenames:
            p = Path(dirpath) / fname
            if fname.endswith(".sh"):
                files.append(p)
                continue
            if fname in {"Dockerfile", "Makefile"}:
                continue
            try:
                if p.is_file() and p.read_text(encoding="utf-8", errors="ignore").startswith("#!/usr/bin/env bash"):
                    files.append(p)
            except Exception:
                continue
    return files


def _extract_identifiers(question: str) -> list[str]:
    """Extract candidate symbol identifiers from user question."""
    ids = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\b", question)
    seen: set[str] = set()
    out: list[str] = []
    for item in ids:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _find_function_defs(workspace: Path, identifiers: list[str]) -> list[dict[str, object]]:
    """Find function definitions matching identifiers.

    Results are prioritized: matches in files whose stem contains an
    identifier are ranked first (the actual module, not a wrapper).
    """
    targets = {x.lower() for x in identifiers}
    matches: list[dict[str, object]] = []
    for fpath in _iter_python_files(workspace):
        try:
            source = fpath.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
            lines = source.splitlines()
        except Exception:
            continue

        rel = str(fpath.relative_to(workspace))
        stem = fpath.stem.lower()
        # Boost: file stem contains one of the target identifiers
        file_match = any(t in stem for t in targets)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                if targets and name.lower() not in targets:
                    continue
                start = int(getattr(node, "lineno", 1))
                end = int(getattr(node, "end_lineno", start))
                snippet = "\n".join(lines[start - 1 : min(end, start + 20)])
                matches.append(
                    {
                        "name": name,
                        "file": rel,
                        "start": start,
                        "end": end,
                        "snippet": snippet,
                        "_file_match": file_match,
                    }
                )

    # Sort: file-name matches first, then by path length (shorter = less nested)
    matches.sort(key=lambda m: (not m.get("_file_match", False), len(str(m.get("file", "")))))
    # Clean internal key before returning
    for m in matches:
        m.pop("_file_match", None)
    return matches[:6]


def _find_call_sites(workspace: Path, func_name: str, limit: int = 12) -> list[str]:
    """Find call sites for a function name."""
    pattern = re.compile(rf"\b{re.escape(func_name)}\s*\(")
    calls: list[str] = []
    for fpath in _iter_python_files(workspace):
        try:
            rel = fpath.relative_to(workspace)
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            if pattern.search(line) and not line.lstrip().startswith("def "):
                calls.append(f"{rel}:{i}: {line.strip()}")
                if len(calls) >= limit:
                    return calls
    return calls


def _find_shell_function_defs(workspace: Path, identifiers: list[str]) -> list[dict[str, object]]:
    """Find shell function definitions matching identifiers."""
    targets = {x.lower() for x in identifiers}
    matches: list[dict[str, object]] = []
    def_pattern = re.compile(r"^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{")

    for fpath in _iter_shell_files(workspace):
        try:
            rel = fpath.relative_to(workspace)
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue

        i = 0
        while i < len(lines):
            line = lines[i]
            m = def_pattern.match(line)
            if not m:
                i += 1
                continue

            name = m.group(1)
            if targets and name.lower() not in targets:
                i += 1
                continue

            start = i + 1
            brace_balance = line.count("{") - line.count("}")
            j = i + 1
            while j < len(lines) and brace_balance > 0:
                brace_balance += lines[j].count("{") - lines[j].count("}")
                j += 1
            end = j if j > start else start
            snippet = "\n".join(lines[start - 1 : min(end, start + 25)])
            matches.append(
                {
                    "name": name,
                    "file": str(rel),
                    "start": start,
                    "end": end,
                    "snippet": snippet,
                }
            )
            i = j
            if len(matches) >= 6:
                return matches
    return matches


def _find_shell_call_sites(workspace: Path, func_name: str, limit: int = 12) -> list[str]:
    """Find shell call sites for a function name."""
    call_pattern = re.compile(rf"\b{re.escape(func_name)}\b")
    def_pattern = re.compile(r"^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{")
    calls: list[str] = []
    for fpath in _iter_shell_files(workspace):
        try:
            rel = fpath.relative_to(workspace)
            lines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            if not call_pattern.search(line):
                continue
            if def_pattern.match(line):
                continue
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            calls.append(f"{rel}:{i}: {stripped}")
            if len(calls) >= limit:
                return calls
    return calls


def _extract_blueprints_from_app(workspace: Path) -> list[str]:
    """Extract blueprint modules from backend app factory registration."""
    app_path = workspace / "backend" / "app.py"
    if not app_path.is_file():
        return []
    try:
        text = app_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    mods = re.findall(r'"backend\.blueprints\.([a-zA-Z0-9_]+)"', text)
    return mods


def _build_retrieval_semantic_answer(workspace: Path, question: str) -> str | None:
    """Build a semantic answer from retrieval artifacts and code evidence."""
    q = question.strip()
    if not q:
        return None

    lines: list[str] = []
    scan_report = workspace / ".antigravity" / "scan_report.json"
    if scan_report.is_file():
        try:
            payload = json.loads(scan_report.read_text(encoding="utf-8"))
            lines.append(
                "[retrieval] "
                f"files={payload.get('file_count', 0)}, "
                f"elapsed={payload.get('scan_elapsed_seconds', 0.0)}s"
            )
        except Exception:
            pass

    if ("blueprint" in q.lower()) or ("模块" in q and "注册" in q):
        bps = _extract_blueprints_from_app(workspace)
        if bps:
            lines.append("后端注册的 blueprint 模块:")
            lines.extend([f"- {m}" for m in bps])
            lines.append("证据: backend/app.py")
            return "\n".join(lines)

    identifiers = _extract_identifiers(q)
    if not identifiers and ("函数" not in q and "调用" not in q and "function" not in q.lower()):
        return None

    py_defs = _find_function_defs(workspace, identifiers)
    sh_defs = _find_shell_function_defs(workspace, identifiers)
    if not py_defs and not sh_defs:
        return None

    lines.append("基于检索到的函数实现与调用关系:")
    for item in py_defs[:3]:
        name = str(item["name"])
        file = str(item["file"])
        start = int(item["start"])
        lines.append(f"- 函数 {name} 定义于 {file}:{start}")
        snippet = str(item.get("snippet", "")).strip()
        if snippet:
            lines.append("```python")
            lines.append(snippet)
            lines.append("```")
        calls = _find_call_sites(workspace, name, limit=8)
        if calls:
            lines.append("  相关调用:")
            lines.extend([f"  - {c}" for c in calls])

    for item in sh_defs[:3]:
        name = str(item["name"])
        file = str(item["file"])
        start = int(item["start"])
        lines.append(f"- Shell 函数 {name} 定义于 {file}:{start}")
        snippet = str(item.get("snippet", "")).strip()
        if snippet:
            lines.append("```bash")
            lines.append(snippet)
            lines.append("```")
        calls = _find_shell_call_sites(workspace, name, limit=8)
        if calls:
            lines.append("  相关调用:")
            lines.extend([f"  - {c}" for c in calls])

    return "\n".join(lines)


def _build_timeout_fallback_answer(workspace: Path, question: str) -> str:
    """Return relevant knowledge snippets when ask agent times out."""
    ag_dir = workspace / ".antigravity"
    q_lower = question.lower()
    keywords = [w for w in re.split(r"\W+", q_lower) if len(w) > 2]

    lines: list[str] = [
        "LLM answering timed out. Here are the most relevant knowledge snippets:\n",
        f"**Question:** {question}\n",
    ]

    # -- Extract relevant sections from conventions.md --
    conventions = ag_dir / "conventions.md"
    if conventions.exists():
        try:
            text = conventions.read_text(encoding="utf-8")
            relevant = _extract_relevant_sections(text, keywords, max_chars=6000)
            if relevant:
                lines.append("## Project Conventions (relevant excerpts)\n")
                lines.append(relevant)
                lines.append("")
        except Exception:
            pass

    # -- Extract relevant sections from structure.md --
    structure = ag_dir / "structure.md"
    if structure.exists():
        try:
            text = structure.read_text(encoding="utf-8")
            relevant = _extract_relevant_sections(text, keywords, max_chars=8000)
            if relevant:
                lines.append("## Code Structure (relevant excerpts)\n")
                lines.append(relevant)
                lines.append("")
        except Exception:
            pass

    # -- Extract from knowledge_graph.md --
    kg = ag_dir / "knowledge_graph.md"
    if kg.exists():
        try:
            text = kg.read_text(encoding="utf-8")
            relevant = _extract_relevant_sections(text, keywords, max_chars=3000)
            if relevant:
                lines.append("## Knowledge Graph (relevant excerpts)\n")
                lines.append(relevant)
                lines.append("")
        except Exception:
            pass

    # -- Fallback: scan report summary --
    scan_report = ag_dir / "scan_report.json"
    if scan_report.exists() and len(lines) <= 4:
        try:
            payload = json.loads(scan_report.read_text(encoding="utf-8"))
            file_count = int(payload.get("file_count", 0)) if isinstance(payload, dict) else 0
            lines.append(f"*(Project has {file_count} files. Try rephrasing with a more specific question.)*")
        except Exception:
            pass

    if len(lines) <= 4:
        lines.append("No relevant knowledge found. Try running `ag refresh` to rebuild the knowledge base.")

    return "\n".join(lines)


def _extract_relevant_sections(text: str, keywords: list[str], max_chars: int = 6000) -> str:
    """Extract sections from markdown text that match keywords."""
    if not keywords:
        return text[:max_chars]

    sections = re.split(r"(?=^#{1,3}\s)", text, flags=re.MULTILINE)
    scored: list[tuple[int, str]] = []
    for section in sections:
        section_lower = section.lower()
        score = sum(1 for kw in keywords if kw in section_lower)
        if score > 0:
            scored.append((score, section.strip()))

    scored.sort(key=lambda x: x[0], reverse=True)

    result: list[str] = []
    total = 0
    for _score, section in scored:
        if total + len(section) > max_chars:
            remaining = max_chars - total
            if remaining > 200:
                result.append(section[:remaining] + "\n...")
            break
        result.append(section)
        total += len(section)

    return "\n\n".join(result)
