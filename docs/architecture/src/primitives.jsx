/* primitives.jsx — shared bits: voice tokens, SVG nodes, arrow defs */

const VOICES = {
  gen: { id: 'gen', letter: 'G', name: 'Generator', role: 'creative', color: 'var(--gen)' },
  ctl: { id: 'ctl', letter: 'C', name: 'Control', role: 'analytical', color: 'var(--ctl)' },
  con: { id: 'con', letter: 'K', name: 'Conservator', role: 'prudent', color: 'var(--con)' },
};

function VToken({ v, children }) {
  const cls = `vtoken vtoken--${v}`;
  const name = children || VOICES[v].name;
  return (
    <span className={cls}>
      <span className="vtoken__bullet" />
      {name}
    </span>
  );
}

/* === SVG arrow marker defs — drop into <defs> once per SVG === */
function ArrowDefs({ id = 'arrow' }) {
  return (
    <defs>
      <marker id={`${id}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" fill="var(--ink)" />
      </marker>
      <marker id={`${id}-faint`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" fill="var(--ink-3)" />
      </marker>
      <marker id={`${id}-gen`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" fill="var(--gen)" />
      </marker>
      <marker id={`${id}-ctl`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" fill="var(--ctl)" />
      </marker>
      <marker id={`${id}-con`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" fill="var(--con)" />
      </marker>
    </defs>
  );
}

/* Voice node — letter in colored chip. cx,cy is center. */
function VoiceNode({ v, cx, cy, r = 18, label }) {
  const colorMap = {
    gen: { soft: 'var(--gen-soft)', ink: 'var(--gen-ink)', stroke: 'var(--gen)' },
    ctl: { soft: 'var(--ctl-soft)', ink: 'var(--ctl-ink)', stroke: 'var(--ctl)' },
    con: { soft: 'var(--con-soft)', ink: 'var(--con-ink)', stroke: 'var(--con)' },
  };
  const c = colorMap[v];
  return (
    <g>
      <circle cx={cx} cy={cy} r={r} fill={c.soft} stroke={c.stroke} strokeWidth="1.2" />
      <text x={cx} y={cy + 4} textAnchor="middle" fontFamily="var(--font-mono)" fontWeight="600" fontSize="13" fill={c.ink}>
        {VOICES[v].letter}
      </text>
      {label && (
        <text x={cx} y={cy + r + 14} textAnchor="middle" className="d-label">
          {label}
        </text>
      )}
    </g>
  );
}

/* Box node with title + optional subtitle */
function BoxNode({ x, y, w, h, title, sub, isolated, fill, stroke }) {
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={w}
        height={h}
        rx="3"
        className={isolated ? 'd-box d-box--isolated' : 'd-box'}
        style={fill ? { fill, stroke: stroke || 'var(--rule-2)' } : undefined}
      />
      {title && (
        <text x={x + w / 2} y={y + h / 2 + (sub ? -4 : 4)} textAnchor="middle" className="d-title">
          {title}
        </text>
      )}
      {sub && (
        <text x={x + w / 2} y={y + h / 2 + 12} textAnchor="middle" className="d-faint">
          {sub}
        </text>
      )}
    </g>
  );
}

/* Section frame — eyebrow + title + lede in one component */
function SectionHead({ num, eyebrow, title, lede, children }) {
  return (
    <header style={{ marginBottom: 28 }}>
      {num && <div className="divider-num"><span className="divider-num__id">{num}</span> <span style={{ color: 'var(--ink-3)' }}>·</span> {eyebrow}</div>}
      {!num && eyebrow && <p className="eyebrow">{eyebrow}</p>}
      <h2 className="h-section">{title}</h2>
      {lede && <p className="lede">{lede}</p>}
      {children}
    </header>
  );
}

Object.assign(window, {
  VOICES,
  VToken,
  ArrowDefs,
  VoiceNode,
  BoxNode,
  SectionHead,
});
