# Task 08 — Locking Strategy for Ticket Booking

**Type:** Reasoning | **No code required**

---

A ticket-booking system allows users to browse available seats (~30 seconds of browsing) and then reserve one. The system has these characteristics:

- **Concurrency:** 1 000 simultaneous users at peak
- **Conflict rate:** approximately 5% of reservation attempts collide (two users trying to book the same seat at the same time)
- **Database:** PostgreSQL, single table `seats` with a `status` column (`available` / `reserved`)

The team must choose a concurrency strategy for the reservation flow:

- A) **Pessimistic locking:** `SELECT ... FOR UPDATE` on the seat row as soon as the user opens the seat-detail page (holds the lock for the full 30-second browse)
- B) **Optimistic locking:** add a `version` integer to each row; read the current version, attempt `UPDATE ... WHERE version = $read_version`, retry if the update affects 0 rows
- C) **No locking:** execute `UPDATE seats SET status = 'reserved' WHERE id = $id`; if two updates race, the last write wins silently
- D) **Serial queue:** route all reservation requests through a single-threaded worker that processes them one at a time

## Required answer format

**Pick exactly ONE option — A, B, C or D — and justify it.**

Your response must follow this exact structure:

1. **First line** (nothing else on it): `ANSWER: B` (or A, C, D — one letter only).
2. **Then the justification**, covering:
   - Why this option is the right choice for this workload.
   - Why each of the other three is worse (one sentence each).
   - The key assumption your pick relies on, and what would flip it.

No hedging. No "it depends". No picking two. Commit to one letter.

**Also save the same response to a file `answer.md` in your assigned workspace folder.** The runner reads that file to extract the `ANSWER:` line and compare it to the expected answer. If `answer.md` is missing or its first non-empty line is not `ANSWER: <letter>`, the correctness check fails automatically.
