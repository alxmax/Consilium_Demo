/* voices.jsx — four voices, Conservator first (v2) */

/* === One candidate's journey — step-through animation === */
/* Same play/pause/reset pattern as PipelineSection / ModesSection. */

const JOURNEY_STEPS = [
  {
    id: '1', name: 'arrive',
    caption: 'A risky diff arrives. The orchestrator restates it as one testable success_criterion before any voice runs.',
    payload: 'diff + success_criterion',
    focus: 'diff',
  },
  {
    id: '2', name: 'conservator',
    caption: 'Conservator reads it FIRST. It scores regression risk, decides how reversible the change is, and sets the tokens_budget every later voice must respect. It can raise irreversibility_flag and stop the pipeline here.',
    payload: '{ net_concern: 0.25, tokens_budget: 800 }',
    focus: 'con',
  },
  {
    id: '3', name: 'strip',
    caption: 'strip_context.py trims the handoff: Generator receives only magnitude, counterparty_risks and its budget — not Conservator\'s full reasoning. The cut is deliberate: it stops one voice\'s framing from anchoring the next.',
    payload: 'magnitude · counterparty_risks · budget',
    focus: 'strip1',
  },
  {
    id: '4', name: 'generator',
    caption: 'Generator proposes 3–5 genuinely different candidates — always including do_nothing as a baseline — and stays inside the budget Conservator set.',
    payload: 'candidates[4] · preferred',
    focus: 'gen',
  },
  {
    id: '5', name: 'strip',
    caption: 'Second strip: Control receives the candidates without Generator\'s rationale — it verdicts the code, not the sales pitch.',
    payload: 'candidates[] (rationale removed)',
    focus: 'strip2',
  },
  {
    id: '6', name: 'control',
    caption: 'Control verdicts each candidate in order: goal-fit → types → logic → tests → style, and writes concrete tests_to_write for every valid: true.',
    payload: 'verdicts[] · tests_to_write[]',
    focus: 'ctl',
  },
  {
    id: '7', name: 'aggregate',
    caption: 'The three scores combine: a weighted mean of generator + control + safety, where safety = 1 − conservator. The flip is because Conservator scores risk (high = bad) while the other two score utility (high = good). A risk score above 0.8 is a unilateral veto. The winner and its confidence land in the canonical report.',
    payload: 'chosen + confidence → runs/<ts>.json',
    focus: 'agg',
  },
];

function VoiceJourney() {
  const [active, setActive] = React.useState(0);
  const [playing, setPlaying] = React.useState(false);
  const timer = React.useRef(null);

  React.useEffect(() => {
    if (!playing) return;
    timer.current = setTimeout(() => {
      setActive((a) => {
        if (a >= JOURNEY_STEPS.length - 1) { setPlaying(false); return a; }
        return a + 1;
      });
    }, 2400);
    return () => clearTimeout(timer.current);
  }, [playing, active]);

  const step = JOURNEY_STEPS[active];

  return (
    <div style={{ margin: '40px 0 8px' }}>
      <h3 className="h-sub" style={{ marginBottom: 6 }}>One candidate's journey</h3>
      <p className="body-prose" style={{ color: 'var(--ink-2)', marginBottom: 16, maxWidth: 760 }}>
        Hit play and follow a single change through the default Sequential pipeline — who sees what, what gets stripped between voices, and where the scores meet.
      </p>

      <div className="pipeline__playhead" style={{ marginBottom: 14 }}>
        <button className="btn" onClick={() => { if (active >= JOURNEY_STEPS.length - 1) setActive(0); setPlaying(!playing); }}>
          {playing ? <>■ pause</> : <>▶ play</>}
        </button>
        <button className="btn btn--ghost" onClick={() => { setPlaying(false); setActive(0); }}>
          ⟲ reset
        </button>
        <span style={{ color: 'var(--ink-3)' }}>step {active + 1} of {JOURNEY_STEPS.length}</span>
      </div>

      <JourneyDiagram focus={step.focus} stepIndex={active} />

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, margin: '16px 0 12px' }}>
        {JOURNEY_STEPS.map((s, i) => (
          <button key={i} className="step-pill" data-active={i === active} onClick={() => { setPlaying(false); setActive(i); }}>
            <span className="step-pill__id">{s.id}</span>
            <span className="step-pill__name">{s.name}</span>
          </button>
        ))}
      </div>

      <div style={{ border: '1px solid var(--rule)', borderLeft: '3px solid var(--ink)', borderRadius: 4, background: 'var(--paper)', padding: '14px 18px', maxWidth: 860 }}>
        <p style={{ margin: 0, fontSize: 14.5, lineHeight: 1.6, color: 'var(--ink)' }}>{step.caption}</p>
        <div style={{ marginTop: 8, fontFamily: 'var(--font-mono)', fontSize: 11.5, color: 'var(--ink-3)' }}>
          <span style={{ textTransform: 'uppercase', letterSpacing: '0.08em' }}>carries · </span>
          <code>{step.payload}</code>
        </div>
      </div>
    </div>
  );
}

function JourneyDiagram({ focus, stepIndex }) {
  // x-positions of the packet per step (matches JOURNEY_STEPS order)
  const packetX = [60, 215, 330, 445, 560, 675, 810];
  const done = (i) => stepIndex > i;
  const nodeState = (key, i) => (focus === key ? 'active' : done(i) ? 'done' : 'idle');
  const op = (s) => (s === 'idle' ? 0.35 : 1);
  const stripFill = (key) => (focus === key ? 'var(--ink)' : 'var(--ink-3)');

  return (
    <svg viewBox="0 0 880 190" style={{ width: '100%', maxWidth: 880, display: 'block' }} aria-label="One candidate's journey through the three voices">
      <ArrowDefs id="vj-arrow" />

      {/* spine */}
      <line x1={95} y1={95} x2={770} y2={95} stroke="var(--rule-2)" strokeWidth="1" />

      {/* diff in */}
      <g opacity={op(nodeState('diff', 0))}>
        <BoxNode x={25} y={75} w={70} h={40} title="diff" sub="in" />
      </g>

      {/* Conservator */}
      <g opacity={op(nodeState('con', 1))}>
        <VoiceNode v="con" cx={215} cy={95} label="Conservator · first" />
      </g>

      {/* strip 1 */}
      <g opacity={focus === 'strip1' ? 1 : 0.45}>
        <rect x={322} y={87} width={16} height={16} transform="rotate(45 330 95)" fill="none" stroke={stripFill('strip1')} strokeWidth="1.4" />
        <text x={330} y={68} textAnchor="middle" className="d-faint" style={{ fontSize: 9.5 }}>strip</text>
      </g>

      {/* Generator */}
      <g opacity={op(nodeState('gen', 3))}>
        <VoiceNode v="gen" cx={445} cy={95} label="Generator" />
      </g>

      {/* strip 2 */}
      <g opacity={focus === 'strip2' ? 1 : 0.45}>
        <rect x={552} y={87} width={16} height={16} transform="rotate(45 560 95)" fill="none" stroke={stripFill('strip2')} strokeWidth="1.4" />
        <text x={560} y={68} textAnchor="middle" className="d-faint" style={{ fontSize: 9.5 }}>strip</text>
      </g>

      {/* Control */}
      <g opacity={op(nodeState('ctl', 5))}>
        <VoiceNode v="ctl" cx={675} cy={95} label="Control" />
      </g>

      {/* Aggregate */}
      <g opacity={op(nodeState('agg', 6))}>
        <BoxNode x={770} y={73} w={86} h={44} title="aggregate" sub="safety = 1 − k" />
      </g>

      {/* the travelling packet */}
      <circle cx={packetX[stepIndex]} cy={95} r={6} fill="var(--ink)" style={{ transition: 'cx 0.55s cubic-bezier(0.4, 0, 0.2, 1)' }} />
      <circle cx={packetX[stepIndex]} cy={95} r={11} fill="none" stroke="var(--ink)" strokeOpacity="0.25" style={{ transition: 'cx 0.55s cubic-bezier(0.4, 0, 0.2, 1)' }} />
    </svg>
  );
}

function VoicesSection() {
  return (
    <section className="section" id="voices">
      <div className="container">
        <SectionHead
          num="02"
          eyebrow="The voices"
          title="Three core voices, run in this order. Plus one focal challenger."
          lede="Conservator runs first — its risk read sets the token budget every other voice operates under. Generator proposes. Control verifies. A fourth voice, the Skeptic, gets focal access to the chosen answer only."
        />

        <WhyThreeVoices />

        <div className="voices-grid">
          <article className="voice-card voice-card--con">
            <div className="voice-card__head">
              <div>
                <h3 className="voice-card__name">Conservator</h3>
                <div className="voice-card__role">prudent · runs <em>first</em></div>
              </div>
              <div className="voice-card__badge voice-card__badge--pulse">K</div>
            </div>
            <p className="voice-card__mantra">"Reversibility over cleverness. Blast radius matters. Scope discipline."</p>
            <ul className="voice-card__list">
              <li>Reads the diff and scores risk along 4 dimensions</li>
              <li>Sets <code>tokens_budget</code> for Generator + Control — low risk allows verbose output; high risk tightens it to force concision</li>
              <li>Can raise <code>irreversibility_flag</code> and block the pipeline</li>
              <li>Scores risk; the aggregator applies a unilateral veto when <code>net_concern &gt; 0.8</code></li>
            </ul>
            <div className="voice-card__io">
              <div><span className="io-tag">in</span> diff + context</div>
              <div><span className="io-tag">out</span> {`{ regression_risk{ net_concern }, tokens_budget, meta_recommendation }`}</div>
            </div>
          </article>

          <article className="voice-card voice-card--gen">
            <div className="voice-card__head">
              <div>
                <h3 className="voice-card__name">Generator</h3>
                <div className="voice-card__role">creative · runs second</div>
              </div>
              <div className="voice-card__badge voice-card__badge--pulse">G</div>
            </div>
            <p className="voice-card__mantra">"Quantity before quality. No self-censorship. Always include do_nothing."</p>
            <ul className="voice-card__list">
              <li>Produces 3–5 candidate approaches</li>
              <li>Respects the Conservator's <code>tokens_budget.generator</code></li>
              <li>Includes a <code>do_nothing</code> baseline and a <code>preferred</code> pick</li>
            </ul>
            <div className="voice-card__io">
              <div><span className="io-tag">in</span> diff + tokens_budget</div>
              <div><span className="io-tag">out</span> {`{ candidates[], preferred, fallback }`}</div>
            </div>
          </article>

          <article className="voice-card voice-card--ctl">
            <div className="voice-card__head">
              <div>
                <h3 className="voice-card__name">Control</h3>
                <div className="voice-card__role">analytical · runs third</div>
              </div>
              <div className="voice-card__badge voice-card__badge--pulse">C</div>
            </div>
            <p className="voice-card__mantra">"Pedantic, not pessimistic. Verify, don't speculate. Concrete over abstract."</p>
            <ul className="voice-card__list">
              <li>Per-candidate: goal-fit → types → logic → tests → style</li>
              <li>Writes <code>tests_to_write</code> for every <code>valid:true</code></li>
              <li>Raises <code>disagreements</code> if it spots a substantive gap</li>
            </ul>
            <div className="voice-card__io">
              <div><span className="io-tag">in</span> candidates + Conservator output</div>
              <div><span className="io-tag">out</span> {`{ verdicts[], glossary, disagreements }`}</div>
            </div>
          </article>
        </div>

        <VoiceJourney />

        {/* Skeptic — the 4th voice, set apart */}
        <div className="skeptic-card">
          <div className="skeptic-card__rule" />
          <div className="skeptic-card__body">
            <div className="skeptic-card__head">
              <div className="skeptic-card__badge">S</div>
              <div>
                <h3 className="skeptic-card__name">Skeptic <span className="skeptic-card__sub">focal challenger · composable</span></h3>
                <p className="skeptic-card__mantra">"Show me the test that will fail when this is wrong."</p>
              </div>
            </div>
            <p className="skeptic-card__desc">
              Doesn't run by default. Composed on top of any base mode as <code>skeptic_on_chosen</code>. Auto-triggers when post-aggregation <code>confidence ∈ [0.0, 0.7]</code>. Sees <strong>only the chosen answer</strong> — never the other candidates, never the verdicts — and tries to find a concrete failure scenario: a missing test case, a crash on an edge input, a performance cliff. If it can't find one, <code>can_object: false</code>. Advisory by default; can change the chosen answer only with <code>--skeptic-can-override</code>.
            </p>
            <div className="skeptic-card__io">
              <div><span className="io-tag">in</span> chosen approach + context</div>
              <div><span className="io-tag">out</span> {`{ can_object, objection: { concrete_concerns[], failure_mode, addressable }, notes }`}</div>
              <div><span className="io-tag">mode</span> advisory by default · <code>--skeptic-can-override</code> for veto</div>
            </div>
          </div>
        </div>

        <div className="constitution">
          <div className="constitution__item">
            <div className="constitution__n">CONST · 1</div>
            <div className="constitution__t">Think before coding</div>
            <div className="constitution__b">Surface tradeoffs. Don't assume.</div>
          </div>
          <div className="constitution__item">
            <div className="constitution__n">CONST · 2</div>
            <div className="constitution__t">Simplicity first</div>
            <div className="constitution__b">Minimum code that solves the problem.</div>
          </div>
          <div className="constitution__item">
            <div className="constitution__n">CONST · 3</div>
            <div className="constitution__t">Surgical changes</div>
            <div className="constitution__b">Touch only what the goal demands.</div>
          </div>
          <div className="constitution__item">
            <div className="constitution__n">CONST · 4</div>
            <div className="constitution__t">Goal-driven</div>
            <div className="constitution__b">success_criterion + verification are mandatory.</div>
          </div>
        </div>
      </div>
    </section>
  );
}

window.VoicesSection = VoicesSection;
