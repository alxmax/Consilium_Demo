# Task 09 — Data Pipeline Freshness SLA

**Type:** Reasoning | **No code required**

---

A recommendation engine must stay "fresh": after a user generates events (clicks, views, purchases), the recommendation model must reflect those events **within 5 minutes**. Events arrive at roughly **10 000 per second** at peak. The data engineering team has **2 engineers**.

The team is choosing the processing architecture:

- A) **Micro-batch every 1 minute** using Spark Structured Streaming: events are accumulated for 60 seconds, then a mini-batch job re-trains or updates the model
- B) **Per-event stream processing** using Apache Flink: each event is processed individually as it arrives, model updated in near real-time (sub-second latency)
- C) **Nightly batch job** using Apache Spark: all events from the day are processed once at 02:00 and the model is replaced
- D) **Lambda architecture**: a real-time path (Flink) handles recent events for low-latency lookups, a batch path (Spark) reprocesses all history nightly; results are merged at read time

## Required answer format

**Pick exactly ONE option — A, B, C or D — and justify it.**

Your response must follow this exact structure:

1. **First line** (nothing else on it): `ANSWER: A` (or B, C, D — one letter only).
2. **Then the justification**, covering:
   - Why this option is the right choice given the SLA and team size.
   - Why each of the other three is worse (one sentence each).
   - The key assumption your pick relies on, and what would flip it.

No hedging. No "it depends". No picking two. Commit to one letter.

**Also save the same response to a file `answer.md` in your assigned workspace folder.** The runner reads that file to extract the `ANSWER:` line and compare it to the expected answer. If `answer.md` is missing or its first non-empty line is not `ANSWER: <letter>`, the correctness check fails automatically.
