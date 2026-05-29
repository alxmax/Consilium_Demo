# Task 12 — Backup restore

**Type:** Reasoning | **No code required**

---

A production PostgreSQL database was accidentally `DROP`-ed at **14:30** today. Your recovery assets:

- A **full base backup** taken every night at **02:00**. Today's 02:00 backup completed successfully.
- **Continuous WAL archiving** (write-ahead log shipping) configured for point-in-time recovery (PITR), which in principle lets you restore to any moment up to the present.

You check the WAL archive directory. The **most recent archived WAL segment has a timestamp of 09:00** today; no segments have arrived since. (The archiver has been silently failing since then — but all segments through 09:00 are present and valid.)

You must pick the **single recovery action that loses the least data while restoring a consistent database**.

- A) PITR: restore the 02:00 base backup and replay WAL forward to **14:29:59** (just before the drop) — lose ~30 seconds.
- B) Restore the 02:00 base backup and replay WAL forward to **09:00** (the last valid archived segment), then open the database.
- C) Restore only the 02:00 base backup; do not replay any WAL.
- D) Something else.

## Required answer format

**Pick exactly ONE option — A, B, C, or D — and justify it.**

Your response must follow this exact structure:

1. **First line** (nothing else on it): `ANSWER: A` (or B, C, D — one letter only).
2. **Second line** (nothing else on it): `VALUE: <number>` — the amount of committed data permanently lost by your chosen action, in **decimal minutes**, written with **1–4 decimal places** (format example only: `VALUE: XX.XXXX`). Measure from the latest recoverable commit point to the moment of the drop (14:30). If you pick A, B, or D, this is the loss implied by your chosen action.
3. **Then the justification**, covering:
   - The latest point in time to which a *consistent* database can actually be recovered, given the assets — and why.
   - The arithmetic that produces your VALUE.
   - Why each of the other three options is wrong (one sentence each).

No hedging. No "it depends". No picking two. Commit to one letter.

**Also save the same response to a file `answer.md` in your assigned workspace folder.** The runner reads that file to extract the `ANSWER:` line and compare it to the expected answer. If `answer.md` is missing or its first non-empty line is not `ANSWER: <letter>`, the correctness check fails automatically.
