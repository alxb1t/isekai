---
bump: minor
version: v0.62
backlog: [0080·R4]
---

# 0091 — the sixth walkthrough

What the operator's sixth pass over the UI found, fixed in one version: one progress for every bar, a photograph
removed from an import, the viewer's keys, Review's keys and ④'s grid, the key list as a dialog, and Compare's pick
and the drawer sized to what they hold. macOS's keys alone.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each fix |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui`, `import` |

```
1 the bars      one progress for Prepare, the Render bar and the drawer · the Prepare bar's words
2 the import    a chosen file removed alone · the tiles' keys · a full-size preview
3 the viewer    ↵ fit and full size · j k scroll · ⇧↵ the hub's large view
4 Review        ⌃H ⌃L alone between panes on macOS · ⌃E ⌃Y gone · the rail in view · ④ a grid
5 the dialogs   the key list a dialog · Compare's pick and the drawer as wide as their rows
```

## Why

**A pass over every screen found what reads wrong or costs a step.** The Prepare stripe sits at a third whatever is
done, and the drawer's bar disagrees with the Render bar. A photograph chosen by mistake cannot leave an import. The
viewer's full size needs the mouse. Review's panes move on plain letters that the panes need. The key list covers the
screen's top. The pick changes width as the focus moves, and a long session scrolls the drawer sideways.

## What Changes

- **One progress** sizes every bar, and the Prepare bar names its photographs ([D1](design.md#d1), [D2](design.md#d2)).
- **A chosen file** is removed alone, the tiles take keys, and `↵` opens a file full size ([D3](design.md#d3)).
- **The viewer** toggles full size by `↵` and scrolls by `j` `k`; the hub's large view moves to `⇧↵` ([D4](design.md#d4)).
- **Review:** `⌃H` `⌃L` alone between panes on macOS, `⌃E` `⌃Y` gone, the rail's focus in view, ④ a key grid
  ([D5](design.md#d5), [D6](design.md#d6)).
- **The key list** is a dialog; **the pick** and **the drawer** take their rows' width ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui` — *The hub shows each source's stage…*: `⇧↵` opens an image's large view.
- `ui` — *Sources are chosen in the file dialog…*: a chosen file removed alone; the tiles' keys.
- `ui` — *Prepare runs what changed as one job…*: each stage's count; the bar's words.
- `ui` — *Every command has one key…*: macOS's pane keys, ④'s slot keys in a field, `⌫` on a chosen file.
- `ui` — *A dialog holds the focus while it is open*: the key list.
- `ui` — *The running render opens in a drawer every screen offers*: its width; one progress.
- `ui` — *Review opens a collection at its own address…*: ④'s grid; the rail's focus in view.
- `ui` — *A version says what it was, and Compare sets an image beside…*: the pick's width and head.
- `ui` — *The viewer shows an image fitted or at full size, by the mouse or the keys*: added.
- `import` — *Import is staged, and a commit is one move*: one staged file deleted before the commit.

## Impact

- `isekai/pipeline/importing.py`, `isekai/interface/ui/app.py`, `isekai/interface/ui/jobs.py`.
- `ui/src/`: `bars.ts`, `stores/live.ts`, `stores/keys.ts`, `panes.ts`, `slots.ts`, `views/Hub.vue`, `views/Review.vue`,
  `components/ImportSheet.vue`, `ImageViewer.vue`, `RenderBar.vue`, `SessionDrawer.vue`, `KeyList.vue`,
  `ComparePick.vue`, `RendersBlock.vue`, `CollectionRail.vue`, `app.css`; `ui/design/spec.md`; `docs/decisions.md`'s D25.
- Browser tests in `tests/e2e/` are edited; CI runs them, out of the gate.

## Not in this change

- Keys on Linux and Windows: their own version.
- A volume RunPod no longer knows: its own version, after gpunit's patch.
- Every backlog card but `0080·R4`, which closes: its SHALL holds, so it never comes due.
