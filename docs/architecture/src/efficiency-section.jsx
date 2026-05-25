/* efficiency-section.jsx — Usage & Efficiency section */

const MODES_DATA = [
  { mode: 'sequential',  costMultiplier: '1×',    dispatches: 0,  note: 'in-context baseline' },
  { mode: 'dialectic',   costMultiplier: '1.33×', dispatches: 1,  note: '+ 1 skeptic sub-agent' },
  { mode: 'trias',       costMultiplier: '3×',    dispatches: 3,  note: '3 personality sub-agents (9 voice runs)' },
  { mode: 'skeptic_on_chosen', costMultiplier: 'base +1', dispatches: 1, note: 'composable flag over any base' },
];

function BarChart({ data }) {
  const max = Math.max(...data.map(d => d.value));
  const colors = {
    sequential: 'var(--gen)',
    dialectic:  'var(--ctl)',
    trias:      'oklch(0.55 0.18 260)',
  };
  return (
    <svg viewBox={`0 0 600 ${data.length * 60 + 20}`} className="diagram" style={{ maxHeight: 280 }}>
      {data.map((d, i) => {
        const barW = max > 0 ? (d.value / max) * 440 : 0;
        const y = i * 60 + 10;
        const col = colors[d.mode] || 'var(--ink-2)';
        return (
          <g key={d.mode}>
            <text x="0" y={y + 20} style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fill: 'var(--ink)' }}>{d.mode}</text>
            <rect x="140" y={y + 6} width={barW} height={28} rx="3" fill={col} opacity="0.8" />
            <text x={140 + barW + 8} y={y + 24} style={{ fontSize: 12, fill: 'var(--ink-2)', fontFamily: 'var(--font-mono)' }}>
              {d.label}
            </text>
          </g>
        );
      })}
      <text x="0" y={data.length * 60 + 18} style={{ fontSize: 11, fill: 'var(--ink-3)', fontVariantNumeric: 'tabular-nums' }}>
        lower tokens/OK = better efficiency
      </text>
    </svg>
  );
}

function ModeRow({ mode, costMultiplier, dispatches, note }) {
  return (
    <tr>
      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, padding: '10px 16px 10px 0', borderBottom: '1px solid var(--rule)' }}>{mode}</td>
      <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--rule)', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{costMultiplier}</td>
      <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--rule)', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{dispatches}</td>
      <td style={{ padding: '10px 16px 10px 0', borderBottom: '1px solid var(--rule)', fontSize: 12, color: 'var(--ink-2)' }}>{note}</td>
    </tr>
  );
}

function EfficiencySection() {
  const placeholder = [
    { mode: 'sequential', value: 3700,  label: '~3 700 tok/OK' },
    { mode: 'dialectic',  value: 5200,  label: '~5 200 tok/OK' },
    { mode: 'trias',      value: 11000, label: '~11 000 tok/OK' },
  ];

  return (
    <section className="section" id="efficiency">
      <div className="container">
        <SectionHead
          num="12"
          eyebrow="Usage & Efficiency"
          title="How much does each mode cost per good outcome?"
          lede="efficiency.py computes tokens_per_OK — total tokens divided by confirmed OK outcomes — so you can compare modes on real usage data, not just dispatch count."
        />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32, marginTop: 32, alignItems: 'start' }}>
          <div>
            <h3 style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-2)', marginBottom: 16 }}>Mode cost multipliers</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '6px 16px 6px 0', borderBottom: '2px solid var(--rule-2)', fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-2)' }}>Mode</th>
                  <th style={{ textAlign: 'right', padding: '6px 16px', borderBottom: '2px solid var(--rule-2)', fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-2)' }}>Cost</th>
                  <th style={{ textAlign: 'right', padding: '6px 16px', borderBottom: '2px solid var(--rule-2)', fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-2)' }}>Sub-agents</th>
                  <th style={{ textAlign: 'left', padding: '6px 0', borderBottom: '2px solid var(--rule-2)', fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-2)' }}>Note</th>
                </tr>
              </thead>
              <tbody>
                {MODES_DATA.map(m => <ModeRow key={m.mode} {...m} />)}
              </tbody>
            </table>
          </div>

          <div>
            <h3 style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-2)', marginBottom: 16 }}>tokens_per_OK (illustrative)</h3>
            <BarChart data={placeholder} />
          </div>
        </div>

        <div style={{ marginTop: 32, padding: '20px 24px', background: 'var(--paper-2)', border: '1px solid var(--rule)', borderRadius: 4 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-2)', marginBottom: 12 }}>Live data</div>
          <code style={{ display: 'block', fontSize: 12, fontFamily: 'var(--font-mono)', lineHeight: 1.8, color: 'var(--ink)' }}>
            python scripts/efficiency.py --by-mode<br />
            python scripts/efficiency.py --self-test<br />
            python scripts/efficiency.py --compare trias sequential --since 2026-05-01
          </code>
        </div>

        <div style={{ marginTop: 20, padding: '16px 24px', background: 'color-mix(in oklch, var(--con) 6%, var(--paper))', border: '1px solid color-mix(in oklch, var(--con) 20%, var(--rule))', borderRadius: 4 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--con)', marginBottom: 8 }}>Caveats</div>
          <ul style={{ fontSize: 12, color: 'var(--ink-2)', lineHeight: 1.7, paddingLeft: 20 }}>
            <li>Token estimates use chars/4 (±10–20% error band), consistent across modes.</li>
            <li>Cross-mode OK is not qualitatively comparable — a Trias OK represents deeper deliberation than a Sequential OK.</li>
            <li>Outcomes are subjective at log time; mark BAD retroactively via <code style={{ fontFamily: 'var(--font-mono)' }}>mark_outcome.py</code> if a choice later regressed.</li>
            <li>Modes with fewer than 3 runs with telemetry show <code style={{ fontFamily: 'var(--font-mono)' }}>insufficient_data</code>.</li>
          </ul>
        </div>
      </div>
    </section>
  );
}

window.EfficiencySection = EfficiencySection;
