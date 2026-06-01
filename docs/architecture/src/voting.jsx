/* voting.jsx — live aggregation calculator */

const PRESETS = {
  safe:   { g: 0.80, c: 0.90, k: 0.30, label: 'A — safe' },
  medium: { g: 0.90, c: 0.80, k: 0.60, label: 'B — medium' },
  risky:  { g: 0.85, c: 0.85, k: 0.85, label: 'C — risky' },
};

const SCHEMES = [
  {
    id: 'majority',
    name: 'majority',
    sub: 'mean of all three voices, no risk flip (treats risk as utility)',
    veto: false,
  },
  {
    id: 'override',
    name: 'conservative_override',
    sub: 'weighted mean with safety = 1 − k · Conservator holds veto at k > 0.8',
    veto: true,
    isDefault: true,
  },
  {
    id: 'risk_adj',
    name: 'risk_adjusted_utility',
    sub: 'mean(g, c, 1−k) with sigmoid penalty centered at k = 0.5 · no hard veto',
    veto: false,
  },
];

function compute({ g, c, k }, schemeId) {
  switch (schemeId) {
    case 'majority':
      return { value: (g + c + k) / 3, veto: false };
    case 'override': {
      if (k > 0.8) return { value: null, veto: true };
      const safety = 1 - k;
      return { value: (g + c + safety) / 3, veto: false };
    }
    case 'risk_adj': {
      const baseUtil = (g + c + (1 - k)) / 3;
      const penalty = 1 / (1 + Math.exp(-(k - 0.5) / 0.1));
      return { value: baseUtil * (1 - penalty), veto: false };
    }
    default:
      return { value: 0, veto: false };
  }
}

function VotingSection() {
  const [candidate, setCandidate] = React.useState({ g: 0.85, c: 0.85, k: 0.5 });
  const [activePreset, setActivePreset] = React.useState(null);

  const setVal = (key, val) => {
    setCandidate((c) => ({ ...c, [key]: val }));
    setActivePreset(null);
  };

  const loadPreset = (id) => {
    const p = PRESETS[id];
    setCandidate({ g: p.g, c: p.c, k: p.k });
    setActivePreset(id);
  };

  const results = SCHEMES.map((s) => ({ ...s, result: compute(candidate, s.id) }));

  return (
    <section className="section" id="voting">
      <div className="container">
        <SectionHead
          num="06"
          eyebrow="Aggregation"
          title="Three schemes. Same scores. Different winners."
          lede="The voices produce three numbers. How you combine them is the political question. Drag the sliders or pick a preset — watch the schemes disagree."
        />

        <div className="tldr">
          <span className="tldr__label">In plain words</span>
          <div>
            <p>Three voices vote. The default scheme flips the Conservator's risk score into a <strong>safety</strong> score before averaging, then lets the Conservator veto anything genuinely dangerous. The other two schemes either ignore risk or smooth it with a sigmoid.</p>
          </div>
        </div>

        <div className="voting">
          <div className="voting__controls">
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--ink-3)', marginBottom: 18 }}>
              Voice scores · candidate
            </div>

            <div className="slider-group">
              <div className="slider-group__head">
                <span className="slider-group__name"><VToken v="gen">Generator</VToken> · utility</span>
                <span className="slider-group__val">{candidate.g.toFixed(2)}</span>
              </div>
              <input type="range" min="0" max="1" step="0.01" value={candidate.g} onChange={(e) => setVal('g', parseFloat(e.target.value))} className="slider slider--gen" />
              <div className="slider-group__hint">how well it solves the problem (higher = better)</div>
            </div>

            <div className="slider-group">
              <div className="slider-group__head">
                <span className="slider-group__name"><VToken v="ctl">Control</VToken> · correctness</span>
                <span className="slider-group__val">{candidate.c.toFixed(2)}</span>
              </div>
              <input type="range" min="0" max="1" step="0.01" value={candidate.c} onChange={(e) => setVal('c', parseFloat(e.target.value))} className="slider slider--ctl" />
              <div className="slider-group__hint">type / logic / test correctness (higher = better)</div>
            </div>

            <div className="slider-group">
              <div className="slider-group__head">
                <span className="slider-group__name"><VToken v="con">Conservator</VToken> · risk</span>
                <span className="slider-group__val">{candidate.k.toFixed(2)}</span>
              </div>
              <input type="range" min="0" max="1" step="0.01" value={candidate.k} onChange={(e) => setVal('k', parseFloat(e.target.value))} className="slider slider--con" />
              <div className="slider-group__hint">risk score (higher = MORE risk · veto at &gt; 0.80)</div>
            </div>

            <div style={{ marginTop: 18, paddingTop: 18, borderTop: '1px solid var(--rule)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--ink-3)', marginBottom: 8 }}>
                presets — original page example
              </div>
              <div className="scheme-presets">
                {Object.entries(PRESETS).map(([id, p]) => (
                  <button key={id} className="preset-chip" data-active={activePreset === id} onClick={() => loadPreset(id)}>
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="voting__results">
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--ink-3)', marginBottom: 18 }}>
              Aggregated score per scheme
            </div>

            {results.map((s) => {
              const r = s.result;
              return (
                <div key={s.id} className="scheme-row">
                  <div className="scheme-row__name">
                    {s.name}{s.isDefault && <span style={{ color: 'var(--ink-3)', fontSize: 10, marginLeft: 6 }}>· DEFAULT</span>}
                    <small>{s.sub}</small>
                  </div>
                  <div className="scheme-row__bar">
                    {r.veto ? (
                      <div className="scheme-row__bar-fill scheme-row__bar-fill--veto" style={{ width: '100%' }} />
                    ) : (
                      <div className="scheme-row__bar-fill" style={{ width: `${Math.max(0, Math.min(1, r.value)) * 100}%` }} />
                    )}
                  </div>
                  <div className={r.veto ? 'scheme-row__val scheme-row__val--veto' : 'scheme-row__val'}>
                    {r.veto ? 'VETO' : r.value.toFixed(3)}
                  </div>
                </div>
              );
            })}

            <div className="note" style={{ marginTop: 24 }}>
              <span className="note__label">Why the default is conservative_override</span>
              <span>
                The naive <code>majority</code> scheme treats the Conservator score as utility — higher = better — which picks the <em>riskier</em> candidate. Only the schemes that flip risk into safety (<code>1 − k</code>), i.e. <code>conservative_override</code> and <code>risk_adjusted_utility</code>, give the intuitive verdict.
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

window.VotingSection = VotingSection;
