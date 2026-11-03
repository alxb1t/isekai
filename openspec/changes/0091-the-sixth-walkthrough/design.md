# Design — 0091 the sixth walkthrough

Each finding's fix, settled at the grilling and re-measured at `c82ffd8`; the line numbers below are `ab956e1`'s.
**Verdict: feasible.**

## Context

The operator walked every screen after `v0.60.0`. The findings sit in the vault; each fix below is the grilling's.
Since `ab956e1` the browser tests are `make e2e`, out of the gate, because Chromium never starts inside `mf-ship`'s
sandbox; CI runs them after the gate on every push.

## Goals / Non-Goals

**Goals:** each finding fixed as decided, each held by a unit test where one can fail, and by a browser test only for
what the browser alone shows.

**Non-Goals:** keys off macOS; the vanished volume; anything a pod does.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | One function, `progress({done, of})` in `ui/src/bars.ts`, sizes every bar. Prepare: `_Job` in `isekai/interface/ui/jobs.py` counts each stage's completed cells against its total from `job.steps`, carried in the snapshot, so a reload keeps them; the strip reads `tag 6 of 6 · caption 3 of 6 · sheet 0 of 6 · 00:35`. Render: images done over asked, in `RenderBar.vue` and `SessionDrawer.vue` alike, the drawer keeping `26:42 of 33:00` as text. With no plan, the stripe slides as today | one progress; time over the limit is a budget that never reaches the end | a bar per screen |
| <a id="d2"></a>**D2** | The Prepare bar in `ui/src/views/Hub.vue` reads `<n> photographs to prepare in <collection>`, photographs counted distinct; its button keeps `<n> changes · Prepare` | a photograph can have several flows | listing each change by name |
| <a id="d3"></a>**D3** | `DELETE /api/staging/{staged}/files/{name}` removes a read file, through a `remove` the import module's `Reader` owns, refused once sealed. A skipped tile leaves the sheet alone; a skipped upload names in `copy_of` the staged file it copies, and removing that file while its copy's tile stands hands the file to the copy instead; a tile still uploading offers no `×`. `GET /api/staging/{staged}/files/{name}` serves the cleaned file full size for `↵`. `.import__tiles` becomes a CSS grid, so `moved` in `ui/src/grid.ts` steps its rows; the first tile takes the focus once read unless a field holds it | nothing is committed and a file can be chosen again; a write goes through the function that owns it (D4 of the decisions) | asking before `⌫`; a client-side removal, since commit walks the folder |
| <a id="d4"></a>**D4** | `ImageViewer.vue`: `↵` toggles fit and full size as the click does, `j` `k` `↓` `↑` scroll by 120 px at full size, `h` `l` keep stepping; on a pair `↵` does nothing. The hub's `open` moves to `⇧↵` | one key, one meaning; the hub was the only screen giving `↵` away | `↵` toggling only where nothing opens |
| <a id="d5"></a>**D5** | macOS only: `paneKeys` in `ui/src/panes.ts` gives `⌃H` `⌃L` alone, from a field or not, and plain `h` `l` `←` `→` go to the pane; off macOS it is unchanged. `⌃E` `⌃Y` leave `Review.vue`. D25 gains `slot-down` and `slot-up` in its in-field list | the operator is on macOS; off macOS, dropping the plain keys would leave none | declaring `⌃H` `⌃L` on Linux |
| <a id="d6"></a>**D6** | ④ in `Review.vue` is a grid for `moved`: row 0 `−` `+`, a row per slot, the column kept; a control that disables passes its focus to the nearest enabled one in its row; `h` `l` across row 0 on macOS alone. `⇧J` `⇧K` scroll the rail's focused thumb in `CollectionRail.vue` with `scrollIntoView({ block: 'center' })` | as the operator asked | |
| <a id="d7"></a>**D7** | The key list is a modal `<dialog>` in `KeyList.vue`, centred, most of the window, columns by scope from a scope the key store exposes. The pick in `ComparePick.vue` sizes to its longest row in CSS — the head on two lines cut at their ends, out of the intrinsic width — floor 480 px, limit `100vw − 96px`, the 720 px cap gone, rows 20 px apart. The drawer is `max-content`, at least `max(50vw, 480px)`, at most `100vw − 100px`, its long text out of the intrinsic width | each holds its width whatever it shows | measuring in JS |

## Tests

| layer | adds | removes |
|---|---|---|
| unit | vitest for `progress`, the Prepare bar's words, the tile grid's keys, the viewer's `↵` and scroll, the pane keys under a stubbed `isMac`, ④'s grid, the rail's scroll, the key list's columns; pytest for each stage's count, the file's removal and its full-size route | none |
| end-to-end | none new; steps in `test_a_rendered_cell_opens_its_newest_image`, `test_compare_shows_both_versions_of_a_seed_each_under_its_head` and `test_the_drawer_holds_the_render` in `tests/e2e/test_render.py`, and the strip's text in `tests/e2e/test_prepare.py` | none |

**A step carries its test's key.** `tests/test_spec_bindings.py` holds one marker a test, so the pick's and the
drawer's width are steps under their tests' own keys, with no scenario of their own. `tests/e2e/` holds 29 tests (`grep -c '^def test_' tests/e2e/*.py`), on Chromium alone; this change adds none. Their
edits are checked by `uv run pytest --collect-only -q tests/e2e` in the build, and run by CI. This change deletes and
merges no test.

## Dependencies

None.

## Risks / Trade-offs

- **The browser tests are not run by the build** → each edit is a step in an existing test, collected by the build and
  run by CI; a red CI run is a patch.
- **`⌫` writes without `⇧`** → only on a chosen file, before anything is committed, and the spec names the exception.
- **Off macOS Review keeps plain `h` `l` between panes** → ④'s `h` `l` are declared on macOS alone, so Linux loses nothing.

## Verdict

**feasible.** Every file named exists at `ab956e1`, and each fix sits under an existing requirement or the viewer's new one.
