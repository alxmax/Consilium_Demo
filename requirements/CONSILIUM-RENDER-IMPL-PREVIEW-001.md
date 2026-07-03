---
milestone: v1.2
id: CONSILIUM-RENDER-IMPL-PREVIEW-001
status: confirmed
layer: bus
owner: auto
depends_on: [CONSILIUM-UTILS-001]
risk: 1
---

# render_impl_preview

> Opt-in Step 7 companion: deliberation report (+ optional unified diff) -> one self-contained static HTML review page for pre-commit handoff.

## Input
- CLI flag `--input` (required): path to a `runs/<file>.json` deliberation report; read with `utf-8-sig` so BOM-stamped files parse
- CLI flag `--diff-file` (optional): unified diff text to render (`-` reads stdin, e.g. piped from `git diff`); omitted -> spec-only preview
- CLI flag `--output` (optional): output HTML path; default `.consilium/preview/<input-stem>.html`
- CLI flag `--title` (optional): page title override
- Programmatic surface: `render_preview_html(report, diff_text, title)` and `split_diff_sections(diff_text)` (pure functions, no I/O)

## Description
Renders a completed deliberation report — success criterion, chosen approach with voice scores, alternatives with why_not, verification command, confidence and mode — together with an optional multi-file unified diff into a single self-contained HTML page. Exists for handoff review outside the live CLI session: unlike session-bound Artifact URLs or ephemeral Plan Mode, the page is a plain file on disk that survives the session and can be attached to the run report it renders. It is never part of the Step 7 dispatch control flow — invocation is always explicit (decided by deliberation `runs/2026-07-03_1443_html-preview-impl-step.json`, which rejected a prose-enforced pipeline checkpoint as the self-enforced-guard anti-pattern). Diff text is split into per-file sections on `diff --git` headers, with headerless input falling back to a single `(diff)` section, and every line of report and diff content passes through `html.escape` before it reaches the page.

## Output
- One self-contained HTML file (inline CSS, no external assets) written atomically via `utils.atomic_write_text` to `--output` or the default preview path
- stdout: `preview: <path>` on success
- exit 0 on success; exit 1 on unreadable input or a missing required report field (`success_criterion`, `chosen_approach`, `verification`); exit 2 on malformed JSON

## WHAT — Contract
- Shall render `success_criterion`, `chosen_approach`, `verification`, `alternatives` (id, summary, why_not) and `confidence` from the input report into the page.
- Shall render each `diff --git` section of the supplied diff as its own titled block; with no diff supplied, shall render a spec-only placeholder instead and still exit 0.
- Shall pass all report and diff content through `html.escape` — hostile input (`</script>`, inline event handlers) shall never appear unescaped in the output.
- Shall emit a self-contained page: no `<link>`, `<script src>`, or `<img src>` references to external URLs.
- Shall follow the viewer's light/dark preference (`prefers-color-scheme`) and include an inline theme-toggle button (`id="theme-toggle"`) that overrides it, persisting the choice in `localStorage`.
- Shall never dispatch, block, or gate any Step 7 stage — the script only reads its inputs and writes one HTML file.

## WHAT — Verify intent
- None - the default output directory `.consilium/preview/` inherits the gitignore on `.consilium/`, so preview pages cannot enter the tree; no separate ignore rule is asserted by tests.
- None - `--diff-file -` consumes stdin exactly once; combining it with a stdin-based report is unsupported by construction (the report always comes from `--input`).

## Acceptance (= tests)
- Round-trip: a report plus a two-file unified diff renders a page containing the success criterion, the chosen id, and one section per `diff --git` header (`scripts/test_render_impl_preview.py`).
- Escaping: a diff containing `</script><script>alert(1)</script>` and `<img onerror=...>` yields a page where the raw sequences are absent and the escaped forms present.
- Spec-only: with no `--diff-file`, the page contains the placeholder and no diff blocks; the CLI exits 0.
- Failure modes: a report missing `chosen_approach` exits 1 naming the field on stderr; malformed JSON exits 2; an absent report path exits 1.
- Theme toggle: the rendered page contains the `theme-toggle` button element.

<!-- verified-by: scripts/test_render_impl_preview.py -->
