"""Tests for _stub_bodies() in implement_pipeline.py.

Run:
    python scripts/test_implement_pipeline.py
"""
# tested-by: CONSILIUM-IMPLEMENT-PIPELINE-001
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from implement_pipeline import _stub_bodies

MARKER = "raise NotImplementedError"

_PASS = 0
_FAIL = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    if condition:
        _PASS += 1
        print(f"  PASS  {name}")
    else:
        _FAIL += 1
        msg = f"  FAIL  {name}"
        if detail:
            msg += f"\n        {detail}"
        print(msg)


# ---------------------------------------------------------------------------
# REGRESSION: single-line def
# ---------------------------------------------------------------------------

def test_single_line_def() -> None:
    source = textwrap.dedent("""\
        def f(x):
            return x + 1
    """)
    result = _stub_bodies(source, MARKER)
    lines = result.splitlines()

    # Line 0 = "def f(x):" — unchanged
    check(
        "single-line: header line preserved",
        lines[0] == "def f(x):",
        repr(lines[0]),
    )
    # Line 1 = "    raise NotImplementedError" — stub at indent+4 (0+4=4 spaces)
    expected_stub = "    " + MARKER
    check(
        "single-line: stub inserted at indent+4 on line 1",
        lines[1] == expected_stub,
        repr(lines[1]),
    )
    # Exactly ONE stub line was inserted
    stub_count = sum(1 for l in lines if MARKER in l)
    check(
        "single-line: exactly one stub line total",
        stub_count == 1,
        f"found {stub_count}",
    )


# ---------------------------------------------------------------------------
# REGRESSION: async def single-line
# ---------------------------------------------------------------------------

def test_async_def_single_line() -> None:
    source = textwrap.dedent("""\
        async def g():
            pass
    """)
    result = _stub_bodies(source, MARKER)
    lines = result.splitlines()

    check(
        "async single-line: header preserved",
        lines[0] == "async def g():",
        repr(lines[0]),
    )
    expected_stub = "    " + MARKER
    check(
        "async single-line: stub at indent+4 on line 1",
        lines[1] == expected_stub,
        repr(lines[1]),
    )


# ---------------------------------------------------------------------------
# NEW: multi-line def header
# ---------------------------------------------------------------------------

def test_multiline_def_header() -> None:
    source = textwrap.dedent("""\
        def foo(
            a, b
        ):
            return a + b
    """)
    result = _stub_bodies(source, MARKER)
    lines = result.splitlines()

    # The three header lines should be present in order
    check(
        "multi-line: 'def foo(' line present",
        any("def foo(" in l for l in lines),
        str(lines),
    )
    check(
        "multi-line: '    a, b' line present",
        any(l.strip() == "a, b" for l in lines),
        str(lines),
    )
    check(
        "multi-line: '):' line present",
        any(l.strip() == "):" for l in lines),
        str(lines),
    )

    # Stub must NOT be inserted after "def foo(" (line 0);
    # it must appear AFTER the "):" line.
    closing_idx = next(i for i, l in enumerate(lines) if l.strip() == "):")
    check(
        "multi-line: stub not inserted after first def line",
        lines[1].strip() != MARKER,
        repr(lines[1]),
    )
    stub_line = lines[closing_idx + 1] if closing_idx + 1 < len(lines) else ""
    check(
        "multi-line: stub inserted immediately after closing '):'",
        MARKER in stub_line,
        repr(stub_line),
    )

    # Stub indentation: def is at column 0, so stub must be at 4 spaces
    expected_stub = "    " + MARKER
    check(
        "multi-line: stub indented at def-indent+4 (4 spaces)",
        stub_line == expected_stub,
        repr(stub_line),
    )

    # Only one stub line total
    stub_count = sum(1 for l in lines if MARKER in l)
    check(
        "multi-line: exactly one stub line total",
        stub_count == 1,
        f"found {stub_count}",
    )


# ---------------------------------------------------------------------------
# NEW: stub actually raises — marker lands in body for multi-line case
# ---------------------------------------------------------------------------

def test_multiline_stub_is_executable() -> None:
    """The stubbed source, when exec'd, must raise on calling foo()."""
    source = textwrap.dedent("""\
        def foo(
            a,
            b,
        ):
            return a + b
    """)
    stubbed = _stub_bodies(source, MARKER)

    # exec in an isolated namespace
    ns: dict = {}
    try:
        exec(compile(stubbed, "<stubbed>", "exec"), ns)  # noqa: S102
    except SyntaxError as exc:
        check("multi-line exec: stubbed source compiles", False, str(exc))
        return

    check("multi-line exec: stubbed source compiles", True)

    raised = False
    try:
        ns["foo"](1, 2)
    except NotImplementedError:
        raised = True
    except Exception as exc:  # noqa: BLE001
        check("multi-line exec: foo() raises NotImplementedError", False, str(exc))
        return

    check("multi-line exec: foo() raises NotImplementedError", raised)


# ---------------------------------------------------------------------------
# NEW: indented multi-line def (method inside class)
# ---------------------------------------------------------------------------

def test_multiline_def_indented() -> None:
    """Method inside a class: stub must use method-indent+4."""
    source = textwrap.dedent("""\
        class C:
            def bar(
                self,
                x,
            ):
                return x
    """)
    result = _stub_bodies(source, MARKER)
    lines = result.splitlines()

    closing_idx = next(i for i, l in enumerate(lines) if l.strip() == "):")
    stub_line = lines[closing_idx + 1] if closing_idx + 1 < len(lines) else ""

    # "    def bar(" is at 4-space indent, so stub should be at 8 spaces
    expected_stub = "        " + MARKER
    check(
        "indented multi-line: stub at method-indent+4 (8 spaces)",
        stub_line == expected_stub,
        repr(stub_line),
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== test_implement_pipeline ===")
    test_single_line_def()
    test_async_def_single_line()
    test_multiline_def_header()
    test_multiline_stub_is_executable()
    test_multiline_def_indented()

    total = _PASS + _FAIL
    print(f"\n{_PASS}/{total} passed, {_FAIL} failed")
    sys.exit(0 if _FAIL == 0 else 1)


if __name__ == "__main__":
    main()
