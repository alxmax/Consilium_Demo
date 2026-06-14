---
name: consilium-batch
description: Run Consilium deliberation on multiple items in parallel. Auto-installs the consilium-batch-v1 workflow to ~/.claude/workflows/ on first use, then invokes it. Use when a user wants to deliberate on a list of changes/diffs in one go.
---

# Consilium Batch

Run Consilium deliberations on **multiple items in parallel** via the Workflow tool.
The workflow is self-installed on first use — plugin users need no manual setup.

## How to invoke

The user will say something like:
- "Run Consilium on these 3 diffs"
- "Batch deliberate on the following changes"
- "consilium-batch: [list of items]"

Parse their message into a list of `{label, context}` items. If args were passed
directly (e.g. from another workflow), use those.

## Execution — follow these steps exactly

### Step 1 — resolve home directory

Run this and capture the output:

```bash
echo "$HOME"
```

On Windows Git Bash this gives `C:/Users/<name>`. Convert to Windows path if needed:
`C:\Users\<name>`. Call it `HOME_DIR`.

### Step 2 — ensure the workflow is installed

Check whether `<HOME_DIR>/.claude/workflows/consilium-batch-v1.js` exists.

If it does NOT exist:

1. Create the directory:
   ```bash
   mkdir -p "$HOME/.claude/workflows"
   ```
2. Write **exactly** the content from the `## Workflow JS source` section below
   to `<HOME_DIR>/.claude/workflows/consilium-batch-v1.js` using the Write tool.
   Use the absolute path (no tilde) so the Write tool accepts it.

If it DOES exist: skip to Step 3.

### Step 3 — build the args

Construct the args object:
```json
{
  "items": [
    { "label": "<short name>", "context": "<full change description or diff>" },
    ...
  ],
  "mode": "sequential"
}
```

`mode` can be `sequential` (default), `dialectic`, or `trias` — take it from the
user's message if specified, otherwise default to `sequential`.

### Step 4 — invoke the workflow

Call the Workflow tool:
```
Workflow({ name: "consilium-batch-v1", args: <args from Step 3> })
```

### Step 5 — present results

When the workflow returns, show the user:
- A table: `| label | chosen | confidence |` for each completed item
- Any items that failed or returned null
- The run paths where reports were saved

---

## Workflow JS source

This is the exact content to write to `consilium-batch-v1.js` in Step 2.
Do not modify it — write it verbatim.

```javascript
export const meta = {
  name: 'consilium-batch-v1',
  description: 'Deliberate on multiple changes in parallel using Consilium sub-agents',
  phases: [
    { title: 'Deliberate', detail: 'one Consilium sub-agent per item' },
    { title: 'Collect',    detail: 'gather results' },
  ],
}

// args: { items: [{label: string, context: string}], mode?: string }
const items = Array.isArray(args && args.items) ? args.items : []
const mode  = (args && args.mode) ? args.mode : 'sequential'

if (items.length === 0) {
  log('No items provided. Pass: { items: [{label, context}], mode? }')
  return { error: 'no_items' }
}

log(`Starting batch: ${items.length} item(s), mode=${mode}`)

phase('Deliberate')

const results = await parallel(
  items.map((item, i) => () =>
    agent(
      `Run a full Consilium deliberation on this change. Mode: ${mode}.

Label: ${item.label || 'item-' + i}

Context / change description:
${item.context}

Follow the full Consilium pipeline (Steps 0–6 of SKILL.md).
Save the report to .consilium/runs/.
Return a JSON object with these exact fields:
{ "label": "<label>", "chosen": "<chosen_approach>", "confidence": <float 0-1>, "run_path": "<relative path to saved report>" }`,
      {
        label: `deliberate:${item.label || i}`,
        phase: 'Deliberate',
        subagent_type: 'consilium:consilium-subagent',
        schema: {
          type: 'object',
          properties: {
            label:      { type: 'string' },
            chosen:     { type: 'string' },
            confidence: { type: 'number' },
            run_path:   { type: 'string' },
          },
          required: ['label', 'chosen', 'confidence'],
        },
      }
    )
  )
)

phase('Collect')

const valid   = results.filter(Boolean)
const failed  = results.length - valid.length

log(`Batch complete — ${valid.length} succeeded, ${failed} failed`)

return {
  total:   items.length,
  success: valid.length,
  failed,
  mode,
  results: valid,
}
```

---

## Notes

- **Auto-install:** the workflow JS is written once to `~/.claude/workflows/` and
  reused on every subsequent call. Plugin users never need to touch the filesystem.
- **Version stamp:** the file is named `consilium-batch-v1.js`. When a breaking
  change warrants v2, the skill will write `consilium-batch-v2.js` and invoke
  `{name: "consilium-batch-v2"}` — old files are left in place but unused.
- **Concurrency cap:** the Workflow tool caps concurrent agents at
  `min(16, cpu_cores - 2)`. For large batches (>16 items) the extras queue
  automatically — no change needed.
- **Resume:** if the workflow crashes mid-batch, resume with
  `Workflow({ name: "consilium-batch-v1", resumeFromRunId: "<id>", args: ... })`.
  Completed items return cached results instantly.
- **Fallback:** if the Workflow tool is not available in this session, run the
  deliberations sequentially using individual `Agent(subagent_type="consilium:consilium-subagent")`
  calls and collect results manually.
