---
milestone: v1.1
id: ARCH-CONSILIUM-IMPLEMENT-001
status: confirmed
level: architecture
layer: aggregate
depends_on: [CONSILIUM-IMPLEMENT-PIPELINE-001, CONSILIUM-IMPLEMENT-CODER-001, CONSILIUM-IMPLEMENT-TEST-WRITER-001, CONSILIUM-IMPLEMENT-SUBAGENT-001, CONSILIUM-INFER-PIPELINE-001, CONSILIUM-RENDER-IMPL-PREVIEW-001]
satisfies: [SYS-CONSILIUM-IMPLEMENT-001]
owner: alxmax
risk: 1
---

# Implementation pipeline

> The post-verdict path from a GO report to written, tested and reviewed code.

## Description

Every line in this section is binding.

- `implement_pipeline.py` turns a report into a dispatch plan, and `infer_pipeline.py` selects the steps from magnitude and reversibility. [[CONSILIUM-IMPLEMENT-PIPELINE-001]] [[CONSILIUM-INFER-PIPELINE-001]]
- The Coder owns implementation paths and the Test Writer owns `test_*` files, and the two never write the same path. [[CONSILIUM-IMPLEMENT-CODER-001]] [[CONSILIUM-IMPLEMENT-TEST-WRITER-001]]
- The implement sub-agent runs Coder, then Test Writer and Reviewer, and returns a manifest plus a Control verdict. [[CONSILIUM-IMPLEMENT-SUBAGENT-001]]
- `render_impl_preview.py` renders an optional static HTML review page from a report and diff. [[CONSILIUM-RENDER-IMPL-PREVIEW-001]]

## Verify intent

- None - contract confirmed by the owner on 2026-09-21.

## Cases

- **CASE-1** — Given a report whose chosen approach is `high` magnitude and `partial` reversibility, when `infer_pipeline.py` reads it, then the returned steps are implement, compile, review, test.
- **CASE-2** — Given a Coder and a Test Writer plan, when their paths are compared, then no path appears in both.
- **CASE-3** — Given a report and a unified diff, when `render_impl_preview.py` runs, then it writes one self-contained HTML page.
