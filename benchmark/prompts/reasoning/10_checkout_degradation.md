# Task 10 — Checkout Graceful Degradation

**Type:** Reasoning | **No code required**

---

An e-commerce checkout page makes calls to four internal services before rendering:

| Service | Purpose | Critical for checkout? |
|---|---|---|
| `payment-service` | Validate payment method, get available options | **Yes** |
| `inventory-service` | Confirm item is in stock | **Yes** |
| `recommendation-service` | Show "you may also like" widget | No |
| `profile-service` | Pre-fill shipping address from saved profile | No |

Each service responds in 50 ms–1 500 ms. The checkout page must respond to the user within **2 seconds total**. Under normal load all four are healthy. Under stress, the non-critical services occasionally become slow or unavailable.

The team must choose a resilience strategy:

- A) Call all four services in **parallel**; if any service fails or times out, return an error and abort checkout
- B) Call `payment-service` and `inventory-service` **in series** (one after the other) as the critical path; call `recommendation-service` and `profile-service` in parallel but treat their failures as non-fatal (show defaults)
- C) Call all four services in **parallel**; if `recommendation-service` or `profile-service` fails or times out, substitute cached or default values and continue checkout normally
- D) **Remove** `recommendation-service` and `profile-service` from the checkout page entirely — they are not needed for a purchase to complete

## Required answer format

**Pick exactly ONE option — A, B, C or D — and justify it.**

Your response must follow this exact structure:

1. **First line** (nothing else on it): `ANSWER: C` (or A, B, D — one letter only).
2. **Then the justification**, covering:
   - Why this option is the right choice.
   - Why each of the other three is worse (one sentence each).
   - The key assumption your pick relies on, and what would flip it.

No hedging. No "it depends". No picking two. Commit to one letter.

**Also save the same response to a file `answer.md` in your assigned workspace folder.** The runner reads that file to extract the `ANSWER:` line and compare it to the expected answer. If `answer.md` is missing or its first non-empty line is not `ANSWER: <letter>`, the correctness check fails automatically.
