# Task 07 — Composite Index Prefix Rule

**Type:** Reasoning | **No code required**

---

A PostgreSQL table `users` has a composite B-tree index defined as:

```sql
CREATE INDEX idx_users ON users (last_name, first_name, email);
```

The table has 10 million rows. A developer writes four candidate queries and wants to know which one makes **efficient** use of the index (i.e., the index can be used to narrow the scan without a full index scan or sequential scan):

- A) `SELECT * FROM users WHERE email = 'alice@example.com'`
- B) `SELECT * FROM users WHERE first_name = 'Alice'`
- C) `SELECT * FROM users WHERE last_name = 'Smith' AND email = 'alice@example.com'`
- D) `SELECT * FROM users WHERE last_name = 'Smith' AND first_name = 'Alice'`

## Required answer format

**Pick exactly ONE option — A, B, C or D — and justify it.**

Your response must follow this exact structure:

1. **First line** (nothing else on it): `ANSWER: D` (or A, B, C — one letter only).
2. **Then the justification**, covering:
   - Why this option uses the index efficiently.
   - Why each of the other three does not (one sentence each).
   - The key assumption your pick relies on, and what would flip it.

No hedging. No "it depends". No picking two. Commit to one letter.

**Also save the same response to a file `answer.md` in your assigned workspace folder.** The runner reads that file to extract the `ANSWER:` line and compare it to the expected answer. If `answer.md` is missing or its first non-empty line is not `ANSWER: <letter>`, the correctness check fails automatically.
