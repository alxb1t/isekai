---
version: v0.43
backlog: [0068·R9, 0068·R10, 0068·R11]
---

# 0069 — the keys

One key registry for the whole app. Every command is declared once, never fires while typing, and every hint is drawn
from it. The new map: `⇧`+letter commands, plain letters where nothing is typed, `h j k l` in the grids and Review,
and **Mod** (`⌘` on macOS, `Ctrl` on Linux) where Option was.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the registry, the field rule, `Esc`, the map, Review's panes, the overlays, the cards |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` |

```
keydown ─▶ one listener ─▶ in a text field? ── yes ─▶ only Esc · Mod+↵ · Mod+Z · Mod+K
                                 │ no
                                 ▼
               top overlay ─▶ screen ─▶ global          first match runs; `?` lists them
```

## Why

**Ten views each listen for keys, and none checks for a text field.** A shortcut can fire while a tag is being typed.

**Option does not reach a Linux browser.** `Alt+Space`, the tag cheatsheet's key, is the window manager's menu there.

**No list of keys exists.** Hints are hand-written in many files, the hub alone has a key bar, and the design spec's
§7 disagrees with Review's code about `⌥←→`.

## What Changes

- **The registry** — a key store, one listener, scopes that stack ([D1](design.md#d1)).
- **The field rule and `Esc`'s order** ([D2](design.md#d2), [D3](design.md#d3)).
- **The map** — `⇧`+letter, plain letters, `h j k l`, **Mod** ([D4](design.md#d4)).
- **Review's panes** — rail, source, sheet and ④, by `h` / `l`; `j` / `k`; `⌃E` / `⌃Y` ([D5](design.md#d5)).
- **The overlays** — `?` the key list on every screen; `Mod+K` the tag cheatsheet; a key bar per screen
  ([D6](design.md#d6)).
- **The import sheet holds while it commits** — `0068·R9`, `0068·R11` ([D7](design.md#d7)).
- **D25** rewritten ([D8](design.md#d8)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - ADDED *Every command has one key, declared once, and none fires while typing* — the registry, the field rule,
    `Esc`'s order, the physical key, the key list.
  - MODIFIED *Sources are chosen in the file dialog, and each shows its own upload* — a commit in flight holds the
    sheet: no file added, no Import, no Cancel, no `Esc`.

## Impact

- **Code:** `ui/src/App.vue`, `ui/src/views/Home.vue`, `ui/src/views/Hub.vue`, `ui/src/views/Renders.vue`,
  `ui/src/views/RenderLarge.vue`, `ui/src/views/Compare.vue`, `ui/src/views/Session.vue`, `ui/src/views/Review.vue`,
  `ui/src/components/ImportSheet.vue`, `ui/src/components/RenderDialog.vue`, `ui/src/components/ReviseConfirm.vue`,
  `ui/src/components/RenderBar.vue`, `ui/src/components/SourcePanel.vue`, `ui/src/components/PhotoOverlay.vue`,
  `ui/src/components/RefusalPage.vue`, `ui/src/app.css`; new `ui/src/stores/keys.ts`, `ui/src/composables/useKeys.ts`,
  `ui/src/components/KeyHint.vue`, `ui/src/components/KeyBar.vue`, `ui/src/components/KeyList.vue`,
  `ui/src/grid.ts`, `ui/src/panes.ts`.
- **Tests:** new `ui/src/stores/keys.test.ts`, `ui/src/grid.test.ts`, `ui/src/panes.test.ts`;
  `tests/e2e/test_review.py`, `tests/e2e/test_render.py`, `tests/e2e/test_import.py`.
- **Docs:** `docs/decisions.md` (D25), `ui/design/spec.md`, `README.md`.

## Not in this change

- **④ as slots and its inner keys** — waits for the next change to ④.
- **Review's layout, its dialogs, its route and tab; Side by side (`⇧C`).**
- **Walking refusals** — `Mod+↓` is its key, built when the walk is.
- **Sessions; the stream; the reader; the job runner.**
- **`0068·R5`, `0068·R12`** — their triggers are the stream and the reader.
