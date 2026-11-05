---
bump: minor
backlog: [0091·R3]
---

# 0106 — deleting a render

`⇧⌫` on a render's large view asks *Delete this render?*, No first; Yes deletes that one render — its image, its
record and its thumbnail — and the Hub opens on its cell. `isekai discard <image>` is the same act in a terminal.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision, and the tests it costs |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `image-generation`, `cli`, `run-directory`, `ui` |

```
1 the function  generate.py's discard_render: the image, its record, an emptied group; library.py's drop_thumbnails
2 the verb      `isekai discard <image>`, through the ui package's front door for the thumbnails
3 the endpoint  DELETE …/renders/{digest}/{flow}/{version}/{seed}, refused while a session renders the collection
4 the page      ⇧⌫ and Delete on the large view; DeleteDialog, No first, h l, ↵, Esc; the Hub on the cell; ⌫
5 the record    D25; principles' Known breaks; data-flow, the READMEs, the interface row (0091·R3)
```

## Why

**A render sometimes fails — a doubled face — while other seeds of the same flow and photograph are good, and today
only a hand in the file manager removes it.** The operator sees the failure on the large view, so the delete belongs
there. A render is a likeness of a person ([`THREAT_MODEL.md`](../../../THREAT_MODEL.md)), so it is deleted, not
hidden.

## What Changes

- **`discard_render(image)`** in `isekai/pipeline/generate.py`, new: deletes the image, then its `.render.json`, then
  its `outputs/<NNN>/` group when that leaves it empty; a path naming no render is refused, nothing deleted
  ([D1](design.md#d1)).
- **`drop_thumbnails(run, image)`** in `isekai/interface/ui/library.py`, new: deletes the image's thumbnails from the
  library's `.cache/` ([D2](design.md#d2)).
- **`isekai discard <image>`**, a new verb: both deletions, one line per deleted path ([D3](design.md#d3)).
- **`DELETE /api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}`**, a new route: both deletions in the
  server's process, refused while a render session runs for the collection ([D4](design.md#d4)).
- **The large view's *Delete*** on `⇧⌫`, opening `DeleteDialog.vue`: No first and focused, `h` `l` move, `↵`
  presses, `Esc` is No ([D5](design.md#d5)). Yes opens the Hub focused on the render's cell ([D6](design.md#d6)).
- **`GLYPHS`** gains `Backspace: '⌫'`, so the import sheet's remove hint reads `⌫` ([D5](design.md#d5)).
- **No seed logic and no refusal** for a draft or approval made from the image ([D7](design.md#d7)).
- **D25 is amended** for `⇧⌫`; principles' *Known breaks* names the discard; the interface README lists staging's
  per-file `GET` and `DELETE` (0091·R3) ([D8](design.md#d8)).
- No run-file kind's version moves. No flow changes, so nothing is re-pinned.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `image-generation` — *A render is discarded whole, and its approval is left short*: added.
- `cli` — *The discard verb deletes a render named by its image path*: added.
- `run-directory` — *Artifacts are append-only and numbered, and re-running a command is a no-op*: a render's image
  and record are deleted only when the operator discards that render.
- `ui` — *The large view deletes its render after asking, and the Hub opens on its cell*: added.
- `ui` — *Every command has one key, declared once, and none fires while typing*: `⇧⌫` on a large view joins `⌫` on a
  chosen file as the commands that take no letter.
- `ui` — *A dialog holds the focus while it is open*: the Delete dialog is a confirming dialog, opening on *No*.

## Impact

- Code: `isekai/pipeline/generate.py`, `isekai/interface/cli.py`, `isekai/interface/ui/__init__.py`,
  `isekai/interface/ui/library.py`, `isekai/interface/ui/app.py`.
- UI: `ui/src/views/RenderLarge.vue`, `ui/src/views/Hub.vue`, `ui/src/components/DeleteDialog.vue` (new),
  `ui/src/api.ts`, `ui/src/stores/keys.ts`, `ui/src/stores/keys.test.ts`.
- Tests: `tests/test_generate.py`, `tests/test_ui_library.py`, `tests/test_pipeline_cli.py`, `tests/test_ui_api.py`,
  `tests/e2e/conftest.py`, `tests/e2e/test_render.py`.
- Docs: `docs/decisions.md`, `docs/principles.md`, `docs/data-flow.md`, `README.md`, `isekai/pipeline/README.md`,
  `isekai/interface/README.md`, `isekai/interface/ui/README.md`.
- `flows/`, `config/`, the session record and every run-file kind's version are untouched.

## Not in this change

- A trash folder or a tombstone: a render is a likeness, and every deletion here unlinks ([D1](design.md#d1)).
- A seed check, or a refusal for a draft or approval made from the image ([D7](design.md#d7)).
- Rewriting a session record: it is history, and the drawer shows what the session made.
- Deleting from the Renders grid: when the operator asks for a delete without opening the image.
- Sweeping thumbnails left by an earlier hand delete: when the cache's size is noticed.
