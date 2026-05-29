# Architecture sync — Modes & Flow tabs vs SKILL.md (post P3-corrigendum PRs)

**Status:** spec
**Created:** 2026-05-16
**Origin:** sync gap discovered after PR #50 / #51 / #52 (P3 corrigendum follow-up).

## Goal

Sync `docs/architecture.html` tabs **Modes** and **Flow** with the current state of `SKILL.md` after three merged PRs:

- **PR #50** — `fix(skill): add benchmarking discipline for fab-rate claims` — added a new "Benchmarking discipline" paragraph under SKILL.md "Skill maintenance"; created `experiments/README.md` checklist.
- **PR #51** — `feat(skill): document skeptic_on_chosen as conceptual cross-cutting flag` — added a new SKILL.md section `## Skeptic-on-chosen mode (skeptic_on_chosen)` after `trias_split`.
- **PR #52** — `fix(docs): revise Haiku verifiers claim from anti-fabrication to conditional` — already touched `docs/architecture.html` Trias split-model "When" cell. No further work needed for #52 in this spec.

## Success criterion

After this work, an outside reader who reads only `docs/architecture.html` Modes + Flow tabs sees:

1. All conceptual modes documented in SKILL.md represented (10 active + 1 SPEC, including `skeptic_on_chosen`).
2. The cross-cutting flag nature of `skeptic_on_chosen` is visible — it composes onto any base mode, unlike `parallel_skeptic` / `dialectic_skeptic` which are fixed compositions.
3. The Benchmarking discipline gate (oracle independent / critique adverbial / verdict fabrication blocked) is referenced somewhere in the Flow tab.
4. The relationship between Step 5d retry and `skeptic_on_chosen` auto-trigger is documented (decided semantics: α — skeptic replaces retry in band [0.5, 0.7], retry remains conditional fallback only if skeptic verdict is `requires_redesign`).

## Verification

- `grep -n "skeptic_on_chosen\|Skeptic-on-chosen" docs/architecture.html` returns ≥ 3 matches (card heading + flowmap note + Step 5d body).
- `grep -n "Benchmarking discipline" docs/architecture.html` returns ≥ 1 match (Flow tab callout).
- Header in Modes tab section reads `Flow models — 10 moduri (9 active + 1 SPEC)`.
- All existing mode cards remain present and structurally unchanged; only addition + minor text adjustments.
- File still validates as HTML (no malformed tags, all sections closed correctly).

## Architecture

The change is a pure HTML edit on `docs/architecture.html`. Two tab sections are touched:

- `<section class="tab" id="modes">` — start at L1780 in current file
- `<section class="tab" id="flow">` — start at L1333 in current file

(Line numbers are reference points; expect drift after edits — verify by grep, not by line number.)

No CSS or JS changes. No new files. No other tabs touched.

## Edits per section

### Modes tab — additions

**A1. New mode card `skeptic_on_chosen`** — inserted after the `Trias split-model` card (`<div class="mode trias" style="grid-column: 1 / -1; ...">`), **before** the `Sequential — naive` legacy card.

Structure (matches existing `.mode parallel` cards):

```html
<div class="mode parallel">
  <h3>Skeptic-on-chosen — flag cross-cutting <span class="mode-badge opt">OPT-IN</span></h3>
  <div class="subtitle">Flag care compune o voce Skeptic focală peste <b>orice</b> mod de bază (Sequential / Parallel / Dialectic / Trias). Spre deosebire de <code>parallel_skeptic</code> și <code>dialectic_skeptic</code> care sunt moduri fixe, acesta e flag-ul generalizat.</div>

  <div class="stage">
    <div class="label">cum — flag care extinde orice mod cu o voce focală</div>
    <div class="actor main">Claude main</div>
    <div class="arrow-down">↓ rulează modul de bază normal (Sequential / Parallel / Dialectic / Trias)</div>
    <span class="actor gen">Generator</span>
    <span class="actor ctl">Control</span>
    <span class="actor con">Conservator</span>
    <div class="arrow-down">↓ aggregator → chosen + confidence</div>
    <div class="label">condiție: confidence ∈ [0.5, 0.7] AND (--skeptic-on-chosen activ OR auto-trigger)</div>
    <span class="actor" style="background:var(--accent-soft); border-color:var(--accent-border); color:var(--accent-text);">Skeptic (sub-agent focal · prompts/skeptic.md)</span>
    <div class="ok">
      ✓ Înlocuiește Step 5d retry în această bandă. Retry rămâne fallback condițional doar dacă Skeptic verdict e <code>requires_redesign</code>.
    </div>
    <div class="ok">
      ✓ Advisory by default — verdict-ul Skeptic apare ca <code>deliberation_log</code> entry + flag <code>skeptic_caught_constraint</code>, dar nu suprascrie <code>chosen</code>. Override-ul cere opt-in suplimentar via <code>--skeptic-can-override</code>.
    </div>
  </div>

  <dl class="mode-meta">
    <div class="cell"><dt>Sub-agenți</dt><dd><b>+1</b> <span style="color:var(--muted); font-size:11px;">peste modul de bază</span></dd></div>
    <div class="cell"><dt>Cost vs Parallel</dt><dd><span class="cost">+0.33×</span> <span style="color:var(--muted); font-size:11px;">peste base</span></dd></div>
    <div class="cell"><dt>Voci</dt><dd><div class="voices-tags"><span class="vt s">Skeptic</span></div><span style="color:var(--muted); font-size:11px;">focal pe chosen</span></dd></div>
    <div class="cell"><dt>When</dt><dd>conf ∈ [0.5, 0.7] cu flag activ sau auto-trigger; oricare mod de bază</dd></div>
  </dl>

  <div class="use-when">
    <b>Use when:</b> vrei o voce focală post-deliberare disponibilă pe <i>orice</i> mod de bază, fără a comuta la modurile fixe <code>parallel_skeptic</code> / <code>dialectic_skeptic</code>. Compune onest cu Sequential și Trias unde altfel n-ai avea acces la Skeptic.
    <br><b>Override:</b> advisory by default; <code>--skeptic-can-override</code> permite Skeptic verdict să suprascrie <code>chosen</code> dacă <code>addressable: requires_redesign</code>.
    <br><b>Cost:</b> +1 sub-agent peste modul de bază.
    <br><b>Origin empiric:</b> <code>chosen_confirmation_pass</code> a obținut 100% catch-rate în sim și 4/7 în reruns reale P3 (vezi <code>experiments/oracle-discipline.md</code>).
  </div>
</div>
```

**A2. Header count update.** In `<section class="tab" id="modes">` change:

```html
<h2>Flow models — 9 moduri (8 active + 1 SPEC)</h2>
```

to:

```html
<h2>Flow models — 10 moduri (9 active + 1 SPEC)</h2>
```

**A3. Flowmap note update.** In the bottom note of `.flowmap` (currently L2417-2420), append one sentence:

> În plus, `skeptic_on_chosen` e un **flag cross-cutting** (nu mod fix) — compune Skeptic focal peste *orice* mod de bază; auto-trigger pe conf ∈ [0.5, 0.7] sau manual via `--skeptic-on-chosen`.

### Flow tab — additions

**B1. Benchmarking discipline callout block.** Inserted as a new `<div class="decision">` block immediately **after** the existing `feedback-diagram` `<div>` (before the closing `</section>` of the flow tab).

Content draft:

```html
<div class="decision">
  <h3>Benchmarking discipline — process gate pre-claim</h3>
  <div class="lede">
    Înainte de a publica orice claim cantitativ pe comportamentul vocilor (<code>fab-rate</code>, <code>accuracy</code>, <code>catch-rate</code>) — 3 verificări obligatorii. Origin: corigendum-ul P3 (vezi <code>experiments/oracle-discipline.md</code>) — oracle-ul greșit a inversat semantic concluzia "fabrication" → "real constraint catch".
  </div>
  <ul style="margin: 12px 0; padding-left: 20px; color: var(--ink); font-size: 13px; line-height: 1.6;">
    <li><b>Oracle independent.</b> Răspunsul corect e fixat de (a) al doilea expert care nu a văzut quick-take-ul evaluatorului, SAU (b) citation explicită din enunț/specs care reduce ambiguitatea. Quick-take-ul evaluatorului ≠ oracle.</li>
    <li><b>Critique adverbial per opțiune.</b> Pentru fiecare răspuns plauzibil (A/B/C/D...), documentează explicit: "există citire alternativă în care răspunsul X devine corect?". Răspunsul "nu" trebuie justificat.</li>
    <li><b>Verdict "fabricație" blocat.</b> Eticheta <code>fabrication</code> pe un raționament cere justificarea oracle-ului independent de intuiția evaluatorului.</li>
  </ul>
  <div class="caption">
    Checklist operațional: <code>experiments/README.md</code>. Doctrinar: SKILL.md "Skill maintenance → Benchmarking discipline". Aplicată retroactiv pe orice fab-rate / accuracy / catch-rate publicat anterior.
  </div>
</div>
```

**B3. Step 5d card update.** Currently:

```html
<div>Dacă <code>confidence &lt; 0.7</code>: rulează <code>scripts/retry_context.py</code> → top-2 candidați cu fișiere/simboluri de citit/grepat. Gather context (Read + Grep) → re-rulează G/C/Cons <b>o singură dată</b> cu input îmbogățit. Dacă confidence încă <code>&lt; 0.7</code>, abia atunci întrebi utilizatorul.</div>
```

Append paragraph (inside the same `<div class="step aux">` cell):

```html
<div style="font-size:12px; color:var(--accent); margin-top:6px;">
  <b>Interacțiune cu <code>skeptic_on_chosen</code>:</b> când flag-ul e activ (manual sau auto-trigger), Skeptic focal rulează <b>în loc de retry</b> în banda [0.5, 0.7]. Retry rămâne fallback condițional doar dacă Skeptic verdict e <code>requires_redesign</code>.
</div>
```

## Out of scope

- **A4** — Dialectic-iterative card has no formal `## Dialectic iterative mode` section in SKILL.md; that's a SPEC-only situation. No sync needed until implementation lands.
- **B2** — Step 4 prompt description does not include `regression_risk -0.15/mitigation, cap -0.20`. The caveat lives correctly in SKILL.md L80-90; bringing it into the Step 4 summary would bloat the card. Skip.
- Other tabs (Architecture, Patterns, Voices, Files, Memory, Git) — unaffected by the 3 merged PRs.
- CSS / JavaScript changes — none. All edits reuse existing classes.
- Backporting to older runs/reports — no migration needed.
- New screenshots or visual mockups — text-only edits.

## Branch / commit plan

- Branch: `feat/arch-sync-skeptic-and-discipline`
- 1 commit: `feat(docs): sync architecture.html Modes+Flow with skeptic_on_chosen and benchmarking discipline`
- No Claude co-author per CLAUDE.md convention.
- Files touched: `docs/architecture.html` only.

## Verification post-merge

```bash
grep -c "skeptic_on_chosen\|Skeptic-on-chosen" docs/architecture.html   # ≥ 3
grep -c "Benchmarking discipline" docs/architecture.html                # ≥ 1
grep -n "Flow models —" docs/architecture.html                          # shows "10 moduri (9 active + 1 SPEC)"
```

## Open questions

None. Design decided through the brainstorming consult (option α + i):
- α: skeptic replaces retry in band [0.5, 0.7]; retry remains conditional fallback on `requires_redesign`.
- i: skeptic_on_chosen presented as own standard mode card (consistent with parallel_skeptic / dialectic_skeptic structure).
