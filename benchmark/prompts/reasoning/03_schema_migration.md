# Task 03 — Zero-Downtime Column Rename

**Type:** Reasoning | **No code required**

---

A SaaS backend uses PostgreSQL. The `users` table has 50 million rows and receives hundreds of writes per second around the clock. The team must rename the column `user_name` to `username` — no data transformation, just a rename. Downtime is not acceptable.

Which deployment strategy should the team use?

- A) Run `ALTER TABLE users RENAME COLUMN user_name TO username` directly in production, then deploy the updated application
- B) Add column `username`, backfill its value from `user_name` in batches, deploy the application to read and write `username`, drop `user_name`
- C) Add column `username` (nullable), deploy the application writing to **both** `user_name` and `username`, backfill old rows, deploy the application reading only `username`, drop `user_name`
- D) Create a database view: `CREATE VIEW users_v AS SELECT *, user_name AS username FROM users`, redirect the application to use `users_v`, rename and clean up later

## Required answer format

**Pick exactly ONE option — A, B, C or D — and justify it.**

Your response must follow this exact structure:

1. **First line** (nothing else on it): `ANSWER: A` (or B, C, D — one letter only).
2. **Then the justification**, covering:
   - Why this option achieves a zero-downtime rename correctly.
   - Why each of the other three fails or is inferior (one sentence each).
   - The key assumption your pick relies on, and what would flip it.

No hedging. No "it depends". No picking two. Commit to one letter.

**Also save the same response to a file `answer.md` in your assigned workspace folder.** The runner reads that file to extract the `ANSWER:` line and compare it to the expected answer. If `answer.md` is missing or its first non-empty line is not `ANSWER: <letter>`, the correctness check fails automatically.
