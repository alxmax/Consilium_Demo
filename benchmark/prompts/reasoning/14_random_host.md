# Task 14 — Random host

**Type:** Reasoning | **No code required**

---

Three identical doors: one hides a **car**, the other two hide **goats**. You pick **door 1** (it stays closed).

The host then opens one of the other two doors — **but this host does NOT know where the car is.** He picks door 2 or door 3 **uniformly at random** and opens it. It happens to reveal a **goat**. (Had he opened the car by chance, the round would have been void; it wasn't — you observed a goat.)

You may now either **stay** with door 1 or **switch** to the remaining unopened door.

What should you do, and what is your probability of winning the car **if you switch**?

- A) Switch — P(win) = 2/3.
- B) It makes no difference — P(win) = 1/2 whether you stay or switch.
- C) Stay — P(win) = 2/3.
- D) Something else.

## Required answer format

**Pick exactly ONE option — A, B, C, or D — and justify it.**

Your response must follow this exact structure:

1. **First line** (nothing else on it): `ANSWER: A` (or B, C, D — one letter only).
2. **Second line** (nothing else on it): `VALUE: <number>` — your probability of **winning the car if you switch**, as a decimal in [0, 1] with **1–4 decimal places** (format example only: `VALUE: 0.XXXX`).
3. **Then the justification**, covering:
   - The probabilities of the car's location *conditioned on the observation that the host's random open revealed a goat*.
   - Why this scenario differs from the classic Monty Hall problem.
   - The arithmetic that produces your VALUE.
   - Why each of the other three options is wrong (one sentence each).

No hedging. No "it depends". No picking two. Commit to one letter.

**Also save the same response to a file `answer.md` in your assigned workspace folder.** The runner reads that file to extract the `ANSWER:` line and compare it to the expected answer. If `answer.md` is missing or its first non-empty line is not `ANSWER: <letter>`, the correctness check fails automatically.
