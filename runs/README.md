# Deliberation Runs

Each time the skill is invoked, it should write the full deliberation as a JSON file here.

Filename: `YYYY-MM-DD_HHMM_<short-label>.json`
Example: `2026-05-12_1430_pr42-extract-helper.json`

## Schema

```json
{
  "timestamp": "2026-05-12T14:30:00Z",
  "context": {
    "repo": "...",
    "ref": "commit hash or PR number",
    "scope": "files touched, brief description"
  },
  "candidates": [
    {"id": "...", "summary": "...", "sketch": "...", "rationale": "..."}
  ],
  "verdicts": [
    {"id": "...", "valid": true, "issues": [], "notes": "..."}
  ],
  "scores": [
    {"id": "...", "risk_score": 0.0, "factors": {...}, "notes": "..."}
  ],
  "aggregation": {
    "scheme": "conservative_override",
    "chosen": "...",
    "vetoed": [...]
  },
  "recommended": "...",
  "confidence": 0.85
}
```

The `*.json` files in this directory are gitignored — they are personal logs, not part of the skill itself. The directory exists as scaffolding; the schema above is what `scripts/feedback.py` expects to read.
