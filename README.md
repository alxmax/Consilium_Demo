# Max Agent

Pattern de deliberare multi-perspectivă pentru evaluarea modificărilor de cod. Skill pentru Claude Code (identifier: `max-agent`) care folosește trei voci independente:

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
git clone https://github.com/alxmax/Max_Skill.git ~/dev/max-agent
mkdir -p ~/.claude/skills
ln -s ~/dev/max-agent ~/.claude/skills/max-agent
```

### Windows (PowerShell)

Junction (recomandat — nu cere admin):

```powershell
git clone https://github.com/alxmax/Max_Skill.git $HOME\dev\max-agent
New-Item -ItemType Directory -Force -Path $HOME\.claude\skills
New-Item -ItemType Junction -Path $HOME\.claude\skills\max-agent -Target $HOME\dev\max-agent
```

Sau symlink (PowerShell ca Administrator):

```powershell
New-Item -ItemType SymbolicLink -Path $HOME\.claude\skills\max-agent -Target $HOME\dev\max-agent
```

## Verifică instalarea

```bash
ls -la ~/.claude/skills/max-agent/SKILL.md
```

Apoi în Claude Code (sesiune nouă): `Review the last commit using the max-agent skill`.

## Structură

```
max-agent/
├── SKILL.md             # YAML frontmatter + workflow
├── README.md
├── FEEDBACK.md          # jurnal manual de uz real
├── .gitignore
├── scripts/
│   ├── personalities.py # rejection sampling (G, C, K)
│   ├── aggregator.py    # voting schemes
│   └── feedback.py      # stats pe FEEDBACK.md + runs/
├── prompts/
│   ├── generator.md     # prompt creativ
│   ├── control.md       # prompt analitic
│   └── conservator.md   # prompt skeptic
├── runs/                # JSON-uri per deliberare (gitignored)
└── examples/
    └── pr_review_example.md
```

## Utilizare

Skill-ul se activează automat când keywords precum "review PR", "evaluate change", "refactor planning", "risk assessment" apar în prompt.

Output: JSON cu `recommended`, `alternatives`, `voice_scores`, `confidence`, `deliberation_log`.

Pentru feedback loop și calibrare după uz real, vezi secțiunea **Feedback loop** din `SKILL.md`.
