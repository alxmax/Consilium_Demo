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

- 2026-05-11 | dashboard_v3 overview review | C2+C3 | OK | C1 dropped (build-output dup, not real); C2 (skip legacy renderers on Summary) + C3 (targets to config.js) shipped; C5 vetoed
