"""Build self-contained architecture HTML from the editable source.

Inlines styles.css and every `src/*.jsx` referenced by an entry HTML into a
single self-contained file (React + Babel-standalone still load from the CDN,
exactly as the source does). No proprietary bundler, stdlib only.

Why this exists: the page is authored as src/*.jsx + styles.css and previewed
by opening docs/architecture/index.html directly (Babel transpiles in-browser).
The committed docs/architecture.html is the shareable one-file export — rebuild
it with this script after editing any source file.

CRITICAL: every inlined `</script>` is escaped to `<\\/script>` so it does not
prematurely close the host <script> element (and stays valid once parsed).

Usage:
    python docs/architecture/build.py            # build docs/architecture.html
    python docs/architecture/build.py --check     # verify output is up to date (exit 1 if stale)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # docs/architecture/
DOCS = HERE.parent                              # docs/

# (source entry in HERE) -> (output file in DOCS)
ENTRIES = [
    ("index.html", "architecture.html"),
]

_LINK_CSS = re.compile(r'<link[^>]*rel="stylesheet"[^>]*href="([^"]+\.css)"[^>]*>')
_BABEL_SRC = re.compile(r'<script type="text/babel" src="([^"]+\.jsx)"></script>')


def _escape_script(text: str) -> str:
    """Neutralise embedded close-tags so they don't terminate the host element."""
    return text.replace("</script>", "<\\/script>")


def build_one(entry: str) -> str:
    html = (HERE / entry).read_text(encoding="utf-8")

    def inline_css(m: re.Match) -> str:
        css = (HERE / m.group(1)).read_text(encoding="utf-8")
        return "<style>\n" + css + "\n</style>"

    def inline_jsx(m: re.Match) -> str:
        code = (HERE / m.group(1)).read_text(encoding="utf-8")
        return (
            f'<script type="text/babel" data-source="{m.group(1)}">\n'
            + _escape_script(code)
            + "\n</script>"
        )

    html = _LINK_CSS.sub(inline_css, html)
    html = _BABEL_SRC.sub(inline_jsx, html)
    return html


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if any committed output differs from a fresh build")
    args = ap.parse_args(argv)

    stale = []
    for entry, out_name in ENTRIES:
        if not (HERE / entry).exists():
            continue
        built = build_one(entry)
        out_path = DOCS / out_name
        if args.check:
            current = out_path.read_text(encoding="utf-8") if out_path.exists() else None
            if current != built:
                stale.append(out_name)
        else:
            out_path.write_text(built, encoding="utf-8", newline="\n")
            print(f"wrote {out_path.relative_to(DOCS.parent)} ({len(built):,} bytes)")

    if args.check:
        if stale:
            print("STALE (rebuild with: python docs/architecture/build.py): " + ", ".join(stale),
                  file=sys.stderr)
            return 1
        print("outputs up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
