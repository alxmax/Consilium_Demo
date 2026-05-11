# Skill Feedback Log

Manual journal of real-world uses. One line per deliberation. Append-only.

## Format

```
YYYY-MM-DD | context           | chosen          | outcome | note
```

- **context** — short label (PR number, repo, "ad-hoc")
- **chosen** — id of the candidate that was actually shipped (or `do_nothing`, or `override` if you ignored the skill's recommendation)
- **outcome** — one of:
  - `OK`     — shipped, no regression observed after 1 week
  - `BAD`    — caused a regression / had to revert
  - `OVR`    — you overrode the recommendation; note the real choice
  - `PEND`   — too recent to evaluate
- **note** — what was useful or off about the deliberation (which voice helped/missed)

## Entries

<!-- newest at top -->

- 2026-05-11 | (template entry — delete after first real use) | example_id | PEND | scaffolding only
