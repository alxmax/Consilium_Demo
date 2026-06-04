/* voices.jsx — four voices, Conservator first (v2) */

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
