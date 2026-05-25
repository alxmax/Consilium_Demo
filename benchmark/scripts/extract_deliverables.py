r"""Extract declared deliverable files from a task prompt + write them from claude_raw.json.

Used by benchmark harness after `claude -p` returns when the spawned Claude
session declared deliverable files but did not actually call the Write tool.
Reads the prompt to find which files are declared (e.g. `Required output
files: \`solution.py\``), then scans the model's chat response in
claude_raw.json for fenced code blocks matching those filenames, and writes
each to the workspace.

Designed per Consilium senate audit 2026-05-18_203925: text-only SKILL.md
rules empirically insufficient to force Write tool calls in Sonnet 4.6
headless. Authority for deliverable file presence moves to the harness layer.

Contract (per senate conditions):
- Deterministic: same prompt + same response → same files written, every run.
- Strict matching: prefer fence-info-string label match (` ```python solution.py `).
  Fall back to language-extension match ONLY when there is exactly one declared
  file and exactly one fenced block of the matching language.
- Idempotent: skip writing if file already exists on disk (model may have
  called Write itself; do not overwrite).
- Verifiability: post-write, confirm `os.path.getsize() > 0`; report status
  per file.
- Hard error (not silent skip) on no-match / ambiguous-match — see Dimon's
  silent failure scenarios.

CLI:
    python scripts/extract_deliverables.py \\
        --prompt-file prompts/code/01_circuit_breaker.md \\
        --raw-json workspace/<mode>/<task>/claude_raw.json \\
        --workspace workspace/<mode>/<task>/

Exit codes:
    0 — all declared files exist on disk (written by extractor, or already
        present by model's own Write call).
    1 — at least one declared file is missing or unwritable after extraction
        (status `no_block_matched`, `ambiguous`, or `empty_block`).
    2 — input error (prompt/raw-json missing, malformed JSON).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ── Pattern definitions (deterministic, single source of truth) ────────────

# Bullets under a `**Required output file(s)?**` / `**Deliverables**` section.
# Bullet shape: `- \`name.ext\` <anything>` or `* \`name.ext\` <anything>`.
_HEADER_RE = re.compile(
    r"\*\*\s*(?:Required\s+output\s+files?|Deliverables?)\s*\*\*\s*:?",
    re.IGNORECASE,
)
# Bullet line within a section: starts with `-` or `*`, then backticked filename.
_BULLET_RE = re.compile(r"^\s*[-*]\s+`([^`]+)`")

# Inline fallback: "save your response to a file `<name>`", "deliver `<name>`",
# "write to `<name>`", "save your full reasoning to `<name>`".
_INLINE_RE = re.compile(
    r"\b(?:save|deliver|write|create|produce|output|generate)\b"
    r"[^.\n]{0,80}?"
    r"`([^`]+\.[A-Za-z0-9]{1,8})`",
    re.IGNORECASE,
)

# Fence: ```<info>\n<content>\n``` (multiline, non-greedy).
_FENCE_RE = re.compile(
    r"```([^\n]*)\n(.*?)\n```",
    re.DOTALL,
)

# Mapping from file extension to plausible fence language tags.
_EXT_TO_LANGS = {
    ".py": {"python", "py"},
    ".cpp": {"cpp", "c++", "cxx"},
    ".hpp": {"cpp", "c++", "hpp", "h"},
    ".h": {"c", "cpp", "c++", "h"},
    ".c": {"c"},
    ".js": {"javascript", "js"},
    ".ts": {"typescript", "ts"},
    ".md": {"markdown", "md", ""},   # plain text often unfenced or untagged
    ".json": {"json"},
    ".sh": {"bash", "sh", "shell"},
    ".rs": {"rust"},
    ".go": {"go"},
}

# A "filename-looking" token: has at least one dot + 1-8 char extension; no
# spaces, no slashes-leading. Used to filter `_INLINE_RE` matches.
_FILENAME_TOKEN_RE = re.compile(r"^[\w./\-]+\.[A-Za-z0-9]{1,8}$")

# Reasoning-task answer line: `ANSWER: A` (or B/C/D) at the start of a line.
# Used to recover the deliverable when the model emits a consilium-style log
# above the answer — we slice the response from this line forward so the
# verifier finds it as the first non-empty line of answer.md.
_ANSWER_LINE_RE = re.compile(r"^\s*ANSWER:\s*[ABCD]\b", re.MULTILINE)


# ── Step 1: extract declared files from the prompt ─────────────────────────

def extract_declared_files(prompt: str) -> list[str]:
    """Return ordered list of filenames declared in the prompt.

    Strategy:
      1. Find a `**Required output files**` (or `**Deliverables**`) header. If
         present, collect every bullet's first-backticked filename until the
         section ends (next `---` separator, next `**Bold:**` header, or EOF).
      2. If header strategy yields nothing, fall back to inline-phrase scan
         (verb + backticked filename within ~80 chars).
      3. Deduplicate preserving first-seen order. Filter out non-filename tokens.
    """
    files: list[str] = []
    seen: set[str] = set()

    # --- Strategy 1: dedicated header section ---
    for m in _HEADER_RE.finditer(prompt):
        start = m.end()
        # Section ends at next `---`, next `**...**:` bold-header line, or EOF.
        rest = prompt[start:]
        end_markers = [
            rest.find("\n---"),
            rest.find("\n**Constraints"),
            rest.find("\n**Workspace"),
            rest.find("\n**At the end"),
            rest.find("\n**Toolchain"),
        ]
        end_offsets = [e for e in end_markers if e >= 0]
        section_end = min(end_offsets) if end_offsets else len(rest)
        section = rest[:section_end]
        for line in section.splitlines():
            bm = _BULLET_RE.match(line)
            if bm:
                name = bm.group(1).strip()
                if _FILENAME_TOKEN_RE.match(name) and name not in seen:
                    files.append(name)
                    seen.add(name)

    if files:
        return files

    # --- Strategy 2: inline phrasing fallback (for outlier prompts) ---
    for m in _INLINE_RE.finditer(prompt):
        name = m.group(1).strip()
        if _FILENAME_TOKEN_RE.match(name) and name not in seen:
            files.append(name)
            seen.add(name)

    return files


# ── Step 2: extract fenced blocks from the model's chat response ───────────

def extract_fenced_blocks(response: str) -> list[tuple[str, str]]:
    """Return list of (info_string, content) for every fenced block in response.

    `info_string` is the raw text after the opening triple-backtick (e.g.
    "python solution.py" or "json" or ""). Content excludes the trailing
    closing fence.
    """
    return [(m.group(1).strip(), m.group(2)) for m in _FENCE_RE.finditer(response)]


# ── Step 3: match each declared file to a fenced block ─────────────────────

def match_blocks_to_files(
    declared: list[str],
    blocks: list[tuple[str, str]],
) -> dict[str, dict]:
    """For each declared filename, find the best matching fenced block.

    Returns {filename: {"status": "...", "content": str | None, "info": str | None}}.
    Status values:
      - "strict":     fence info-string contains the exact filename.
      - "loose":      fence language tag matches the file extension and the
                      pairing is unambiguous (1-to-1 within the language bucket).
      - "ambiguous":  multiple plausible blocks for one file (or vice versa);
                      caller must decide.
      - "no_match":   no fenced block matches by either rule.
    """
    result: dict[str, dict] = {}

    # --- Pass A: strict label match (filename appears in fence info string) ---
    consumed: set[int] = set()
    for fname in declared:
        for i, (info, content) in enumerate(blocks):
            if i in consumed:
                continue
            if fname in info:
                result[fname] = {"status": "strict", "content": content, "info": info}
                consumed.add(i)
                break

    # --- Pass B: loose match by language tag, paired in declaration order ---
    # Strategy: bucket files and blocks by extension. Within each bucket,
    # pair 1:1 in declaration order. If M blocks < N files, remaining files
    # are no_match (model under-delivery). If M > N, surplus blocks are
    # ambiguous (which file gets which?) — we still pair the first N, then
    # flag remaining files we'd have to pick from.
    remaining_files = [f for f in declared if f not in result]

    # Group remaining files by extension, preserving declaration order.
    files_by_ext: dict[str, list[str]] = {}
    for f in remaining_files:
        files_by_ext.setdefault(Path(f).suffix.lower(), []).append(f)

    # Group remaining blocks by matching language, preserving response order.
    for ext, fnames in files_by_ext.items():
        langs = _EXT_TO_LANGS.get(ext, set())
        candidates = []
        for i, (info, c) in enumerate(blocks):
            if i in consumed:
                continue
            first = info.split()[0].lower() if info.split() else ""
            if first in langs:
                candidates.append((i, info, c))

        if len(candidates) > len(fnames):
            # Surplus blocks — ambiguous, since we don't know which to pick.
            for fname in fnames:
                result[fname] = {
                    "status": "ambiguous",
                    "content": None,
                    "info": None,
                    "detail": f"{len(candidates)} candidate block(s) for ext {ext}, only {len(fnames)} declared file(s) of same ext — cannot decide which block(s) to drop",
                }
            continue

        # candidates <= fnames: pair 1:1 in declaration order.
        for fname, (i, info, c) in zip(fnames, candidates):
            result[fname] = {"status": "loose", "content": c, "info": info}
            consumed.add(i)
        for fname in fnames[len(candidates):]:
            result[fname] = {"status": "no_match", "content": None, "info": None}

    # Catch any file not handled (shouldn't happen, but defensive):
    for fname in declared:
        if fname not in result:
            result[fname] = {"status": "no_match", "content": None, "info": None}

    return result


# ── Step 4: write deliverables (idempotent + verifiable) ───────────────────

def write_deliverables(
    workspace: Path,
    matches: dict[str, dict],
) -> dict[str, str]:
    """Write each matched file to workspace; return per-file status string.

    Status values:
      - "already_exists":  file is on disk (model called Write itself); no overwrite.
      - "written":         file written by extractor; verified non-empty.
      - "empty_block":     matched block was empty; nothing written.
      - "ambiguous":       extraction punted; nothing written.
      - "no_block_matched": no fenced block matched declared filename.
      - "write_error":     IO error during write.
    """
    statuses: dict[str, str] = {}
    for fname, match in matches.items():
        target = workspace / fname

        # Idempotency check: respect anything the model already wrote.
        if target.exists():
            statuses[fname] = "already_exists"
            continue

        status = match["status"]
        if status == "ambiguous":
            statuses[fname] = "ambiguous"
            continue
        if status == "no_match":
            statuses[fname] = "no_block_matched"
            continue

        content = match["content"]
        if not content or not content.strip():
            statuses[fname] = "empty_block"
            continue

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        except OSError as exc:
            statuses[fname] = f"write_error: {exc}"
            continue

        # Verifiability gate (Dimon): exists + non-empty.
        if not target.exists() or target.stat().st_size == 0:
            statuses[fname] = "write_error: post-write check failed"
        else:
            statuses[fname] = "written"

    return statuses


# ── Orchestrator ───────────────────────────────────────────────────────────

def extract_and_write_from_response(
    prompt: str,
    response: str,
    workspace: Path,
) -> dict[str, str]:
    """Variant taking the model's chat response directly (in-memory path).

    Used by run_task.py immediately after `claude -p` returns, before
    claude_raw.json is persisted to disk. Same return contract as
    `extract_and_write`.

    Special case: for declared `.md` files that find no fenced block,
    fall back to writing the entire response as the file content. This
    matches the reasoning-task convention where the user's prompt says
    "save your full response to `answer.md`" — the response IS the file.
    """
    declared = extract_declared_files(prompt)
    if not declared:
        return {}
    blocks = extract_fenced_blocks(response)
    matches = match_blocks_to_files(declared, blocks)

    # Markdown fallback: response-as-file for unmatched .md deliverables,
    # ONLY when the .md is the sole declared file (reasoning-task convention:
    # "save your full response to `answer.md`"). For multi-file prompts (e.g.
    # circuit_breaker declares solution.hpp + tests_self.cpp + BUILD.md), the
    # .md is typically optional/auxiliary and must NOT get the full response.
    if len(declared) == 1 and Path(declared[0]).suffix.lower() == ".md":
        fname = declared[0]
        if matches[fname]["status"] in ("no_match", "ambiguous"):
            # Reasoning-task recovery: if the response contains an `ANSWER: X`
            # line, slice from there so the verifier sees it as the first
            # non-empty line. Otherwise keep the full response as-is.
            answer_match = _ANSWER_LINE_RE.search(response)
            if answer_match:
                content = response[answer_match.start():]
                info = "(sliced from ANSWER: line)"
            else:
                content = response
                info = "(full response as markdown body)"
            matches[fname] = {
                "status": "loose",
                "content": content,
                "info": info,
            }

    return write_deliverables(workspace, matches)


def extract_and_write(
    prompt: str,
    raw_json_path: Path,
    workspace: Path,
) -> dict[str, str]:
    """End-to-end: parse prompt, parse claude_raw.json, write missing files.

    Returns {filename: status}. Empty dict if prompt declares no deliverables.
    Raises FileNotFoundError if raw_json_path is missing.
    """
    raw = json.loads(raw_json_path.read_text(encoding="utf-8"))
    response = raw.get("result", "") or ""
    return extract_and_write_from_response(prompt, response, workspace)


# ── CLI ────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--prompt-file", required=True, help="Path to task prompt .md")
    ap.add_argument("--raw-json", required=True, help="Path to claude_raw.json")
    ap.add_argument("--workspace", required=True, help="Target workspace directory")
    args = ap.parse_args()

    prompt_path = Path(args.prompt_file)
    raw_path = Path(args.raw_json)
    workspace = Path(args.workspace)

    if not prompt_path.exists():
        print(f"ERROR: prompt file not found: {prompt_path}", file=sys.stderr)
        return 2
    if not raw_path.exists():
        print(f"ERROR: raw json not found: {raw_path}", file=sys.stderr)
        return 2

    prompt = prompt_path.read_text(encoding="utf-8")
    try:
        statuses = extract_and_write(prompt, raw_path, workspace)
    except json.JSONDecodeError as exc:
        print(f"ERROR: malformed claude_raw.json: {exc}", file=sys.stderr)
        return 2

    # Print one line per file: status: filename
    if not statuses:
        print("(no deliverable contract detected in prompt — nothing to extract)")
        return 0

    print(json.dumps(statuses, indent=2, ensure_ascii=False))

    # Exit 0 only if every file is now on disk.
    bad = {f for f, s in statuses.items() if s not in ("written", "already_exists")}
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
