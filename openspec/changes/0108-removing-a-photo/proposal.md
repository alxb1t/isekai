---
bump: minor
after: [0107-the-slowest-card]
---

# 0108 — removing a photo

In the Render dialog a photograph's tile is taken out of the session before the confirm, by its `×` or `⌫`; the
removal reaches `isekai render` as a repeatable `--without <runs>/<run-id>/<flow>`.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision, and the tests it costs |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `cli`, `ui` |

```
1 the planner  short(), quote(), _session() and again() take a `without`; `isekai render --without`
2 the server   the quote and the confirm carry it; each source's run id; jobs.render appends the flags
3 the dialog   tiles with × and ⌫, h j k l by flow, the first tile focused, centred scroll, all removed;
               the left-out lines gone, from the dialog and the quote
4 the record   docs D3, D4, D36; README.md and the interface READMEs
```

## Why

**A session renders every approval short of its count, and the operator cannot leave one out without editing its
approval.** The dialog shows each photograph that will render, so the choice belongs on its tile. The terminal gets
the same act as a flag, so the page's session is one the terminal can run
([docs D3](../../../docs/decisions.md#d3--the-hand-path-stays)).

## What Changes

- **`short()`** in `isekai/interface/render.py` takes a `without` set of `<runs>/<run-id>/<flow>` paths and wants none
  of them; a damaged approval is refused all the same ([D1](design.md#d1)).
- **`isekai render --without <runs>/<run-id>/<flow>`**, repeatable: refused under no runs root named, naming no run's
  flow, and beside a request; the retry the limit prints carries each ([D2](design.md#d2)).
- **`POST /api/render/quote`** and **`POST /api/render`** take `without`, a list of `{collection, run, flow}`; a
  quoted source gains its `run`; an entry naming no run's flow of a quoted collection is refused ([D3](design.md#d3)).
- **`Jobs.render`** takes `without` and appends `--without` per path to the verb's line ([D4](design.md#d4)).
- **The Render dialog's tiles**: `×` and `⌫` take a photograph out; `h` `l` along a flow's tiles, `j` `k` between
  flows, one Tab stop, centred scroll with the edges; the first tile holds the first focus; a row all taken out reads
  *all removed*, unticked ([D5](design.md#d5)–[D8](design.md#d8)).
- **The left-out lines go**: the dialog's *Not included* groups and the quote's `left_out` ([D9](design.md#d9)).
- **docs D3, D4 and D36** are amended; `README.md` and the interface READMEs name the flag ([D10](design.md#d10)).
- No run-file kind's version moves; the session record gains no field. No flow changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli` — *A render with no request renders every approval short of its count*: less each `--without`, with its
  refusals and its retry.
- `ui` — *Render is confirmed in a dialog that quotes what renders, its limit and its price at most*: tiles taken out
  by `×` and `⌫`, moved by `h j k l`; *all removed*; no left-out photographs; the confirmation carries what was taken
  out.
- `ui` — *A dialog holds the focus while it is open*: removed, as its Render scenario's title no longer holds.
- `ui` — *A dialog holds the focus from its first control while it is open*: added in its place, the Render dialog
  opening on its first photograph's tile.

## Impact

- Code: `isekai/interface/render.py`, `isekai/interface/cli.py`, `isekai/interface/ui/app.py`,
  `isekai/interface/ui/jobs.py`.
- UI: `ui/src/components/RenderDialog.vue`, `ui/src/thumbs.ts`, `ui/src/types.ts`, `ui/src/api.ts`,
  `ui/src/composables/useEdges.ts`, `ui/src/app.css`.
- Tests: `tests/test_render.py`, `tests/test_ui_jobs.py`, `ui/src/components/RenderDialog.test.ts`,
  `ui/src/composables/useEdges.test.ts`, `tests/e2e/test_render.py`.
- Docs: `docs/decisions.md`, `README.md`, `isekai/interface/README.md`, `isekai/interface/ui/README.md`.
- `gpunit.toml`, `config/`, `flows/`, the session record and every run-file kind's version are untouched.

## Not in this change

- Taking out a refused (damaged) entry: it stays a refusal (brief Q3).
- A session-record field for what was taken out: the record's lines already omit it (brief Q5).
- The *Not included* lines and the left-out thumbnails, moved anywhere else: they are dropped (brief Q11).
- Taking a photograph out for good: a removal lasts while the dialog is open, and changes nothing on disk.
- `ui/design/spec.md`'s Render dialog text: when the paydown edits that file.
