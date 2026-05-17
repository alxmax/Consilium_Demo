# Consilium

Pattern de deliberare multi-perspectivă pentru evaluarea modificărilor de cod. Skill pentru Claude Code (identifier: `consilium`) care folosește trei voci independente:

- **Generator** (creativ) — propune alternative
- **Control** (analitic) — verifică corectitudine
- **Conservator** (prudent) — evaluează risc

## Când să folosești

- Review de PR sau diff
- Planning de refactor pe 2+ fișiere
- Decizie între mai multe abordări de implementare
- Înainte de commit pe cod shared/core
- Evaluare de risc pentru schimbări non-triviale

## Install

### Linux / macOS

```bash
git clone https://github.com/alxmax/Consilium.git ~/dev/consilium
mkdir -p ~/.claude/skills
ln -s ~/dev/consilium ~/.claude/skills/consilium
```

### Windows (PowerShell)

Junction (recomandat — nu cere admin):

```powershell
git clone https://github.com/alxmax/Consilium.git $HOME\dev\consilium
New-Item -ItemType Directory -Force -Path $HOME\.claude\skills
New-Item -ItemType Junction -Path $HOME\.claude\skills\consilium -Target $HOME\dev\consilium
```

Sau symlink (PowerShell ca Administrator):

```powershell
New-Item -ItemType SymbolicLink -Path $HOME\.claude\skills\consilium -Target $HOME\dev\consilium
```

## Verifică instalarea

```bash
ls -la ~/.claude/skills/consilium/SKILL.md
```

Apoi în Claude Code (sesiune nouă): `Review the last commit using the consilium skill`.

## Structură

```
consilium/
├── SKILL.md                 # contract: Constitution + workflow în 6 pași
├── README.md
├── FEEDBACK.html            # jurnal de uz real (gitignored)
├── prompts/
│   ├── voices/              # generator, control, conservator, skeptic,
│   │                        #   *_pass2, pioneer/architect/steward_lens,
│   │                        #   frontend_domain_lens
│   └── senators/            # wittgenstein, aurelius, confucius, socrate,
│                            #   musk, dimon, napoleon (Senate mode)
├── scripts/                 # ~30 scripts stdlib-only (aggregator, confidence,
│                            #   priors, scope_gate, dialectic_merge,
│                            #   senate_synth, log_feedback, …)
├── agents/
│   └── consilium-subagent.md  # dispatch izolat via Agent tool
├── runs/                    # un JSON per deliberare (gitignored)
│   └── senate/              # bundles Senate
├── docs/senate/             # architecture.html (vizualizări runde + blocaj)
├── experiments/             # benchmark-uri pe probleme reale
└── evals/                   # regression scenarios pentru scripts
```

## Utilizare

Skill-ul se activează automat când keywords precum "review PR", "evaluate change", "refactor planning", "risk assessment", "should I commit", "which approach" apar în prompt.

**Moduri disponibile** (vezi SKILL.md pentru workflow per mod):

- **Sequential** (default) — Conservator → Generator → Control single-context
- **Dialectic** — two-pass; Pass-2 vede output-ul celorlalte voci
- **Trias** — 3 personalități × 3 voci (Pioneer/Architect/Steward); 9 sub-agenți
- **`trias_split`** — Trias cu Sonnet Generator + Haiku verifiers
- **`parallel_skeptic`** / **`dialectic_skeptic`** — modul de bază + 1 voce focală Skeptic
- **`skeptic_on_chosen`** — flag composabil peste orice mod
- **Senate** — audit pe modificările skill-ului însuși (7 senatori, on-demand)

Parallel-ul ca opțiune selectabilă a fost retras în RUND2; rămâne ca auto cross-check când `magnitude=critical ∧ reversibility=irreversible`.

**Output canonic** (validat de `scripts/validate_report.py`): JSON cu `success_criterion`, `chosen_approach`, `verification`, `alternatives`, `voice_scores`, `confidence`, `deliberation_log`.

Pentru feedback loop și calibrare după uz real, vezi secțiunea **Feedback loop** din `SKILL.md`.

## License

[Business Source License 1.1](LICENSE) © 2026 Schipor Alexandru.

Free for non-commercial use (evaluation, education, research, personal use). Commercial use within an organization that generates revenue from products or services incorporating the Licensed Work requires a commercial license — contact the Licensor. License converts automatically to Apache 2.0 on **2030-05-16**.
