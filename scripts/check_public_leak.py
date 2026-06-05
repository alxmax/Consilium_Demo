"""Guard: the published repo must not point back to its private source.

Fails (exit 1) if any tracked file references the private development
repository (any `alxmax/[Cc]onsilium…` that is not `…_Demo`) or leaks a
local absolute dev path. This keeps the public release repo decoupled from
its private source across rebuilds and dev->demo migrations — a private-repo
reference becomes un-shippable rather than a silent leak (e.g. the explainer's
"View repository" link, which once pointed at the private repo).

    python scripts/check_public_leak.py        # exit 1 + offending file:line on any hit

Stdlib only. Wired into CI (.github/workflows/ci.yml). Patterns are written
with character classes so this guard file does not match its own source.
"""
# implements: CONSILIUM-CHECK-PUBLIC-LEAK-001

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Owner-qualified repo refs only (the bare project name "consilium" appears in
# countless legitimate paths/strings). `_Demo` is the allowed public repo.
PATTERNS = [
    (re.compile(r"alxmax/[Cc]onsilium(?!_[Dd]emo)"), "reference to the private dev repo"),
    (re.compile(r"Desktop[\\/]+Doc[\\/]+[Cc]onsilium"), "local dev absolute path"),
]
SKIP_SUFFIX = (".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
               ".woff", ".woff2", ".ttf", ".zip", ".pdf")
SELF = Path(__file__).name


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if f.strip()]


def main() -> int:
    hits: list[str] = []
    for f in tracked_files():
        if f.endswith(SELF) or f.lower().endswith(SKIP_SUFFIX):
            continue
        try:
            text = Path(f).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat, desc in PATTERNS:
            for m in pat.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                hits.append(f"  {f}:{line}: {desc}: {m.group(0)!r}")

    if hits:
        print("public-leak guard FAILED — the published repo must not point back to "
              "the private dev repo or leak local paths:", file=sys.stderr)
        print("\n".join(hits), file=sys.stderr)
        return 1
    print("public-leak guard: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
