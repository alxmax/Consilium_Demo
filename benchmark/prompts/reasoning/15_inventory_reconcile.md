# Task 15 — Inventory reconciliation

**Type:** Reasoning | **No code required**

---

A warehouse tracks units of **Product X**. This morning the system shows **480 units** on hand. During the day, in this order:

1. A delivery arrives: **12 cases** of Product X, **24 units per case**.
2. **350 units** of Product X are shipped to customers.
3. An auditor finds that *yesterday's* shipment of **60 units** of Product X was accidentally entered into the system **twice**. She fixes the duplicate today.
4. A customer returns **15 units** of Product X. On inspection, **5 are damaged** and scrapped (not returned to sellable stock); the rest go back on the shelf.
5. A quality sweep finds **18 units** of Product X expired and writes them off.
6. A delivery arrives: **5 cases** of **Product Y** (a different SKU), **40 units per case**.

What is the **on-hand count of Product X** at the end of the day?

- A) 410
- B) 475
- C) 470
- D) Something else

## Required answer format

**Pick exactly ONE option — A, B, C, or D — and justify it.**

Your response must follow this exact structure:

1. **First line** (nothing else on it): `ANSWER: A` (or B, C, D — one letter only).
2. **Second line** (nothing else on it): `VALUE: <number>` — the end-of-day on-hand count of Product X, as an integer (format example only: `VALUE: XXX`).
3. **Then the justification**, showing the running balance after **each** of the six events (one line each), and one sentence on why each of the other three options is wrong.

No hedging. No "it depends". No picking two. Commit to one letter.

**Also save the same response to a file `answer.md` in your assigned workspace folder.** The runner reads that file to extract the `ANSWER:` line and compare it to the expected answer. If `answer.md` is missing or its first non-empty line is not `ANSWER: <letter>`, the correctness check fails automatically.
