---
id: AREA-NAME-NNN
status: draft        # draft | baseline | in-progress | implemented | confirmed | deprecated
layer: feature       # bus | feature
owner: alex
depends_on: []       # ids of bus/other capabilities this builds on
superseded_by:       # <ID>, if replaced
---

# Short name

> One line: what this is, in plain language.

## Input
- What the caller / runtime provides.

## Description
What it does between input and output, and why it exists. The "why" goes here —
code can never recover it. Keep it short; this is the part a human reads cold.

## Output
- What it produces. This defines the boundary.

## Acceptance (= tests)
- A checkable statement that becomes a test.
- An edge case → expected result.
- A failure mode → expected error.

## Links
- Used by: (auto)
<!-- members-in-code below are filled by reqmap.py scan — do not edit by hand -->
## Members in code (auto)
