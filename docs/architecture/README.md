# Architecture explainer — source

Interactive, single-page explainer of how Consilium works (voices, pipeline,
modes, Trias, voting, the learning loop). Authored as small React components,
transpiled in-browser by Babel-standalone — **no build step to preview**.

## Layout

| Path | Role |
|------|------|
| `index.html` | Entry point — loads React + Babel from CDN, links `styles.css`, mounts `src/*.jsx` into `#root`. |
| `index-print.html` | Print/export variant. |
| `styles.css` | All styling. |
| `src/*.jsx` | Components (`app.jsx` is the root; the rest are sections: `voices`, `pipeline`, `modes`, `trias`, `voting`, `cascade`, `loop`, `extras`, `primitives`, `tweaks-panel`). |
| `build.py` | Inlines the source into the shareable one-file exports. |

## Preview (no build)

Open `index.html` in a browser (needs internet for the React/Babel CDN). Edit any
`src/*.jsx` or `styles.css` and refresh — Babel re-transpiles on load.

## Build the shareable export

The committed `docs/architecture.html` (and `docs/architecture-print.html`) are
self-contained one-file exports generated from this source:

```bash
python docs/architecture/build.py          # regenerate both exports
python docs/architecture/build.py --check   # CI: fail if exports are stale
```

`build.py` inlines `styles.css` and each `src/*.jsx` into the entry HTML and
escapes embedded `</script>` to `<\/script>` (so they don't prematurely close
the host element). React + Babel still load from the CDN, keeping the export
small (~230 KB) and the source the single point of truth.

> After editing any source file, **rerun `build.py`** so the committed exports
> match the source. `--check` is the guard.
