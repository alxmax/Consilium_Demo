# Task 06 — Split-Brain Financial Database

**Type:** Reasoning | **No code required**

---

A distributed database spans two data centres (DC-A and DC-B) and stores financial transaction records — payments and transfers. A network partition isolates the two DCs from each other for 40 seconds. Both DCs can still reach their own local users.

The engineering team must choose how the system behaves **during** the partition:

- A) Allow writes in **both** partitions simultaneously; reconcile conflicts automatically after reconnection
- B) Allow writes **only in the primary partition** (DC-A); DC-B rejects all write requests until the partition heals
- C) **Block all writes** in both DCs until the partition heals; reads are still served from local replicas
- D) **Buffer writes locally** in each DC and merge them automatically when the partition heals

## Required answer format

**Pick exactly ONE option — A, B, C or D — and justify it.**

Your response must follow this exact structure:

1. **First line** (nothing else on it): `ANSWER: B` (or A, C, D — one letter only).
2. **Then the justification**, covering:
   - Why this option is the right choice.
   - Why each of the other three is wrong (one sentence each).
   - The key assumption your pick relies on, and what would flip it.

No hedging. No "it depends". No picking two. Commit to one letter.

**Also save the same response to a file `answer.md` in your assigned workspace folder.** The runner reads that file to extract the `ANSWER:` line and compare it to the expected answer. If `answer.md` is missing or its first non-empty line is not `ANSWER: <letter>`, the correctness check fails automatically.
