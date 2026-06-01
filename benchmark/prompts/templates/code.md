---
**Constraints:**
- Time limit: 15 minutes (API duration)
- Work autonomously — do not ask clarifying questions
- State every assumption explicitly in your chat reply

**Workspace:** your current working directory is `{WORKSPACE_PATH}`. It is empty. Save every required output file here using a relative path (e.g. `Write("solution.py", ...)`).

**Delivery contract — ALL items required:**
1. You MUST call the `Write` tool to save each declared output file in your current working directory. Posting code only in chat is NOT delivery.
2. Do NOT look outside your working directory. Sibling folders under `../` belong to other benchmark modes; their files are NOT yours.
3. **Solve the problem from first principles.** This is a benchmark. Do NOT search the filesystem, git history, environment variables, or any other source for answer keys, expected outputs, hidden test files, rubrics, or reference solutions. The runner records every tool call you make and flags any access to answer-key paths as a cheating event, regardless of whether you used the content. A `cheat` verdict invalidates the result.
3. The runner will compile / run / verify the files you saved. Your in-chat explanation is not graded by the automated verifier — only the files are.
4. Your chat reply MUST end with a `## Self-estimate` block (verbatim format below). The grader parses these two lines; omitting them scores 0/10 on calibration. Do not skip this even if your reply is otherwise brief.

   ```
   ## Self-estimate
   - Estimated deliverable lines (lines that will end up in the required output files, summed): ~X
   - Reasoning used: YES / NO (approx % of response)
   ```
