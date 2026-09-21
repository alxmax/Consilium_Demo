---
milestone: v1.1
id: SYS-CONSILIUM-IMPLEMENT-001
status: confirmed
level: system
layer: need
depends_on: []
owner: alxmax
risk: 1
---

# A verified implementation from a GO verdict

> Once a deliberation says GO, the developer can have the chosen approach written, tested and reviewed without the implementation work polluting the orchestrating session.

## Description

Every line in this section is binding.

- A GO report can be handed to the implementation pipeline, which returns a file manifest and a Control verdict, not a new deliberation report.
- Tests for the change are written by a role that never edits implementation files, and they fail before the implementation lands (the Red→Green gate).
- Which implementation steps run is decided from the report's magnitude and reversibility, and the developer confirms them before execution.

## Verify intent

- None - contract confirmed by the owner on 2026-09-21.

## Cases

- **CASE-1** — Given a GO report, when the implementation pipeline runs, then it returns a manifest listing the files written and a Control verdict.
- **CASE-2** — Given a test the Test Writer emitted, when it runs against the Coder's stub, then it fails first, then passes once the implementation lands.
- **CASE-3** — Given a report whose `chosen_approach` is `do_nothing` or whose `verification` is empty, when Step 7 is reached, then an error is shown and no implementation sub-agent is dispatched.
