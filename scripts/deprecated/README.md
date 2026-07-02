## scripts/deprecated/

Retired from the live pipeline, but **not necessarily dead**: `meta_critic.py`
(the only script left after the 2026-06-30 deletion sweep, PR #466) is retained
as the import target of the gated suite `scripts/test_meta_critic_trim.py` and
of 4 `evals/scenarios.json` cases. Deleting it requires retiring that suite
from `ci.yml` and the run-consilium driver first (the test-suite-coverage
invariant in `check_doc_drift.py` will otherwise fail).

Moved: 2026-05-17 (Senate refactor-bundle-7items, item S5); sweep: 2026-06-30 (PR #466)
