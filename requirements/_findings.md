# Open findings

> 1 open verify-intent item(s) across 1 requirement(s), aggregated from each requirement's `## WHAT — Verify intent` section by `reqmap.py sync`.
>
> These are open questions raised while reconstructing intent from code - NOT confirmed bugs. Resolve each by fixing the code or promoting the behavior into a Contract line. Run the AI triage pass (see SKILL.md) and drop a `_findings_triage.json` beside this file for a verified, prioritized view.

---

## CONSILIUM-CONFIDENCE-CALIBRATION-001 - confidence_calibration  (1)

- Should `modes/trias.md`'s "the default flips A→C automatically once that gate crosses its threshold" be enforced by code? Today nothing reads this script's verdict at dispatch time.

