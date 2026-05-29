# Task 13 — Allocation under ruin

**Type:** Reasoning | **No code required**

---

You manage a fund holding exactly **$100,000**. This quarter you must commit the full $100k to **exactly one** of the allocations below. A binding loan covenant applies: **if the quarter ends having returned $0 on the committed capital, the loan is called and the fund is liquidated** — there are no future quarters. Any strictly positive return, however small, keeps the fund alive. You want the best allocation for the long-run survival-and-growth of the fund.

Returns are on the full $100k and resolve at quarter end:

- A) **Venture deal.** 70% chance it returns **$300,000**; 30% chance it returns **$0**.
- B) **Index fund.** Returns **$140,000** with certainty.
- C) **Split:** put $50k in the venture deal and $50k in the index. (The venture half returns 3× on a hit / $0 on a miss; the index half returns 1.4× with certainty. The two halves resolve on the same 70/30 venture outcome.)
- D) Something else.

## Required answer format

**Pick exactly ONE option — A, B, C, or D — and justify it.**

Your response must follow this exact structure:

1. **First line** (nothing else on it): `ANSWER: A` (or B, C, D — one letter only).
2. **Second line** (nothing else on it): `VALUE: <number>` — the **expected (mean) total return** of your chosen allocation, in **thousands of dollars**, written with **1–4 decimal places** (format example only: `VALUE: XXX.XXXX`).
3. **Then the justification**, covering:
   - The expected return AND the worst-case return of each allocation.
   - How the loan covenant (ruin on a $0 return) changes the ranking.
   - The arithmetic that produces your VALUE.
   - Why each of the other three options is worse (one sentence each).

No hedging. No "it depends". No picking two. Commit to one letter.

**Also save the same response to a file `answer.md` in your assigned workspace folder.** The runner reads that file to extract the `ANSWER:` line and compare it to the expected answer. If `answer.md` is missing or its first non-empty line is not `ANSWER: <letter>`, the correctness check fails automatically.
