/* modes.jsx — Consilium modes with animated play-through */

const MODES = [
  {
    id: 'seq_blind',
    name: 'Sequential — blind',
    tag: 'DEFAULT',
    plain: 'One Claude turn plays all three voices in order, in the same context. A small script strips each voice\'s output before passing it to the next — so each voice sees only what it needs. If confidence < 0.60 after the pipeline, the orchestrator automatically re-runs with Dialectic.',
    desc: 'A single Claude turn plays Conservator → Generator → Control sequentially. Between voices, scripts/strip_context.py trims each handoff to what the next voice needs — e.g. Control receives Generator\'s candidates without their rationale. (The Generator\'s narrower view of Conservator — magnitude, counterparty_risks, tokens_budget — is a manual handoff by the orchestrator; strip_context.py itself implements only the Gen→Control and Control→Conservator projections.) Auto-escalation: if confidence < 0.60 at Step 5b, the orchestrator re-runs the full pipeline with --mode dialectic — no user action required. The Dialectic result is the final output; the report carries auto_escalated: true. If Dialectic also < 0.60, no further escalation fires.',
    use: 'most deliberations — fast, with a chinese wall via context stripping',
    cost: '1× (baseline)',
    isolation: 'context strip',
    voices: 'Cons · Gen · Ctrl',
    subagents: '0',
  },
  {
    id: 'dialectic_v2',
    name: 'Dialectic',
    tag: 'OPT-IN',
    plain: 'A normal Sequential pass, then a single Skeptic sub-agent is dispatched specifically to challenge the chosen answer. The mode is that focal post-hoc challenge — code context is injected when the change is code, but writing the code itself is the Integration step.',
    desc: 'Stage 1: a normal Sequential pass (when the change is code, voice inputs are enriched with language / framework / files_touched[] / test_files[] / ci_gates context). Stage 2: a single Skeptic sub-agent receives only the chosen answer. Skeptic runs unconditionally — not gated on the confidence band.',
    use: 'any chosen answer that benefits from a focal post-hoc challenge before it ships',
    cost: '1.33×',
    isolation: 'in-process sequential + 1 isolated Skeptic',
    voices: 'Cons · Gen · Ctrl + Skeptic',
    subagents: '1 (Skeptic)',
  },
  {
    id: 'trias',
    name: 'Trias',
    tag: 'OPT-IN',
    plain: 'Three independent Claude sub-agents each run the full Sequential pipeline. Each has a different personality (bold / structural / protective). Each answer is then challenged by its own Skeptic sub-agent before the three (possibly revised) answers go to a democratic vote.',
    desc: 'Six sub-agents — three personalities (Pioneer / Architect / Steward), each running Sequential internally, then each personality\'s chosen is challenged by a dedicated Skeptic sub-agent at orchestrator level before the team vote. A simple majority vote decides the winner — 3-0 / 2-1 / 2-0. (Spec mandates parallel dispatch; in practice the runtime dispatches them serially — see the Trias parallelism audit, check_trias_parallelism.py.)',
    use: 'highest-stakes — DB migrations, security, large refactors',
    cost: '4× · worst case 10 sub-agents (1-1-1 → Round 2 → Skeptic)',
    isolation: 'sub-agent per personality + strip per voice inside',
    voices: '3× (Cons · Gen · Ctrl)',
    subagents: '6 (3 personality + 3 Skeptic; worst 10)',
  },
  {
    id: 'skeptic_flag',
    name: 'Skeptic-on-chosen',
    tag: 'FLAG',
    plain: 'A composable flag, not a standalone mode. Adds one Skeptic sub-agent to any base mode that challenges the chosen answer after aggregation. Auto-fires when the system isn\'t sure.',
    desc: 'Layered on top of any base mode. Adds +1 Skeptic sub-agent that receives only the chosen answer. Advisory by default; can override with --skeptic-can-override. Auto-triggers when confidence ∈ [0.0, 0.7]. Manual trigger: --skeptic-on-chosen.',
    use: 'whenever you want a focal challenger post-hoc',
    cost: 'base +1 (≈1.33× of a 3-voice base)',
    isolation: '+1 isolated Skeptic',
    voices: 'base + Skeptic',
    subagents: '+1',
  },
  {
    id: 'parallel_auto',
    name: 'Parallel — auto',
    tag: 'AUTO',
    plain: 'Not user-selectable. The system fires this automatically when a change is both critical and irreversible. A two-turn dispatch: first Generator runs alone, then Control and Conservator run in parallel — both receiving Generator\'s candidates so they have what they need to verdict and assess risk.',
    desc: 'Auto-triggered when magnitude=critical AND reversibility=irreversible. Two-turn flow per SKILL.md: Turn 1 dispatches Generator alone in an isolated sub-agent. Turn 2 dispatches Control and Conservator in parallel (same orchestrator message), both receiving Generator\'s candidates. This preserves the data dependency — Control needs candidates to verdict, Conservator needs them to assess risk — while isolating each voice in its own context within a turn.',
    use: 'auto-only · critical + irreversible changes',
    cost: '3× (3 sub-agents)',
    isolation: 'isolated per voice within each turn',
    voices: 'Gen → (Cons ∥ Ctrl)',
    subagents: '3 (1 per voice, 2 turns)',
  },
];

/* === Per-mode walkthrough scripts === */
/* Each step: { caption, nodes: {id:state}, arrows: ['id1', ...] } */
/* state: 'idle' | 'active' | 'done' */

const WALKTHROUGHS = {
  seq_blind: {
    name: 'Sequential — blind',
    layout: 'seq',
    steps: [
      { id: '1', name: 'arrive', caption: 'The diff arrives at the orchestrator (Claude main).',
        nodes: { orch: 'active', cons: 'idle', gen: 'idle', ctl: 'idle', agg: 'idle' }, arrows: [] },
      { id: '2', name: 'conservator', caption: 'Conservator runs first. Reads the diff, scores risk, sets tokens_budget for the others.',
        nodes: { orch: 'done', cons: 'active', gen: 'idle', ctl: 'idle', agg: 'idle' }, arrows: ['orch_cons'] },
      { id: '3', name: 'strip→gen', caption: 'Hand-off to Generator: only {magnitude, counterparty_risks, tokens_budget} are passed on — a manual projection by the orchestrator (strip_context.py itself covers the Gen→Control and Control→Conservator hops). The rest stays in main context.',
        nodes: { orch: 'done', cons: 'done', gen: 'active', ctl: 'idle', agg: 'idle' }, arrows: ['orch_cons', 'cons_gen'] },
      { id: '4', name: 'generator', caption: 'Generator produces 3–5 candidate approaches, always including do_nothing.',
        nodes: { orch: 'done', cons: 'done', gen: 'active', ctl: 'idle', agg: 'idle' }, arrows: ['orch_cons', 'cons_gen'] },
      { id: '5', name: 'strip→ctl', caption: 'Strip: Control receives candidates without the Generator\'s rationale.',
        nodes: { orch: 'done', cons: 'done', gen: 'done', ctl: 'active', agg: 'idle' }, arrows: ['orch_cons', 'cons_gen', 'gen_ctl'] },
      { id: '6', name: 'control', caption: 'Control verifies types, logic, and tests for each candidate.',
        nodes: { orch: 'done', cons: 'done', gen: 'done', ctl: 'active', agg: 'idle' }, arrows: ['orch_cons', 'cons_gen', 'gen_ctl'] },
      { id: '7', name: 'aggregate', caption: 'Aggregator applies conservative_override. Veto if Conservator scored risk > 0.8.',
        nodes: { orch: 'done', cons: 'done', gen: 'done', ctl: 'done', agg: 'active' }, arrows: ['orch_cons', 'cons_gen', 'gen_ctl', 'ctl_agg', 'cons_agg', 'gen_agg'] },
      { id: '8', name: 'done', caption: 'Winner chosen. Report written to runs/. Outcome logged to FEEDBACK.html. (If confidence < 0.60, the orchestrator re-runs the full pipeline with Dialectic automatically.)',
        nodes: { orch: 'done', cons: 'done', gen: 'done', ctl: 'done', agg: 'done' }, arrows: ['orch_cons', 'cons_gen', 'gen_ctl', 'ctl_agg', 'cons_agg', 'gen_agg', 'agg_out'] },
    ],
  },
  dialectic_v2: {
    name: 'Dialectic',
    layout: 'dialectic',
    steps: [
      { id: '1', name: 'arrive', caption: 'Diff arrives. Code context (language, framework, test files, CI gates) is gathered and injected into voice inputs.',
        nodes: { orch: 'active', cons: 'idle', gen: 'idle', ctl: 'idle', agg: 'idle', skp: 'idle' }, arrows: [] },
      { id: '2', name: 'sequential', caption: 'Stage 1: Sequential pass — Conservator → Generator → Control, all in main context with strips between.',
        nodes: { orch: 'done', cons: 'active', gen: 'active', ctl: 'active', agg: 'idle', skp: 'idle' }, arrows: ['orch_cons', 'cons_gen', 'gen_ctl'] },
      { id: '3', name: 'aggregate', caption: 'Aggregator picks chosen + confidence.',
        nodes: { orch: 'done', cons: 'done', gen: 'done', ctl: 'done', agg: 'active', skp: 'idle' }, arrows: ['orch_cons', 'cons_gen', 'gen_ctl', 'ctl_agg'] },
      { id: '4', name: 'skeptic dispatch', caption: 'Stage 2: a sub-agent Skeptic is dispatched with only the chosen answer + code context.',
        nodes: { orch: 'active', cons: 'done', gen: 'done', ctl: 'done', agg: 'done', skp: 'active' }, arrows: ['orch_cons', 'cons_gen', 'gen_ctl', 'ctl_agg', 'agg_skp'] },
      { id: '5', name: 'skeptic', caption: 'Skeptic challenges the chosen. Returns concrete_concerns[], can_object, addressable.',
        nodes: { orch: 'done', cons: 'done', gen: 'done', ctl: 'done', agg: 'done', skp: 'active' }, arrows: ['orch_cons', 'cons_gen', 'gen_ctl', 'ctl_agg', 'agg_skp'] },
      { id: '6', name: 'done', caption: 'Final report includes the Skeptic\'s objection (if any). Advisory by default.',
        nodes: { orch: 'done', cons: 'done', gen: 'done', ctl: 'done', agg: 'done', skp: 'done' }, arrows: ['orch_cons', 'cons_gen', 'gen_ctl', 'ctl_agg', 'agg_skp', 'skp_out'] },
    ],
  },
  trias: {
    name: 'Trias',
    layout: 'trias',
    steps: [
      { id: '1', name: 'arrive', caption: 'Diff arrives at the orchestrator.',
        nodes: { orch: 'active', p1: 'idle', p2: 'idle', p3: 'idle', vote: 'idle' }, arrows: [] },
      { id: '2', name: 'dispatch', caption: 'Three sub-agents dispatched — one per personality (serial in practice; parallel by spec mandate). Each gets a different lens prepended over the core voices.',
        nodes: { orch: 'done', p1: 'active', p2: 'active', p3: 'active', vote: 'idle' }, arrows: ['orch_p1', 'orch_p2', 'orch_p3'] },
      { id: '3', name: 'inside', caption: 'Inside each personality, the full Sequential pipeline runs: Conservator → Generator → Control with strips.',
        nodes: { orch: 'done', p1: 'active', p2: 'active', p3: 'active', vote: 'idle' }, arrows: ['orch_p1', 'orch_p2', 'orch_p3'] },
      { id: '4', name: 'chosen', caption: 'Each personality returns its own chosen answer.',
        nodes: { orch: 'done', p1: 'done', p2: 'done', p3: 'done', vote: 'idle' }, arrows: ['orch_p1', 'orch_p2', 'orch_p3'] },
      { id: '4b', name: 'skeptic ×3', caption: 'Three Skeptic sub-agents dispatched in parallel — one per chosen answer. An in_place objection revises that personality\'s pick before the vote.',
        nodes: { orch: 'done', p1: 'active', p2: 'active', p3: 'active', vote: 'idle' }, arrows: ['orch_p1', 'orch_p2', 'orch_p3'] },
      { id: '5', name: 'tally', caption: 'Democratic vote tally over the (possibly revised) answers. 3-0 → confidence 0.95. 2-1 → 0.75. 2-0 → 0.70. 1-1-1 → PEND + escalate.',
        nodes: { orch: 'done', p1: 'done', p2: 'done', p3: 'done', vote: 'active' }, arrows: ['orch_p1', 'orch_p2', 'orch_p3', 'p1_vote', 'p2_vote', 'p3_vote'] },
      { id: '6', name: 'done', caption: 'Winner declared. Dissent (if any) logged for human review.',
        nodes: { orch: 'done', p1: 'done', p2: 'done', p3: 'done', vote: 'done' }, arrows: ['orch_p1', 'orch_p2', 'orch_p3', 'p1_vote', 'p2_vote', 'p3_vote', 'vote_out'] },
    ],
  },
  skeptic_flag: {
    name: 'Skeptic-on-chosen',
    layout: 'skeptic',
    steps: [
      { id: '1', name: 'base mode', caption: 'Any base mode (Sequential, Trias, etc.) runs and produces a chosen + confidence.',
        nodes: { base: 'active', conf: 'idle', skp: 'idle', out: 'idle' }, arrows: [] },
      { id: '2', name: 'confidence', caption: 'Confidence gate checks the score after aggregation.',
        nodes: { base: 'done', conf: 'active', skp: 'idle', out: 'idle' }, arrows: ['base_conf'] },
      { id: '3', name: 'auto-trigger', caption: 'If confidence ∈ [0.0, 0.7] — below the trust floor — the Skeptic auto-fires. Manual via --skeptic-on-chosen.',
        nodes: { base: 'done', conf: 'done', skp: 'active', out: 'idle' }, arrows: ['base_conf', 'conf_skp'] },
      { id: '4', name: 'skeptic', caption: 'Skeptic receives only the chosen answer — never candidates, never verdicts. Tries to find a concrete failure mode.',
        nodes: { base: 'done', conf: 'done', skp: 'active', out: 'idle' }, arrows: ['base_conf', 'conf_skp'] },
      { id: '5', name: 'done', caption: 'Skeptic\'s objection lands in the report. Advisory by default. With --skeptic-can-override, it can change chosen.',
        nodes: { base: 'done', conf: 'done', skp: 'done', out: 'done' }, arrows: ['base_conf', 'conf_skp', 'skp_out'] },
    ],
  },
  seq_naive: { /* kept only for type safety — no longer in MODES list */
    name: 'Sequential — naive',
    layout: 'seq',
    steps: [
      { id: '1', name: 'arrive', caption: '',
        nodes: { orch: 'idle', cons: 'idle', gen: 'idle', ctl: 'idle', agg: 'idle' }, arrows: [] },
    ],
  },
  parallel_auto: {
    name: 'Parallel — auto',
    layout: 'parallel',
    steps: [
      { id: '1', name: 'gate', caption: 'A change arrives. Auto-gate checks: is this critical AND irreversible? If yes → Parallel mode auto-fires.',
        nodes: { orch: 'active', gate: 'active', cons: 'idle', gen: 'idle', ctl: 'idle', agg: 'idle' }, arrows: [] },
      { id: '2', name: 'turn 1 — Generator', caption: 'Turn 1: Generator dispatched alone in its own sub-agent. Returns candidates.',
        nodes: { orch: 'active', gate: 'done', cons: 'idle', gen: 'active', ctl: 'idle', agg: 'idle' }, arrows: ['orch_gen'] },
      { id: '3', name: 'turn 2 — Cons ∥ Ctrl', caption: 'Turn 2: Control and Conservator dispatched in parallel (same orchestrator message), both receiving Generator\'s candidates. Each runs isolated in its own context but sees the candidates it needs to verdict / assess risk.',
        nodes: { orch: 'done', gate: 'done', cons: 'active', gen: 'done', ctl: 'active', agg: 'idle' }, arrows: ['orch_gen', 'gen_cons', 'gen_ctl'] },
      { id: '4', name: 'collect', caption: 'Control and Conservator return their JSONs to the orchestrator.',
        nodes: { orch: 'done', gate: 'done', cons: 'done', gen: 'done', ctl: 'done', agg: 'active' }, arrows: ['orch_gen', 'gen_cons', 'gen_ctl', 'cons_agg', 'ctl_agg'] },
      { id: '5', name: 'aggregate', caption: 'Aggregator applies the cascade and conservative_override scheme over the three outputs.',
        nodes: { orch: 'done', gate: 'done', cons: 'done', gen: 'done', ctl: 'done', agg: 'active' }, arrows: ['orch_gen', 'gen_cons', 'gen_ctl', 'cons_agg', 'ctl_agg'] },
      { id: '6', name: 'done', caption: 'Winner chosen. Also fires as a silent audit every 20 Sequential runs (1/5 in HOT mode after ≥2 divergences in the last 5 audits) — implemented in scripts/audit_counter.py, state in .consilium/audit_state.json.',
        nodes: { orch: 'done', gate: 'done', cons: 'done', gen: 'done', ctl: 'done', agg: 'done' }, arrows: ['orch_gen', 'gen_cons', 'gen_ctl', 'cons_agg', 'gen_agg', 'ctl_agg', 'agg_out'] },
    ],
  },
};

function ModesSection() {
  const [active, setActive] = React.useState('seq_blind');
  const mode = MODES.find((m) => m.id === active);
  const walkthrough = WALKTHROUGHS[active];

  /* per-mode playback state */
  const [step, setStep] = React.useState(0);
  const [playing, setPlaying] = React.useState(false);
  const playRef = React.useRef(null);

  React.useEffect(() => {
    setStep(0);
    setPlaying(false);
  }, [active]);

  React.useEffect(() => {
    if (!playing) return;
    playRef.current = setTimeout(() => {
      setStep((s) => {
        if (s >= walkthrough.steps.length - 1) {
          setPlaying(false);
          return s;
        }
        return s + 1;
      });
    }, 1500);
    return () => clearTimeout(playRef.current);
  }, [playing, step, walkthrough]);

  const currentStep = walkthrough.steps[step] || walkthrough.steps[0];

  return (
    <section className="section section--tinted" id="modes">
      <div className="modes-bg-extra" aria-hidden="true" />
      <div className="container">
        <SectionHead
          num="07"
          eyebrow="Modes"
          title="Five ways to run the same voices."
          lede="Modes differ in how voices are isolated and how often they get to talk. Pick a mode below, then hit play to see how a single diff actually travels through it."
        />

        <div className="tldr">
          <span className="tldr__label">In plain words</span>
          <div>
            <p>Same three voices, different staging. The default mode runs everything in one Claude turn with information filtered between voices. Other modes spin up isolated sub-agents — three different "personalities" in <strong>Trias</strong>, or a single challenger in <strong>Dialectic</strong> and <strong>Skeptic-on-chosen</strong>. <strong>Parallel</strong> is no longer user-selectable — the system fires it automatically on critical, irreversible changes.</p>
          </div>
        </div>

        {/* Which mode when? — routing boundary from SKILL.md */}
        <div style={{ margin: '0 0 28px', border: '1px solid var(--rule)', borderRadius: 4, background: 'var(--paper)', overflow: 'hidden' }}>
          <div style={{ padding: '10px 16px', fontFamily: 'var(--font-mono)', fontSize: 10.5, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--ink-3)', borderBottom: '1px solid var(--rule)' }}>
            Which mode, when — the routing boundary
          </div>
          {[
            ['Obvious bugfix, or diff < 20 lines / 1 file', 'Sequential', 'the scope gate usually skips deliberation entirely'],
            ['Any other PR-level review', 'Sequential', 'auto Parallel cross-check fires on critical + irreversible'],
            ['A chosen answer came back shaky (confidence ≤ 0.7) with one nagging concern', 'Dialectic + skeptic_on_chosen', 'focal post-hoc challenge on exactly that answer'],
            ['2+ plausible architectural approaches, no clear winner', 'Trias', 'three personalities on three models, settled by vote'],
          ].map(([when, mode, why]) => (
            <div key={mode + when} style={{ display: 'grid', gridTemplateColumns: 'minmax(220px, 1.4fr) minmax(150px, 0.8fr) 1.2fr', gap: 12, padding: '10px 16px', borderBottom: '1px solid var(--rule)', fontSize: 13, alignItems: 'baseline' }}>
              <span style={{ color: 'var(--ink)' }}>{when}</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--ink)' }}>{mode}</span>
              <span style={{ color: 'var(--ink-2)' }}>{why}</span>
            </div>
          ))}
        </div>

        <div className="mode-panel">
          <div className="mode-panel__controls">
            <button className="btn" onClick={() => { if (step >= walkthrough.steps.length - 1) setStep(0); setPlaying(!playing); }}>
              {playing ? <>■ pause</> : <>▶ play how data flows</>}
            </button>
            <button className="btn btn--ghost" onClick={() => { setPlaying(false); setStep(0); }}>
              ⟲ reset
            </button>
            <div className="mode-panel__caption">{currentStep.caption}</div>
          </div>

          <div className="mode-panel__info">
            <div>
              <div className="mode-panel__sub">MODE · {mode.tag}</div>
              <h3 className="mode-panel__title">{mode.name}</h3>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-3)', letterSpacing: '0.08em', textTransform: 'uppercase', margin: '4px 0 6px' }}>
                Plain words
              </p>
              <p style={{ fontSize: 15, lineHeight: 1.5, color: 'var(--ink)', margin: '0 0 18px', textWrap: 'pretty' }}>
                {mode.plain}
              </p>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-3)', letterSpacing: '0.08em', textTransform: 'uppercase', margin: '0 0 6px' }}>
                Technical
              </p>
              <p className="mode-panel__desc">{mode.desc}</p>
            </div>
            <div>
              <dl className="mode-panel__meta">
                <dt>Use when</dt><dd>{mode.use}</dd>
                <dt>Cost</dt><dd>{mode.cost}</dd>
                <dt>Voices</dt><dd>{mode.voices}</dd>
                <dt>Sub-agents</dt><dd>{mode.subagents}</dd>
              </dl>
            </div>
          </div>

          {/* === Mode tabs — placed just before the diagram so they obviously control it === */}
          <div className="modes-tabs modes-tabs--inline">
            <span className="modes-tabs__label">switch mode →</span>
            {MODES.map((m) => (
              <button
                key={m.id}
                className="mode-tab"
                data-active={m.id === active}
                onClick={() => setActive(m.id)}
              >
                {m.name}
                <span className="mode-tab__tag">{m.tag}</span>
              </button>
            ))}
          </div>

          {/* === Full-width animated walkthrough === */}
          <div className="walkthrough">
            <div className="walkthrough__timeline">
              {walkthrough.steps.map((s, i) => {
                const state = i < step ? 'done' : (i === step ? 'active' : 'idle');
                return (
                  <button
                    key={s.id}
                    className="timeline-step"
                    data-state={state}
                    onClick={() => { setPlaying(false); setStep(i); }}
                  >
                    <span className="timeline-step__id">{s.id}</span>
                    <span className="timeline-step__name">{s.name}</span>
                  </button>
                );
              })}
            </div>

            <div className="walkthrough__stage">
              <ModeStage layout={walkthrough.layout} step={currentStep} />
            </div>

            <div className="mode-panel__controls mode-panel__controls--bottom">
              <button className="btn" onClick={() => { if (step >= walkthrough.steps.length - 1) setStep(0); setPlaying(!playing); }}>
                {playing ? <>■ pause</> : <>▶ play how data flows</>}
              </button>
              <button className="btn btn--ghost" onClick={() => { setPlaying(false); setStep(0); }}>
                ⟲ reset
              </button>
              <div className="mode-panel__caption">
                <span className="mode-panel__caption-hint">switching modes redraws this diagram →</span>
              </div>
            </div>
          </div>
        </div>

        {/* === Parallel — auto: when, why, what next === */}
        <div className="note" style={{ marginTop: 36 }}>
          <span className="note__label">Parallel — auto, in depth</span>
          <span>
            <strong>When</strong> — the orchestrator never picks this by hand. It fires automatically in two cases: (1) the Conservator scores a change as <code>magnitude = critical</code> <em>and</em> <code>reversibility = irreversible</code>; (2) as a silent audit on every 20th run (rising to 1-in-5 if it keeps diverging from Sequential).{' '}
            <strong>Why</strong> — true isolation (three voices in three separate context windows, no shared memory) costs 3×, so it is held back for the calls where a wrong answer is most expensive, and for keeping the cheap default honest.{' '}
            <strong>After</strong> — the parallel result cross-checks the Sequential chosen answer; any divergence is surfaced in the report rather than silently resolved, then the run continues to confidence → canonical report → (if files were requested) the implementation pipeline.
          </span>
        </div>

        {/* === End-to-end lifecycle: request → deliberation → code → learn === */}
        <h3 className="h-sub" style={{ fontSize: 20, margin: '44px 0 4px' }}>From request to written code</h3>
        <p className="body-prose" style={{ color: 'var(--ink-2)', fontSize: 14, marginBottom: 18, maxWidth: 760 }}>
          A mode is only the middle act. Here is the whole path a change travels — and how it loops back to make the next run smarter.
        </p>
        <div style={{ display: 'flex', alignItems: 'stretch', gap: 0, overflowX: 'auto', fontFamily: 'var(--font-mono)' }}>
          {[
            { tag: 'USER', title: '/consilium', sub: 'invokes the skill on a diff, a question, or a change to plan', color: 'var(--ink)' },
            { tag: 'DELIBERATION', title: 'a mode runs', sub: 'Conservator → Generator → Control under the 8-component veto cascade → a chosen approach + confidence, saved as canonical JSON in runs/', color: 'var(--ctl)' },
            { tag: 'IMPLEMENTATION', title: 'Step 7 pipeline', sub: 'if the prompt declares deliverables: Coder → (Test Writer ∥ Reviewer) → red→green gate → files written to disk', color: 'var(--gen)' },
            { tag: 'LEARN', title: 'feedback loop', sub: 'the outcome is logged to FEEDBACK.html; priors.py feeds it into the next deliberation', color: 'var(--con)' },
          ].map((s, i, arr) => (
            <React.Fragment key={s.tag}>
              <div style={{ flex: '1 1 0', minWidth: 150, padding: '14px 16px', border: '1px solid var(--rule)', borderTop: `3px solid ${s.color}`, borderRadius: 4, background: 'var(--paper)' }}>
                <div style={{ fontSize: 10, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--ink-3)', marginBottom: 4 }}>{s.tag}</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: s.color, marginBottom: 6 }}>{s.title}</div>
                <div style={{ fontSize: 11.5, color: 'var(--ink-2)', lineHeight: 1.5, fontFamily: 'var(--font-sans)' }}>{s.sub}</div>
              </div>
              {i < arr.length - 1 && (
                <div style={{ alignSelf: 'center', padding: '0 8px', color: 'var(--ink-3)', fontSize: 14, flexShrink: 0 }}>▶</div>
              )}
            </React.Fragment>
          ))}
        </div>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-3)', marginTop: 8 }}>
          ↻ LEARN feeds back into the next DELIBERATION — the loop closes on disk. The last two stages have their own tabs: <strong>Integration</strong> (pipeline) and <strong>Calibration</strong> (feedback).
        </p>

        <CostScatter />
        <CostBars />
      </div>
    </section>
  );
}

/* === Per-layout SVG stages === */

function ModeStage({ layout, step }) {
  switch (layout) {
    case 'seq':       return <StageSeq step={step} />;
    case 'dialectic': return <StageDialectic step={step} />;
    case 'trias':     return <StageTrias step={step} />;
    case 'skeptic':   return <StageSkeptic step={step} />;
    case 'parallel':  return <StageParallel step={step} />;
    default: return null;
  }
}

/* Helpers */

function WVoice({ x, y, v, state, label, w = 86, h = 44, dashed }) {
  const c = { gen: 'var(--gen)', ctl: 'var(--ctl)', con: 'var(--con)', skp: 'oklch(0.55 0.16 320)' }[v] || 'var(--ink)';
  const s = { gen: 'var(--gen-soft)', ctl: 'var(--ctl-soft)', con: 'var(--con-soft)', skp: 'oklch(0.94 0.04 320)' }[v] || 'var(--paper)';
  const letter = { gen: 'G', ctl: 'C', con: 'K', skp: 'S' }[v] || '';
  return (
    <g className={`wt-voice wt-voice--${state}`}>
      <rect x={x} y={y} width={w} height={h} rx="4" fill={s} stroke={c} strokeWidth="1.4" strokeDasharray={dashed ? '4 3' : undefined} />
      <circle cx={x + 14} cy={y + h / 2} r="9" fill={c} />
      <text x={x + 14} y={y + h / 2 + 3} textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: 11, fill: 'var(--paper)' }}>{letter}</text>
      <text x={x + 28} y={y + h / 2 + 4} style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fill: 'var(--ink)' }}>{label}</text>
    </g>
  );
}

function WBox({ x, y, w, h, title, state, dashed, fill }) {
  return (
    <g className={`wt-voice wt-voice--${state}`}>
      <rect x={x} y={y} width={w} height={h} rx="4" fill={fill || 'var(--paper)'} stroke="var(--ink)" strokeWidth="1.4" strokeDasharray={dashed ? '4 3' : undefined} />
      <text x={x + w / 2} y={y + h / 2 + 4} textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 500, fill: 'var(--ink)' }}>{title}</text>
    </g>
  );
}

function WArrow({ d, state, dashed, label, labelX, labelY, color = 'var(--ink)' }) {
  return (
    <g className={`wt-arrow wt-arrow--${state}`}>
      <path d={d} fill="none" stroke={color} strokeWidth="1.6" strokeDasharray={dashed ? '4 3' : undefined} markerEnd="url(#wt-arrow)" />
      {label && state !== 'idle' && (
        <text x={labelX} y={labelY} textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: 'var(--ink-3)' }}>{label}</text>
      )}
    </g>
  );
}

function WtDefs() {
  return (
    <defs>
      <marker id="wt-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10z" fill="var(--ink)" />
      </marker>
    </defs>
  );
}

/* === Sequential stage (handles blind + naive) === */
function StageSeq({ step }) {
  const ns = step.nodes;
  const ar = step.arrows;

  const has = (id) => ar.includes(id);
  const stripState = (full, stripped) =>
    has(stripped) ? 'active' : (has(full) ? 'done' : 'idle');

  return (
    <svg viewBox="0 0 720 320" className="diagram">
      <WtDefs />

      {/* Orchestrator */}
      <WBox x={20} y={140} w={90} h={48} title="orch" state={ns.orch} />
      <text x={65} y={130} textAnchor="middle" className="d-faint" style={{ fontSize: 9 }}>claude main</text>

      {/* Three voices */}
      <WVoice x={170} y={48} v="con" state={ns.cons} label="Conservator" />
      <WVoice x={170} y={144} v="gen" state={ns.gen} label="Generator" />
      <WVoice x={170} y={240} v="ctl" state={ns.ctl} label="Control" />

      {/* Aggregator */}
      <WBox x={400} y={140} w={90} h={48} title="aggregate" state={ns.agg} fill="var(--paper-2)" />

      {/* Output */}
      <WBox x={560} y={140} w={130} h={48} title="chosen → runs/" state={has('agg_out') ? 'done' : 'idle'} />

      {/* Arrows: orch → cons */}
      <WArrow d="M 110 164 C 130 164, 140 80, 168 78" state={has('orch_cons') ? (ns.cons === 'active' ? 'active' : 'done') : 'idle'} />

      {/* cons → gen (strip OR full) */}
      <WArrow
        d="M 213 96 C 213 130, 213 142, 213 144"
        state={has('cons_gen') ? (ns.gen === 'active' ? 'active' : 'done') : (has('cons_gen_full') ? (ns.gen === 'active' ? 'active' : 'done') : 'idle')}
        dashed={has('cons_gen')}
        label={has('cons_gen') ? 'strip → budget' : (has('cons_gen_full') ? 'FULL' : '')}
        labelX={272} labelY={120}
      />

      {/* gen → ctl */}
      <WArrow
        d="M 213 188 C 213 220, 213 234, 213 240"
        state={has('gen_ctl') ? (ns.ctl === 'active' ? 'active' : 'done') : (has('gen_ctl_full') ? (ns.ctl === 'active' ? 'active' : 'done') : 'idle')}
        dashed={has('gen_ctl')}
        label={has('gen_ctl') ? 'strip → candidates' : (has('gen_ctl_full') ? 'FULL' : '')}
        labelX={278} labelY={218}
      />

      {/* All three voices → aggregator */}
      <WArrow d="M 256 78 C 310 78, 360 140, 400 162" state={has('cons_agg') ? 'active' : 'idle'} />
      <WArrow d="M 256 166 L 400 166" state={has('gen_agg') ? 'active' : 'idle'} />
      <WArrow d="M 256 262 C 310 262, 360 188, 400 170" state={has('ctl_agg') ? 'active' : 'idle'} />

      {/* aggregator → output */}
      <WArrow d="M 490 164 L 560 164" state={has('agg_out') ? 'active' : 'idle'} />
    </svg>
  );
}

/* === Dialectic stage === */
function StageDialectic({ step }) {
  const ns = step.nodes;
  const ar = step.arrows;
  const has = (id) => ar.includes(id);

  return (
    <svg viewBox="0 0 720 360" className="diagram">
      <WtDefs />

      <text x="20" y="22" className="d-faint">STAGE 1 — SEQUENTIAL (IN MAIN CONTEXT)</text>
      <rect x="14" y="32" width="500" height="180" rx="4" fill="var(--paper-2)" stroke="var(--rule)" strokeDasharray="3 3" />

      <WBox x={28} y={120} w={66} h={36} title="orch" state={ns.orch} />
      <WVoice x={130} y={50} v="con" state={ns.cons} label="Cons" />
      <WVoice x={130} y={118} v="gen" state={ns.gen} label="Gen" />
      <WVoice x={130} y={186} v="ctl" state={ns.ctl} label="Ctrl" />

      <WBox x={290} y={120} w={90} h={36} title="aggregate" state={ns.agg} fill="var(--paper-3)" />

      <WArrow d="M 94 138 C 110 138, 110 70, 128 70" state={has('orch_cons') ? 'done' : 'idle'} />
      <WArrow d="M 173 86 L 173 118" state={has('cons_gen') ? (ns.gen === 'active' ? 'active' : 'done') : 'idle'} dashed />
      <WArrow d="M 173 154 L 173 186" state={has('gen_ctl') ? (ns.ctl === 'active' ? 'active' : 'done') : 'idle'} dashed />
      <WArrow d="M 218 138 L 290 138" state={has('ctl_agg') ? (ns.agg === 'active' ? 'active' : 'done') : 'idle'} />

      <text x="20" y="252" className="d-faint">STAGE 2 — SKEPTIC SUB-AGENT (ISOLATED)</text>
      <rect x="14" y="262" width="500" height="80" rx="4" fill="var(--paper-2)" stroke="var(--rule)" strokeDasharray="3 3" />
      <WVoice x={130} y={282} v="skp" state={ns.skp} label="Skeptic" dashed />

      {/* agg → skeptic */}
      <WArrow d="M 335 156 C 335 200, 220 220, 175 282" state={has('agg_skp') ? (ns.skp === 'active' ? 'active' : 'done') : 'idle'} dashed
        label="chosen + code ctx" labelX={400} labelY={234} />

      {/* output */}
      <WBox x={550} y={130} w={140} h={48} title="chosen + objection" state={has('skp_out') ? 'done' : 'idle'} />
      <WArrow d="M 220 304 C 400 304, 480 200, 548 158" state={has('skp_out') ? 'done' : 'idle'} />
    </svg>
  );
}

/* === Trias stage === */
function StageTrias({ step }) {
  const ns = step.nodes;
  const ar = step.arrows;
  const has = (id) => ar.includes(id);

  const personalities = [
    { id: 'p1', name: 'Pioneer', y: 24, weights: 'G 0.49 · C 0.30 · K 0.21' },
    { id: 'p2', name: 'Architect', y: 130, weights: 'G 0.30 · C 0.40 · K 0.30' },
    { id: 'p3', name: 'Steward', y: 236, weights: 'G 0.30 · C 0.30 · K 0.40' },
  ];

  return (
    <svg viewBox="0 0 720 360" className="diagram">
      <WtDefs />

      <WBox x={20} y={156} w={76} h={48} title="orch" state={ns.orch} />
      <text x={58} y={148} textAnchor="middle" className="d-faint" style={{ fontSize: 9 }}>claude main</text>

      {personalities.map((p) => {
        const inside = ['active', 'done'].includes(ns[p.id]);
        return (
          <g key={p.id} className={`wt-voice wt-voice--${ns[p.id]}`}>
            <rect x="160" y={p.y} width="340" height="76" rx="4" fill="var(--paper-2)" stroke="var(--ink)" strokeWidth="1.4" strokeDasharray="4 3" />
            <text x="172" y={p.y + 18} style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 500, fill: 'var(--ink)' }}>{p.name}</text>
            <text x="172" y={p.y + 32} style={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: 'var(--ink-3)' }}>{p.weights}</text>

            {/* inner sequential indicator */}
            <WVoice x={172} y={p.y + 38} v="con" state={inside ? 'active' : 'idle'} label="" w={42} h={28} />
            <WVoice x={232} y={p.y + 38} v="gen" state={inside ? 'active' : 'idle'} label="" w={42} h={28} />
            <WVoice x={292} y={p.y + 38} v="ctl" state={inside ? 'active' : 'idle'} label="" w={42} h={28} />

            {/* strip walls within */}
            <line x1="226" y1={p.y + 38} x2="226" y2={p.y + 66} stroke="var(--ink)" strokeWidth="1.4" strokeDasharray="2 4" />
            <line x1="286" y1={p.y + 38} x2="286" y2={p.y + 66} stroke="var(--ink)" strokeWidth="1.4" strokeDasharray="2 4" />

            {/* chosen output */}
            <rect x="360" y={p.y + 38} width="130" height="28" rx="3" fill={ns[p.id] === 'done' ? 'var(--paper)' : 'transparent'} stroke="var(--rule-2)" />
            <text x="425" y={p.y + 56} textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: ns[p.id] === 'done' ? 'var(--ink)' : 'var(--ink-3)' }}>chosen</text>
          </g>
        );
      })}

      {/* orchestrator → personalities */}
      <WArrow d="M 96 180 C 130 180, 130 62, 160 62" state={has('orch_p1') ? (ns.p1 === 'active' ? 'active' : 'done') : 'idle'} dashed />
      <WArrow d="M 96 180 L 160 168" state={has('orch_p2') ? (ns.p2 === 'active' ? 'active' : 'done') : 'idle'} dashed />
      <WArrow d="M 96 180 C 130 180, 130 274, 160 274" state={has('orch_p3') ? (ns.p3 === 'active' ? 'active' : 'done') : 'idle'} dashed />

      {/* personalities → vote */}
      <WBox x={550} y={140} w={120} h={80} title="vote tally" state={ns.vote} fill="var(--paper-3)" />

      <WArrow d="M 490 52 C 530 52, 540 130, 550 162" state={has('p1_vote') ? (ns.vote === 'active' ? 'active' : 'done') : 'idle'} dashed />
      <WArrow d="M 490 168 L 550 178" state={has('p2_vote') ? (ns.vote === 'active' ? 'active' : 'done') : 'idle'} dashed />
      <WArrow d="M 490 264 C 530 264, 540 200, 550 192" state={has('p3_vote') ? (ns.vote === 'active' ? 'active' : 'done') : 'idle'} dashed />

      {/* output */}
      <text x="610" y="240" textAnchor="middle" className="d-faint" style={{ fontSize: 9 }}>3-0 / 2-1 / 2-0</text>
    </svg>
  );
}

/* === Skeptic-flag stage === */
function StageSkeptic({ step }) {
  const ns = step.nodes;
  const ar = step.arrows;
  const has = (id) => ar.includes(id);

  return (
    <svg viewBox="0 0 720 320" className="diagram">
      <WtDefs />

      <WBox x={30} y={130} w={150} h={60} title="any base mode" state={ns.base} fill="var(--paper-2)" />
      <text x={105} y={210} textAnchor="middle" className="d-faint" style={{ fontSize: 9 }}>Sequential / Trias / Dialectic …</text>

      <WBox x={250} y={140} w={130} h={40} title="confidence" state={ns.conf} />
      <text x={315} y={196} textAnchor="middle" className="d-faint" style={{ fontSize: 9 }}>checked after aggregate</text>

      <g>
        <rect x="250" y="225" width="130" height="14" fill="var(--paper-2)" stroke="var(--rule)" rx="2" />
        <rect x="250" y="225" width="65" height="14" fill="oklch(0.92 0.06 5)" stroke="oklch(0.6 0.15 5)" rx="2" />
        <rect x="315" y="225" width="33" height="14" fill="oklch(0.93 0.07 60)" stroke="oklch(0.6 0.14 60)" rx="2" />
        <rect x="348" y="225" width="32" height="14" fill="oklch(0.94 0.05 150)" stroke="oklch(0.55 0.12 150)" rx="2" />
        <text x="315" y="252" textAnchor="middle" className="d-faint" style={{ fontSize: 8 }}>0.0 — uncertain — 0.7</text>
      </g>

      <WVoice x={460} y={130} v="skp" state={ns.skp} label="Skeptic" dashed w={140} h={50} />
      <text x={530} y={210} textAnchor="middle" className="d-faint" style={{ fontSize: 9 }}>sees only chosen</text>

      <WBox x={620} y={130} w={80} h={50} title="report" state={ns.out} />

      <WArrow d="M 180 160 L 250 160" state={has('base_conf') ? 'done' : 'idle'} />
      <WArrow d="M 380 160 L 458 154" state={has('conf_skp') ? (ns.skp === 'active' ? 'active' : 'done') : 'idle'} dashed
        label="conf ∈ [0.0, 0.7]" labelX={420} labelY={138} />
      <WArrow d="M 600 154 L 620 154" state={has('skp_out') ? 'done' : 'idle'} />
    </svg>
  );
}

/* === Parallel — auto stage === */
function StageParallel({ step }) {
  const ns = step.nodes;
  const ar = step.arrows;
  const has = (id) => ar.includes(id);

  return (
    <svg viewBox="0 0 720 320" className="diagram">
      <WtDefs />

      <WBox x={20} y={140} w={90} h={48} title="orch" state={ns.orch} />
      <text x={65} y={130} textAnchor="middle" className="d-faint" style={{ fontSize: 9 }}>claude main</text>

      <g>
        <polygon
          points="180,164 220,144 260,164 220,184"
          fill={ns.gate === 'active' || ns.gate === 'done' ? 'var(--signal-soft)' : 'var(--paper)'}
          stroke={ns.gate === 'active' || ns.gate === 'done' ? 'var(--signal)' : 'var(--ink)'}
          strokeWidth="1.4"
        />
        <text x={220} y={168} textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 500, fill: 'var(--ink)' }}>auto-gate</text>
        <text x={220} y={205} textAnchor="middle" className="d-faint" style={{ fontSize: 8 }}>critical + irreversible?</text>
      </g>

      <WArrow d="M 110 164 L 180 164" state={ns.gate !== 'idle' ? 'done' : 'idle'} />

      <WVoice x={330} y={48} v="con" state={ns.cons} label="Conservator" dashed w={120} h={50} />
      <WVoice x={330} y={134} v="gen" state={ns.gen} label="Generator" dashed w={120} h={50} />
      <WVoice x={330} y={220} v="ctl" state={ns.ctl} label="Control" dashed w={120} h={50} />

      <text x={390} y={36} textAnchor="middle" className="d-faint" style={{ fontSize: 8 }}>isolated context windows</text>

      <WArrow d="M 260 164 L 328 158" state={has('orch_gen') ? (ns.gen === 'active' ? 'active' : 'done') : 'idle'} dashed />
      <WArrow d="M 390 134 L 390 100" state={has('gen_cons') ? (ns.cons === 'active' ? 'active' : 'done') : 'idle'} dashed />
      <WArrow d="M 390 184 L 390 218" state={has('gen_ctl') ? (ns.ctl === 'active' ? 'active' : 'done') : 'idle'} dashed />

      <WBox x={510} y={140} w={90} h={48} title="aggregate" state={ns.agg} fill="var(--paper-2)" />

      <WArrow d="M 450 72 C 480 72, 490 130, 510 158" state={has('cons_agg') ? 'active' : 'idle'} />
      <WArrow d="M 450 158 L 510 162" state={has('gen_agg') ? 'active' : 'idle'} />
      <WArrow d="M 450 244 C 480 244, 490 188, 510 170" state={has('ctl_agg') ? 'active' : 'idle'} />

      <WBox x={620} y={140} w={80} h={48} title="report" state={has('agg_out') ? 'done' : 'idle'} />
      <WArrow d="M 600 164 L 620 164" state={has('agg_out') ? 'active' : 'idle'} />

      <text x="360" y="298" textAnchor="middle" className="d-faint" style={{ fontSize: 9, fill: 'var(--ink-3)' }}>
        auto-only · also runs silent audit every 20 runs
      </text>
    </svg>
  );
}

window.ModesSection = ModesSection;
