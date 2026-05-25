/* pipeline.jsx — animated step 0 → 7 walkthrough (RUND2: Conservator first) */

const STEPS = [
  {
    id: '0', name: 'bootstrap',
    title: 'Bootstrap',
    desc: 'Reads each voice\'s contract from prompts/voices/ and runs priors.py to pull soft priors from past runs — override rate, veto rate, recurring keywords, pending entries. Three signals can block until resolved: stale_pendings, missing_feedback_runs, pend_pressure.',
    plain: 'Wakes up. Reads each voice\'s job description and checks what worked last time.',
    inputs: ['prompts/voices/*.md', 'runs/*.json', 'FEEDBACK.html'],
    outputs: ['soft priors', 'stale_pendings prompt?'],
    scripts: ['priors.py'],
  },
  {
    id: '1', name: 'goal',
    title: 'Gather & Goal',
    desc: 'Reads the proposed change. Identifies scope, type, blast radius. Reformulates intent as a single testable success_criterion. Clarity gate: if two plausible interpretations exist, halts and asks which is real.',
    plain: 'Looks at the change. Restates the goal in one sentence anyone could test against.',
    inputs: ['diff', 'user prompt'],
    outputs: ['success_criterion', 'verification command'],
    scripts: [],
  },
  {
    id: '1.5', name: 'scope gate',
    title: 'Scope gate',
    desc: 'Auto-skip when the diff is trivial: ≤1 file, ≤15 lines, no sensitive paths (auth/, security/, migrations/, .github/workflows/, secrets, .env, Dockerfile, *.tf). Fails open — non-diff tasks bypass entirely.',
    plain: 'If the change is a typo or one-liner, skip the full deliberation.',
    inputs: ['diff metrics', 'blocklist'],
    outputs: ['should_skip: true → step 6', 'or → continue'],
    scripts: ['scope_gate.py', 'probe_change.py'],
  },
  {
    id: '2', name: 'conservator',
    title: 'Conservator',
    desc: 'Runs FIRST in RUND2. Answers Q1–Q5: reversibility, magnitude, counterparty risks, status-quo bias, meta_recommendation. Its tokens_budget output caps how deep Generator and Control go. irreversibility_flag:true halts the pipeline until the user explicitly confirms.',
    plain: 'The cautious one. Sizes up the risk before anyone proposes anything, and sets a token budget for the others.',
    inputs: ['diff + context'],
    outputs: ['risk_score', 'tokens_budget', 'meta_recommendation', 'irreversibility_flag'],
    scripts: ['probe_change.py'],
    voice: 'con',
  },
  {
    id: '3', name: 'generator',
    title: 'Generator',
    desc: 'Produces 3–5 candidate approaches via divergent thinking. Always includes do_nothing. Respects tokens_budget.generator. Adversarial is conditional: only when the change touches shared/core code or a function with >3 external callers.',
    plain: 'The brainstormer. Comes up with 3–5 ways to do the change, including "do nothing".',
    inputs: ['success_criterion', 'tokens_budget.generator', 'magnitude'],
    outputs: ['candidates[]', 'preferred', 'fallback_scenario'],
    scripts: [],
    voice: 'gen',
  },
  {
    id: '4', name: 'control',
    title: 'Control',
    desc: 'Per candidate: types → logic → tests → style. Writes tests_to_write for every valid:true (1–4 acceptance tests). Receives the full Conservator and Generator outputs so it can spot disagreements.',
    plain: 'The technical checker. Marks each candidate valid or not, writes the tests it should pass.',
    inputs: ['candidates', 'Conservator output (full)'],
    outputs: ['verdicts[]', 'glossary', 'disagreements'],
    scripts: [],
    voice: 'ctl',
  },
  {
    id: '5', name: 'aggregate',
    title: 'Aggregate',
    desc: 'Applies the chosen scheme. Default is conservative_override — weighted mean of generator + control + safety (where safety = 1 − conservator), with a unilateral Conservator veto at risk > 0.8. If every candidate is vetoed, attaches retry_suggested with a threshold relaxation.',
    plain: 'Combines the three opinions into one winner. If risk is too high, nothing wins.',
    inputs: ['verdicts', 'scores'],
    outputs: ['chosen_approach', 'ranking', '[retry_suggested]'],
    scripts: ['aggregator.py'],
  },
  {
    id: '5b', name: 'confidence',
    title: 'Confidence',
    desc: 'Derives a score from inter-voice agreement and the gap to the runner-up. Mode confidence floor: sequential=0.70, dialectic=0.75, trias=0.80. A run below floor signals the mode did not deliver value for the cost — logged as WEAK in FEEDBACK.html. ≥ 0.7 → continue. ∈ [0.5, 0.7] → auto-triggers Skeptic (if mode supports it). < 0.5 → retry context, then ask user.',
    plain: 'How sure are the voices? Each mode has a confidence floor it should clear — if it doesn\'t, that\'s a signal the mode was wrong for this task.',
    inputs: ['ranking', 'voice variances', 'mode'],
    outputs: ['confidence ∈ [0, 1]', 'below_floor: bool'],
    scripts: ['confidence.py'],
  },
  {
    id: '5c', name: 'meta-critic',
    title: 'Meta-critic (retired)',
    desc: 'Retired 2026-05-25 — moved to scripts/deprecated/. Advisory only; never blocked. Trimmed to a single conservator_spread heuristic (generator_divergence + control_concreteness removed, 0/163 fires). The substance-validation gap is now an accepted known limitation.',
    plain: 'Used to grade deliberation quality (advisory). Retired — kept for reference only.',
    inputs: ['voice outputs'],
    outputs: ['deliberation_quality.flags'],
    scripts: ['scripts/deprecated/meta_critic.py'],
  },
  {
    id: '5d', name: 'retry',
    title: 'Retry on low confidence',
    desc: 'Single pass only. If confidence < 0.7, retry_context.py returns the top-2 candidates with files/symbols to read or grep. The orchestrator gathers extra context and re-runs Generator/Control/Conservator once with enriched input. Headless mode skips this step.',
    plain: 'If still uncertain after one round, gather more context and re-deliberate exactly once.',
    inputs: ['top-2 candidates', 'codebase signals'],
    outputs: ['enriched bundle → step 2 again'],
    scripts: ['retry_context.py'],
  },
  {
    id: '6', name: 'report',
    title: 'Report',
    desc: 'Telemetry mandate (before build_report): every voice/sub-agent dispatch must accumulate {tokens_in, tokens_out, latency_ms} into telemetry.voices.<name>. telemetry.mode and telemetry.dispatch_count are also required. Runs without telemetry return null from efficiency.py and pollute per-mode averages. validate_report.py enforces Principle #4. log_feedback.py appends a row to FEEDBACK.html.',
    plain: 'Writes the final decision to disk. Telemetry per voice is mandatory — without it the run is invisible to cost analysis.',
    inputs: ['everything above', 'telemetry per voice'],
    outputs: ['runs/<ts>.json', 'FEEDBACK.html row'],
    scripts: ['build_report.py', 'validate_report.py', 'log_feedback.py'],
  },
  {
    id: '7', name: 'infer pipeline',
    title: 'Infer pipeline',
    desc: 'Conditional — runs only when the prompt declared Required output files or Deliverables. infer_pipeline.py deduces and executes the implementation steps after step 6. Skipped if chosen_approach ∈ {do_nothing, skipped}. Headless flag: --yes.',
    plain: 'If the change should actually ship, this is the step that ships it.',
    inputs: ['chosen_approach', 'declared deliverables'],
    outputs: ['implementation steps[]', 'execution result'],
    scripts: ['infer_pipeline.py'],
  },
];

function PipelineSection() {
  const [active, setActive] = React.useState(3); // start on Conservator
  const [playing, setPlaying] = React.useState(false);
  const playRef = React.useRef(null);

  React.useEffect(() => {
    if (!playing) return;
    playRef.current = setTimeout(() => {
      setActive((a) => {
        if (a >= STEPS.length - 1) {
          setPlaying(false);
          return a;
        }
        return a + 1;
      });
    }, 1500);
    return () => clearTimeout(playRef.current);
  }, [playing, active]);

  const step = STEPS[active];

  return (
    <section className="section section--tinted" id="pipeline">
      <div className="container">
        <SectionHead
          num="04"
          eyebrow="The pipeline"
          title="One deliberation, twelve steps."
          lede="0 → 7, including 1.5 / 5b / 5c / 5d. Hit play and watch the data move from station to station."
        />

        <div className="tldr">
          <span className="tldr__label">In plain words</span>
          <div>
            <p>The change goes in. <strong>Conservator</strong> sizes up risk first and budgets the rest. <strong>Generator</strong> proposes options. <strong>Control</strong> verifies them. The aggregator picks a winner. If confidence is shaky, the <strong>Skeptic</strong> may get called. A report lands on disk and feeds the next run.</p>
          </div>
        </div>

        <div className="pipeline">
          <div className="pipeline__playhead">
            <button className="btn" onClick={() => { if (active >= STEPS.length - 1) setActive(0); setPlaying(!playing); }}>
              {playing ? <>■ pause</> : <>▶ play walkthrough</>}
            </button>
            <button className="btn btn--ghost" onClick={() => { setPlaying(false); setActive(0); }}>
              ⟲ reset
            </button>
            <span style={{ color: 'var(--ink-3)' }}>step {active + 1} of {STEPS.length}</span>
          </div>

          <PipelineDiagram active={active} />

          <div className="step-track" style={{ marginTop: 28 }}>
            <div className="step-list">
              {STEPS.map((s, i) => (
                <button
                  key={s.id}
                  className="step-pill"
                  data-active={i === active}
                  onClick={() => { setPlaying(false); setActive(i); }}
                >
                  <span className="step-pill__id">STEP {s.id}</span>
                  <span className="step-pill__name">{s.name}</span>
                </button>
              ))}
            </div>
            <div className="step-detail">
              <div className="step-detail__left">
                <div className="step-detail__id">Step {step.id}{step.voice && <> · <VToken v={step.voice} /></>}</div>
                <h3 className="step-detail__title">{step.title}</h3>
                {step.plain && (
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.03em', margin: '0 0 12px', textTransform: 'uppercase' }}>
                    Plain words
                  </p>
                )}
                {step.plain && (
                  <p style={{ fontSize: 15, lineHeight: 1.5, color: 'var(--ink)', margin: '0 0 16px', maxWidth: 480, textWrap: 'pretty' }}>
                    {step.plain}
                  </p>
                )}
                <p style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.03em', margin: '0 0 8px', textTransform: 'uppercase' }}>
                  Technical
                </p>
                <p className="step-detail__desc">{step.desc}</p>
                {step.scripts.length > 0 && (
                  <>
                    <div className="step-detail__id" style={{ marginTop: 18 }}>Scripts</div>
                    <div className="step-detail__scripts">
                      {step.scripts.map((s) => <span key={s} className="script-chip">{s}</span>)}
                    </div>
                  </>
                )}
              </div>
              <div className="step-detail__right">
                <div>
                  {step.inputs.map((v) => (
                    <div key={v} className="io-row">
                      <span className="io-row__label">in</span>
                      <span className="io-row__val"><code>{v}</code></span>
                    </div>
                  ))}
                  {step.outputs.map((v) => (
                    <div key={v} className="io-row">
                      <span className="io-row__label">out</span>
                      <span className="io-row__val"><code>{v}</code></span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* === The pipeline overview SVG (12 stations) === */
function PipelineDiagram({ active }) {
  const W = 1080;
  const H = 240;
  const stationW = 78;
  const stationH = 56;
  const gap = (W - stationW * STEPS.length - 60) / (STEPS.length - 1);
  const ystation = 100;

  const xFor = (i) => 30 + i * (stationW + gap);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="diagram" style={{ maxHeight: 280 }} aria-hidden="true">
      <ArrowDefs id="pl" />

      <text x="30" y="22" className="d-faint">CANONICAL PATH · CONSERVATOR-FIRST</text>
      <line x1="30" y1="32" x2={W - 30} y2="32" className="d-rule" />

      {/* Flow line behind boxes */}
      <line x1={xFor(0) + stationW} y1={ystation + stationH / 2} x2={xFor(STEPS.length - 1)} y2={ystation + stationH / 2} className="d-rule" />

      {/* Stations */}
      {STEPS.map((s, i) => {
        const x = xFor(i);
        const isActive = i === active;
        const isPast = i < active;
        const voiceColor = s.voice
          ? { gen: 'var(--gen)', ctl: 'var(--ctl)', con: 'var(--con)' }[s.voice]
          : null;
        const voiceSoft = s.voice
          ? { gen: 'var(--gen-soft)', ctl: 'var(--ctl-soft)', con: 'var(--con-soft)' }[s.voice]
          : null;

        return (
          <g key={s.id}>
            <rect
              x={x}
              y={ystation}
              width={stationW}
              height={stationH}
              rx="3"
              fill={isActive ? 'var(--ink)' : (voiceSoft || 'var(--paper)')}
              stroke={isActive ? 'var(--ink)' : (voiceColor || 'var(--rule-2)')}
              strokeWidth={isActive ? 1.5 : 1}
              opacity={isPast ? 0.92 : 1}
              style={{ transition: 'all 0.3s' }}
            />
            <text
              x={x + 8}
              y={ystation + 14}
              className="d-faint"
              style={{ fill: isActive ? 'var(--paper)' : 'var(--ink-3)', fontSize: 8 }}
            >
              STEP {s.id}
            </text>
            <text
              x={x + 8}
              y={ystation + 34}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                fontWeight: 500,
                fill: isActive ? 'var(--paper)' : 'var(--ink)',
              }}
            >
              {s.name}
            </text>
            {s.voice && (
              <circle
                cx={x + stationW - 10}
                cy={ystation + 10}
                r="5"
                fill={isActive ? 'var(--paper)' : voiceColor}
              />
            )}
            {isActive && (
              <g>
                <circle cx={x + stationW / 2} cy={ystation + stationH + 14} r="3" fill="var(--ink)" />
                <text x={x + stationW / 2} y={ystation + stationH + 30} textAnchor="middle" className="d-faint" style={{ fontSize: 8 }}>
                  NOW
                </text>
              </g>
            )}
          </g>
        );
      })}
    </svg>
  );
}

window.PipelineSection = PipelineSection;
