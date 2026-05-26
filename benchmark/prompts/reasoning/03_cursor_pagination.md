# Task 03 — Feed Pagination Architecture

**Type:** Reasoning | **No code required**

---

A mobile social app serves a reverse-chronological post feed. New posts are inserted frequently; spam posts are deleted frequently. Mobile clients paginate the feed and must be able to resume from their last position after the app is backgrounded for minutes or hours.

The team debates which server-side pagination strategy to implement:

- A) Offset-based: `GET /feed?offset=100&limit=20` — skip the first N rows
- B) Cursor-based: `GET /feed?cursor=<opaque_token>&limit=20` — resume from a stable bookmark
- C) Page-number: `GET /feed?page=5&per_page=20` — address by page index
- D) Something else — no standard pagination strategy fits; a bespoke solution is required

## Required answer format

**Pick exactly ONE option — A, B, C or D — and justify it.**

Your response must follow this exact structure:

1. **First line** (nothing else on it): `ANSWER: A` (or B, C, D — one letter only).
2. **Then the justification**, covering:
   - Why this option is the right choice for the described use case.
   - Why each of the other three is worse (one sentence each).
   - The key assumption your pick relies on, and what would flip it.

No hedging. No "it depends". No picking two. Commit to one letter.

**Also save the same response to a file `answer.md` in your assigned workspace folder.** The runner reads that file to extract the `ANSWER:` line and compare it to the expected answer. If `answer.md` is missing or its first non-empty line is not `ANSWER: <letter>`, the correctness check fails automatically.
