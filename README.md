# code-deliberation-skill

Pattern de deliberare multi-perspectivă pentru evaluarea modificărilor de cod. Skill pentru Claude Code care folosește trei voci independente:

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
git clone https://github.com/<user>/code-deliberation-skill.git ~/dev/code-deliberation-skill
mkdir -p ~/.claude/skills
ln -s ~/dev/code-deliberation-skill ~/.claude/skills/code-deliberation
```

### Windows (PowerShell ca Administrator)

```powershell
git clone https://github.com/<user>/code-deliberation-skill.git $HOME\dev\code-deliberation-skill
New-Item -ItemType Directory -Force -Path $HOME\.claude\skills
New-Item -ItemType SymbolicLink -Path $HOME\.claude\skills\code-deliberation -Target $HOME\dev\code-deliberation-skill
```

## Verifică instalarea

```bash
ls -la ~/.claude/skills/code-deliberation/SKILL.md
```

Apoi în Claude Code: `Review the last commit using the code-deliberation skill`.

## Structură

```
code-deliberation-skill/
├── SKILL.md             # YAML frontmatter + workflow
├── README.md
├── .gitignore
├── scripts/
│   ├── personalities.py # rejection sampling (G, C, K)
│   └── aggregator.py    # voting schemes
├── prompts/
│   ├── generator.md     # prompt creativ
│   ├── control.md       # prompt analitic
│   └── conservator.md   # prompt skeptic
└── examples/
    └── pr_review_example.md
```

## Utilizare

Skill-ul se activează automat când keywords precum "review PR", "evaluate change", "refactor planning", "risk assessment" apar în prompt.

Output: JSON cu `recommended`, `alternatives`, `voice_scores`, `confidence`, `deliberation_log`.
