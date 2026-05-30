/* efficiency-section.jsx — Usage & Efficiency section */

const MODES_DATA = [
  { mode: 'sequential',  costMultiplier: '1×',    usd: '~$0.11', dispatches: 0,  note: 'in-context baseline · measured' },
  { mode: 'dialectic',   costMultiplier: '1.33×', usd: '~$0.15', dispatches: 1,  note: '+ 1 skeptic sub-agent' },
  { mode: 'trias',       costMultiplier: '3×',    usd: '~$0.33', dispatches: 3,  note: '3 personality sub-agents (9 voice runs)' },
  { mode: 'skeptic_on_chosen', costMultiplier: 'base +1', usd: '+~$0.04', dispatches: 1, note: 'composable flag over any base' },
];

function BarChart({ data }) {
  const max = Math.max(...data.map(d => d.value));
  const colors = {
    sequential: 'var(--gen)',
    dialectic:  'var(--ctl)',
    trias:      'oklch(0.55 0.18 260)',
    parallel:   'var(--con)',
  };
  return (
    <svg viewBox={`0 0 640 ${data.length * 64 + 20}`} className="diagram" style={{ maxHeight: 360 }}>
      {data.map((d, i) => {
        const barW = max > 0 ? (d.value / max) * 420 : 0;
        const y = i * 64 + 10;
        const col = colors[d.mode] || 'var(--ink-2)';
        return (
          <g key={d.mode}>
            <text x="0" y={y + 16} style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fill: 'var(--ink)' }}>{d.mode}</text>
            <text x="0" y={y + 32} style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--ctl-ink)' }}>{d.model}</text>
            <rect x="160" y={y + 6} width={barW} height={28} rx="3" fill={col} opacity="0.8" />
            <text x={160 + barW + 8} y={y + 24} style={{ fontSize: 12, fill: 'var(--ink-2)', fontFamily: 'var(--font-mono)' }}>
              {d.label}
            </text>
          </g>
        );
      })}
      <text x="0" y={data.length * 64 + 16} style={{ fontSize: 11, fill: 'var(--ink-3)', fontVariantNumeric: 'tabular-nums' }}>
        measured tokens / voice dispatch · lower = cheaper per voice call
      </text>
    </svg>
  );
}

function ModeRow({ mode, costMultiplier, usd, dispatches, note }) {
  return (
    <tr>
      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, padding: '10px 16px 10px 0', borderBottom: '1px solid var(--rule)' }}>{mode}</td>
      <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--rule)', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{costMultiplier}</td>
      <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--rule)', textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--ctl-ink)' }}>{usd}</td>
      <td style={{ padding: '10px 16px', borderBottom: '1px solid var(--rule)', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{dispatches}</td>
      <td style={{ padding: '10px 16px 10px 0', borderBottom: '1px solid var(--rule)', fontSize: 12, color: 'var(--ink-2)' }}>{note}</td>
    </tr>
  );
}

function EfficiencySection() {
  // Measured by scripts/efficiency.py over runs/*.json telemetry (2026-05-30).
  // tokens_per_dispatch is outcome-independent (no labelling needed), unlike
  // tokens_per_OK which is still gated on more confirmed-OK labels.
  const measured = [
    { mode: 'sequential', value: 1565, label: '1 565 tok · n=131', model: 'Sonnet 4.6' },
    { mode: 'dialectic',  value: 2313, label: '2 313 tok · n=20',  model: 'Sonnet 4.6' },
    { mode: 'trias',      value: 6346, label: '6 346 tok · n=37',  model: 'Sonnet 4.6' },
    { mode: 'parallel',   value: 5367, label: '5 367 tok · n=26',  model: 'Sonnet 4.6' },
  ];

  return (
    <section className="section" id="efficiency">
      <div className="container">
        <SectionHead
          num="12"
          eyebrow="Usage & Efficiency"
          title="How much does each mode actually cost?"
          lede="scripts/efficiency.py rolls up per-dispatch telemetry from every run. The chart below is a frozen snapshot of measured tokens-per-dispatch, captured 2026-05-30 — re-run the command in the panel below for current numbers. The stricter tokens_per_OK metric also exists but is held back until enough runs carry a confirmed OK/BAD label — honest measurement over a flattering one."
        />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32, marginTop: 32, alignItems: 'start' }}>
          <div>
            <h3 style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-2)', marginBottom: 4 }}>Mode cost multipliers</h3>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-3)', marginBottom: 16 }}>1× baseline = Sequential on Sonnet 4.6 · $/run ≈ multiplier × measured Sequential</p>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '6px 16px 6px 0', borderBottom: '2px solid var(--rule-2)', fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-2)' }}>Mode</th>
                  <th style={{ textAlign: 'right', padding: '6px 16px', borderBottom: '2px solid var(--rule-2)', fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-2)' }}>Cost</th>
                  <th style={{ textAlign: 'right', padding: '6px 16px', borderBottom: '2px solid var(--rule-2)', fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-2)' }}>$ / run</th>
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
            <h3 style={{ fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-2)', marginBottom: 4 }}>tokens / dispatch (measured)</h3>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-3)', marginBottom: 16 }}>frozen snapshot · <strong style={{ color: 'var(--ctl-ink)' }}>Sonnet 4.6</strong> · efficiency.py over runs/*.json · captured 2026-05-30</p>
            <BarChart data={measured} />
          </div>
        </div>

        <div style={{ marginTop: 32, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {[
            { role: 'Orchestrator', model: 'your session model', color: 'var(--con)', note: 'the main Claude Code session that runs the workflow and dispatches sub-agents — on whatever model you launched Claude Code with (Opus or Sonnet). The skill does not pin it; Opus gives the strongest orchestration.' },
            { role: 'Voices & sub-agents', model: 'Sonnet 4.6', color: 'var(--ctl)', note: 'Generator · Control · Conservator · Skeptic · Trias personalities — pinned to model: "sonnet"; they do not inherit the session model.' },
            { role: 'Override', model: '→ Opus', color: 'var(--gen)', note: 'an opt-in that bumps the Generator from its pinned Sonnet up to Opus for high-stakes / ambiguous changes.' },
          ].map((m) => (
            <div key={m.role} style={{ padding: '14px 16px', border: '1px solid var(--rule)', borderTop: `3px solid ${m.color}`, borderRadius: 4, background: 'var(--paper)' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-3)', marginBottom: 4 }}>{m.role}</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 15, fontWeight: 600, color: m.color, marginBottom: 6 }}>{m.model}</div>
              <p style={{ fontSize: 12, color: 'var(--ink-2)', lineHeight: 1.5, margin: 0 }}>{m.note}</p>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 20, padding: '20px 24px', background: 'var(--paper-2)', border: '1px solid var(--rule)', borderRadius: 4 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--ink-2)', marginBottom: 12 }}>Reproduce / live data</div>
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
            <li>This is cost <em>per dispatch</em>, not per run — total run cost ≈ dispatches × this, which the cost-multiplier column on the left captures (Sequential 1×, Trias 3×).</li>
            <li>`tokens_per_OK` (cost per confirmed-good outcome) is the stricter metric but is withheld until enough runs carry an OK/BAD label — most current runs are unlabeled, which would inflate it.</li>
            <li>Modes with fewer than 3 runs with telemetry show <code style={{ fontFamily: 'var(--font-mono)' }}>insufficient_data</code>.</li>
          </ul>
        </div>
      </div>
    </section>
  );
}

window.EfficiencySection = EfficiencySection;
