/* trias.jsx — Trias deep-dive (ROUND2 weights) + lens heatmap + lazy routing */

const LENSES = [
  {
    name: 'Pioneer',
    tag: 'bold',
    model: 'Sonnet',
    g: 0.49, c: 0.30, k: 0.21,
    desc: 'Values bold, high-reward approaches that push the codebase forward. Tolerates moderate risk for genuinely new solutions. Prefers new patterns over existing ones when the new pattern offers a clear gain.',
  },
  {
    name: 'Architect',
    tag: 'structural',
    model: 'Sonnet',
    g: 0.30, c: 0.40, k: 0.30,
    desc: 'Values internal consistency, type safety, clean abstractions. Long-term maintainability over short-term wins. Prefers changes that strengthen invariants over those that work around them.',
  },
  {
    name: 'Steward',
    tag: 'protective',
    model: 'Sonnet',
    g: 0.30, c: 0.30, k: 0.40,
    desc: 'Values reversibility, minimal scope, and protection of systems that already work. Prefers existing patterns over novel ones unless the new is clearly necessary. Blast radius is the dominant concern.',
  },
];

const TRIAS_OUTCOMES = [
  { p: '3–0', label: 'Unanimous', desc: 'All three personalities picked the same candidate. Strongest signal possible.', conf: 0.95, outcome: 'OK auto' },
  { p: '2–1', label: 'Majority + dissent', desc: 'Two personalities agree on a candidate; the third picks a different one. Dissent is logged. The majority wins.', conf: 0.75, outcome: 'OK auto' },
  { p: '2–0', label: 'Majority + abstention', desc: 'Two personalities agree. The third had no valid choice — Conservator vetoed all its candidates (chose=null). The majority still elects a winner.', conf: 0.70, outcome: 'OK auto' },
  { p: '1–1–1', label: 'Fragmented', desc: 'Each personality picked a different candidate — no consensus. Escalates to a second deliberation round with peer context (B2 cascade).', conf: null, outcome: 'Round 2 → Skeptic → PEND' },
  { p: '1–1–0', label: 'Split + abstention', desc: 'Two different candidates got one vote each; one personality was vetoed out. No majority — goes to PEND for human decision.', conf: null, outcome: 'PEND' },
  { p: '1–0–0', label: 'Lone vote + 2 abstentions', desc: 'Only one personality produced a valid choice; the other two were vetoed. Insufficient agreement to auto-proceed.', conf: null, outcome: 'PEND' },
  { p: '0–0–0', label: 'Total veto', desc: 'All three personalities had every candidate vetoed by Conservator risk. No winner possible — escalates to B2 cascade, then PEND.', conf: null, outcome: 'Round 2 → PEND' },
];

function TriasSection() {
  return (
    <section className="section" id="trias">
      <div className="container">
        <SectionHead
          num="08"
          eyebrow="Trias — deep dive"
          title="Three personalities, one verdict."
          lede="Same three voices, but each personality biases them differently. The orchestrator dispatches three isolated sub-agents, then runs a democratic vote on their three chosen answers."
        />

        <div className="tldr">
          <span className="tldr__label">In plain words</span>
          <div>
            <p>Three Claudes each run the full pipeline — one is told to be bold, one structural, one cautious. All three run on <strong>Sonnet</strong> — divergence comes purely from the lens re-weighting (Pioneer up-weights Generator, Steward up-weights Conservator, Architect balances). Empirical baseline: ≈52% non-unanimity at n=25. They each pick a winner. A majority vote of the three picks the final answer. If they fragment 1-1-1, escalate.</p>
          </div>
        </div>

        <div className="trias-personalities">
          {LENSES.map((l) => (
            <PersonaCard key={l.name} {...l} />
          ))}
        </div>

        <h3 className="h-sub" style={{ marginTop: 8 }}>Lens weights — heatmap</h3>
        <p className="body-prose" style={{ color: 'var(--ink-2)', marginBottom: 16 }}>
          Each row sums to 1.0. The darker the cell, the heavier that lens leans on that voice.
        </p>
        <LensHeatmap lenses={LENSES} />

        <h3 className="h-sub" style={{ marginTop: 40 }}>Cost-aware routing — when Trias auto-downgrades</h3>
        <p className="body-prose" style={{ color: 'var(--ink-2)', marginBottom: 22 }}>
          Trias costs 2.67× Sequential. To avoid overspending on changes that don't need three perspectives, the orchestrator auto-downgrades based on risk (magnitude): <strong>low / medium → Sequential</strong> (1×), <strong>high → Dialectic</strong> (1.33×), <strong>critical</strong> (blocklist hit: auth, security, migrations, CI, secrets) → <strong>full Trias</strong> (2.67×). Each tier buys proportionally more scrutiny. You can override with an explicit <code>--trias</code> flag.
        </p>

        <LazyRoutingDiagram />

        <h3 className="h-sub" style={{ marginTop: 40 }}>Vote outcomes</h3>
        <p className="body-prose" style={{ color: 'var(--ink-2)', marginBottom: 24 }}>
          Each personality casts one vote. Below: every possible pattern, the confidence it produces, and what happens next.
        </p>

        <Collapsible label="Show all vote patterns" defaultOpen={true}>
          <VoteOutcomesTable rows={TRIAS_OUTCOMES} />
        </Collapsible>

        <div className="note" style={{ marginTop: 28 }}>
          <span className="note__label">Deadlock cascade — 1-1-1 / 0-0-0</span>
          <span>
            A true tie doesn't resolve to a "senior" personality — it escalates. <strong>Round 2</strong> re-dispatches all three personalities (+3 sub-agents), each now seeing the other two's Round-1 pick and reasoning. If they still split 1-1-1, a single <strong>Skeptic</strong> tiebreaker (+1 sub-agent) selects the winner; <code>0-0-0</code> — everyone vetoed everything — falls straight through to <strong>PEND</strong>. That path is the worst-case cost of <strong>7 sub-agents</strong> (3 + Round 2's 3 + 1 Skeptic). In practice it is rare: <strong>4 of 37</strong> Trias runs reached a 1-1-1 deadlock (≈11%), and ≈51% were non-unanimous — measured by <code>scripts/vote_degeneracy.py</code>.
          </span>
        </div>

        <div className="note" style={{ marginTop: 16 }}>
          <span className="note__label">Aggregate bias</span>
          <span>
            Mean weights across the three personalities: <VToken v="gen">Generator 0.363</VToken>, <VToken v="ctl">Control 0.333</VToken>, <VToken v="con">Conservator 0.303</VToken>. Compared to a balanced 0.333, the team tilts <strong>slightly toward exploration</strong>. Trias costs 2.67× Sequential — use only when the cost of a wrong decision dominates the cost of running 4 sub-agents (3 personalities + 1 post-vote Skeptic).
          </span>
        </div>
      </div>
    </section>
  );
}

function PersonaCard({ name, tag, model, g, c, k, desc }) {
  return (
    <article className="persona">
      <h3 className="persona__name">{name}</h3>
      <div className="persona__lean">{tag}-leaning{model && <> · runs on <strong>{model}</strong></>}</div>
      <div className="persona__bars">
        <PersonaBar v="gen" label="Generator" w={g} />
        <PersonaBar v="ctl" label="Control" w={c} />
        <PersonaBar v="con" label="Conservator" w={k} />
      </div>
      <p className="persona__pull">{desc}</p>
    </article>
  );
}

function PersonaBar({ v, label, w }) {
  return (
    <div className="persona-bar">
      <span>{label}</span>
      <div className="persona-bar__track">
        <div className={`persona-bar__fill persona-bar__fill--${v}`} style={{ width: `${w * 100}%`, transition: 'width 0.6s cubic-bezier(0.4, 0, 0.2, 1)' }} />
      </div>
      <span style={{ textAlign: 'right' }}>{w.toFixed(2)}</span>
    </div>
  );
}

function LensHeatmap({ lenses }) {
  const colors = {
    gen: 'oklch(0.66 0.13 55)',
    ctl: 'oklch(0.62 0.13 245)',
    con: 'oklch(0.62 0.18 25)',
  };

  return (
    <div className="lens-heatmap">
      <div className="lens-heatmap__row lens-heatmap__row--head">
        <div className="lens-heatmap__cell lens-heatmap__cell--head">Lens / Voice</div>
        <div className="lens-heatmap__cell">Generator</div>
        <div className="lens-heatmap__cell">Control</div>
        <div className="lens-heatmap__cell">Conservator</div>
      </div>
      {lenses.map((l) => (
        <div key={l.name} className="lens-heatmap__row">
          <div className="lens-heatmap__cell lens-heatmap__cell--head">{l.name}</div>
          <HeatCell w={l.g} color={colors.gen} />
          <HeatCell w={l.c} color={colors.ctl} />
          <HeatCell w={l.k} color={colors.con} />
        </div>
      ))}
    </div>
  );
}

function HeatCell({ w, color }) {
  // intensity: 0.2 → 0.5 weight maps to ~0.12 → 0.94 alpha (floor 0.12)
  const alpha = Math.max(0.12, Math.min(1, (w - 0.18) / 0.34));
  return (
    <div className="lens-heatmap__cell">
      <div
        className="lens-heatmap__weight"
        style={{
          background: `color-mix(in oklch, ${color} ${(alpha * 100).toFixed(0)}%, transparent)`,
          color: alpha > 0.55 ? 'var(--paper)' : 'var(--ink)',
        }}
      >
        {w.toFixed(2)}
      </div>
    </div>
  );
}

/* === Lazy routing decision diagram === */
function LazyRoutingDiagram() {
  return (
    <div style={{
      background: 'var(--paper)',
      border: '1px solid var(--rule)',
      borderRadius: 4,
      padding: '32px 28px 24px',
      marginBottom: 32,
    }}>
      <svg viewBox="0 0 880 360" className="diagram" aria-label="Cost-aware routing decision flow">
        <defs>
          <marker id="lr-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10z" fill="var(--ink)" />
          </marker>
          <marker id="lr-arrow-faint" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10z" fill="var(--ink-3)" />
          </marker>
        </defs>

        {/* Entry */}
        <g>
          <rect x="20" y="148" width="120" height="64" rx="4" fill="var(--paper-2)" stroke="var(--rule-2)" />
          <text x="80" y="178" textAnchor="middle" style={{ fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 500, fill: 'var(--ink)' }}>change arrives</text>
          <text x="80" y="194" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--ink-3)' }}>diff + context</text>
        </g>

        {/* Optional user override branch */}
        <g>
          <rect x="20" y="40" width="120" height="56" rx="4" fill="var(--paper)" stroke="var(--rule-2)" strokeDasharray="4 3" />
          <text x="80" y="64" textAnchor="middle" style={{ fontFamily: 'var(--font-sans)', fontSize: 12, fontWeight: 500, fill: 'var(--ink)' }}>user flag</text>
          <text x="80" y="80" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fill: 'var(--signal)' }}>--trias</text>
        </g>
        <path d="M 140 68 C 200 68, 280 68, 460 68 L 660 68" stroke="var(--ink-3)" strokeWidth="1.4" strokeDasharray="3 4" fill="none" markerEnd="url(#lr-arrow-faint)" />
        <text x="380" y="58" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--ink-3)' }}>bypass gate</text>

        {/* Decision diamond */}
        <g>
          <polygon
            points="260,180 360,140 460,180 360,220"
            fill="color-mix(in oklch, var(--signal) 10%, var(--paper))"
            stroke="var(--signal)"
            strokeWidth="1.5"
          />
          <text x="360" y="174" textAnchor="middle" style={{ fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 600, fill: 'var(--ink)' }}>scope_gate.py</text>
          <text x="360" y="192" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--ink-2)' }}>magnitude?</text>
        </g>

        {/* Entry → diamond */}
        <line x1="140" y1="180" x2="260" y2="180" stroke="var(--ink)" strokeWidth="1.5" markerEnd="url(#lr-arrow)" />

        {/* Diamond → high (top right) */}
        <path d="M 410 152 C 460 130, 540 100, 660 80" stroke="var(--ink)" strokeWidth="1.5" fill="none" markerEnd="url(#lr-arrow)" />
        <text x="540" y="118" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fill: 'var(--ink-2)' }}>critical</text>

        {/* Diamond → high (mid right) */}
        <line x1="460" y1="180" x2="660" y2="180" stroke="var(--ink)" strokeWidth="1.5" markerEnd="url(#lr-arrow)" />
        <text x="540" y="170" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fill: 'var(--ink-2)' }}>high</text>
        <text x="540" y="195" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: 'var(--ink-3)' }}>auto-downgrade</text>

        {/* Diamond → low/medium (bottom right) */}
        <path d="M 410 208 C 460 240, 540 280, 660 280" stroke="var(--ink)" strokeWidth="1.5" fill="none" markerEnd="url(#lr-arrow)" />
        <text x="540" y="240" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fill: 'var(--ink-2)' }}>low · medium</text>
        <text x="540" y="254" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 9, fill: 'var(--ink-3)' }}>auto-downgrade</text>

        {/* OUTCOMES — right column */}
        {/* Trias full */}
        <g>
          <rect x="660" y="40" width="200" height="68" rx="4"
            fill="color-mix(in oklch, oklch(0.55 0.16 320) 8%, var(--paper))"
            stroke="oklch(0.55 0.16 320)" strokeWidth="1.4" />
          <text x="760" y="64" textAnchor="middle" style={{ fontFamily: 'var(--font-sans)', fontSize: 14, fontWeight: 600, fill: 'var(--ink)' }}>Trias — full</text>
          <text x="760" y="82" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fill: 'oklch(0.4 0.16 320)' }}>4 sub-agents · 2.67× cost</text>
          <text x="760" y="97" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--ink-3)' }}>3 personalities + 1 post-vote Skeptic</text>
        </g>

        {/* Dialectic */}
        <g>
          <rect x="660" y="146" width="200" height="68" rx="4"
            fill="var(--ctl-soft)" stroke="var(--ctl)" strokeWidth="1.4" />
          <text x="760" y="170" textAnchor="middle" style={{ fontFamily: 'var(--font-sans)', fontSize: 14, fontWeight: 600, fill: 'var(--ink)' }}>Dialectic</text>
          <text x="760" y="188" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fill: 'var(--ctl-ink)' }}>seq + 1 Skeptic · 1.33×</text>
          <text x="760" y="203" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--ink-3)' }}>notification emitted</text>
        </g>

        {/* Sequential */}
        <g>
          <rect x="660" y="252" width="200" height="56" rx="4"
            fill="var(--con-soft)" stroke="var(--con)" strokeWidth="1.4" />
          <text x="760" y="274" textAnchor="middle" style={{ fontFamily: 'var(--font-sans)', fontSize: 14, fontWeight: 600, fill: 'var(--ink)' }}>Sequential</text>
          <text x="760" y="291" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fill: 'var(--ink-3)' }}>3 voices in-context · 1×</text>
        </g>

        {/* Footer note */}
        <text x="440" y="342" textAnchor="middle" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fill: 'var(--ink-3)' }}>
          override hierarchy:&nbsp;&nbsp;user --trias  &gt;  magnitude gate  &gt;  trivial-skip
        </text>
      </svg>
    </div>
  );
}

function VoteOutcomesTable({ rows }) {
  return (
    <div style={{ border: '1px solid var(--rule)', borderRadius: 4, overflow: 'hidden', background: 'var(--paper)' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '90px 1.6fr 80px 1.2fr', background: 'var(--paper-2)', borderBottom: '1px solid var(--rule)', padding: '12px 18px', fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--ink-3)' }}>
        <span>pattern</span>
        <span>meaning</span>
        <span>conf.</span>
        <span>outcome</span>
      </div>
      {rows.map((r, i) => (
        <div key={r.p} style={{ display: 'grid', gridTemplateColumns: '90px 1.6fr 80px 1.2fr', padding: '14px 18px', borderBottom: i === rows.length - 1 ? 0 : '1px solid var(--rule)', alignItems: 'center', fontSize: 14, gap: 14 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 500 }}>{r.p}</span>
          <span>
            <strong style={{ fontWeight: 500 }}>{r.label}</strong>
            <div style={{ color: 'var(--ink-2)', fontSize: 13, marginTop: 2 }}>{r.desc}</div>
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13 }}>{r.conf === null ? '—' : r.conf.toFixed(2)}</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: r.outcome.startsWith('PEND') ? 'oklch(0.55 0.18 25)' : 'var(--ink-2)' }}>{r.outcome}</span>
        </div>
      ))}
    </div>
  );
}

window.TriasSection = TriasSection;
