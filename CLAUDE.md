# CLAUDE.md

Persistent context for Claude Code when working in this repository.

## What this repo is

**Consilium** — a multi-agent deliberation pattern, packaged as a Claude Code skill (identifier: `consilium`). Three voices (Generator / Control / Conservator) evaluate code changes sequentially (Sequential — Blind, default) or via opt-in modes (Dialectic, Trias), with explicit voting and veto. This repo is the public showcase / demo. The live skill source is in a private repository.

## The four Constitution principles

These govern every deliberation. They have priority over a voice's recommendation if the two conflict. Apply them to any change you make in this repo.

1. **Think before coding.** Expose trade-offs explicitly. If the request has 2 plausible interpretations, list them as separate candidates — don't pick silently.
2. **Simplicity first.** Minimum code. Refuse speculative abstractions and unrequested features. `do_nothing` is always on the table as a candidate.
3. **Surgical changes.** Touch only what the goal asks for. The Conservator voice measures deviation via `scope_drift` — respect a high score (don't bundle a refactor into a bugfix).
4. **Goal-driven execution.** Restate the goal as a testable **success criterion** before generating candidates. The final output must include a **verification** step (a concrete command or check, not "looks good").

These are operationalised by the Consilium skill itself — see `SKILL.md` in the live (private) skill repo for the full enforcement workflow (clarity gate, scope gate, validate_report.py, FEEDBACK.html calibration loop).

## Code & content conventions

- **English only.** All comments, identifiers, README copy, and JSON labels are in English. No mixed-language strings.
- **Voice names are proper nouns.** Generator / Control / Conservator (capitalised). Don't pluralise into "voices" mid-sentence inconsistently — they are *the three voices*.
- **Single-file HTML for demos.** `architecture.html` is intentionally self-contained — no external CSS/JS files beyond Google Fonts. Don't introduce build tooling.
- **Dark theme palette.** Use the CSS variables defined at the top of `architecture.html` (`--bg`, `--gold`, `--ctl`, `--gen`, `--con`, `--accent`, `--trias`). Don't introduce ad-hoc hex codes.
- **No copyrighted assets.** No fonts beyond Google Fonts, no audio, no third-party imagery. This is a public portfolio.

## Working in this repo

- The repo is meant to be readable end-to-end in one sitting. Keep additions focused; don't bloat the architecture poster with content that belongs in the live skill repo.
- The `architecture.html` file has an **Interactive Demo** tab (formerly Patterns) with an interactive flow diagram and a Play tour. Treat it as the centrepiece — if you touch flow definitions, the SVG line routing, or the Trias / Calibration sub-diagrams, make sure the Play tour still renders cleanly end-to-end.
- `example_output.json` is the canonical schema example. Its shape is what `scripts/build_report.py` produces. Don't drift from it without updating the skill's `validate_report.py` schema check upstream first.
- `README.md` describes the live skill at a high level — keep it in sync with the private skill repo's README if the install procedure or layout changes.

## What not to do

- Don't translate, rename, or "humanise" the voice prompt files (`generator.md`, `control.md`, `conservator.md`) without coordination — they are the public contract of the skill.
- Don't add a build step, package manager, or bundler. This repo stays vanilla.
- Don't introduce client-side analytics, trackers, or telemetry pixels in the demo HTML.
- Don't commit `runs/` JSON artefacts (gitignored) — they contain real deliberation outputs and may include sensitive context.

## Verification before claiming done

Match the Constitution's fourth principle. After any change to `architecture.html`:

1. Open the file in a modern browser (Chrome / Firefox / Safari).
2. Click through all five tabs — **Architecture / Flow / Modes / Interactive Demo / Benchmark**.
3. On Interactive Demo, click each flow in the sidebar — verify highlighted path + arrows render correctly, and the gate node flips PASS / FAIL for Veto trigger.
4. Click **Play tour** — confirm the auto-tour completes the full ~28s cycle without errors and stops at the bottom.
5. Resize the window to verify the diagram reflows responsively (≥1100px, 820px, 600px breakpoints).
