# Cuts per photograph — tasks

The library and its routes, then the picker. Each `Verify:` runs after its task.

## Progress

- [x] 1 — The library, its routes and the decision · hard
- [x] 2 — The picker and the page's calls · moderate

## 1 — The library, its routes and the decision

- [x] 1.1 **HALT CHECK** The library's folder paths are built in `isekai/pipeline/tattoos.py` alone. If another module builds one, the plan misses a reader: stop and say so.
  Verify: `git grep -c "TATTOOS" -- isekai/interface isekai/foundation isekai/shared` prints nothing.
- [x] 1.2 In `isekai/pipeline/tattoos.py` add `CUTS = ".cuts"` beside `TATTOOS`, `_digest_of(digest)` that returns a twelve-hex digest or raises the refusal `cut` and `_stage1_path` raise today (both call it), and `_cut_folder(library, digest, name)` returning `library / TATTOOS / CUTS / digest / name`, per [D1](design.md#d1).
  Verify: `grep -c "^CUTS = \".cuts\"" isekai/pipeline/tattoos.py` prints `1`.
- [x] 1.3 In `tattoos.py` replace `_load_named(library, name)` with `_load_named(library, name, digest)` over a new `_find(library, name, digest)` of [D2](design.md#d2). Replace `_every(library)` with `_every(library, digest)`, which lists the uploads and `.cuts/<digest>/*`. `_find` and `_every` refuse a cut whose `cut_from` is not its folder's digest as damaged, and `_damaged` names a cut's folder as `.tattoos/.cuts/<digest>/<name>`.
  Verify: `grep -c "^def _find(library: Path, name: str, digest: str)" isekai/pipeline/tattoos.py` prints `1`.
- [x] 1.4 In `tattoos.py` delete `_on_its_photograph` and its calls in `_view_image`, `preview` and `composite`, which `_find` replaces.
  Verify: `grep -L "^def _on_its_photograph" isekai/pipeline/tattoos.py` prints `isekai/pipeline/tattoos.py`.
- [x] 1.5 In `tattoos.py` give `listed(library, digest)`, `named`, `design_bytes`, `read_outline` and `save_outline` the digest (after `name`, and after `library` for `listed`). Pass it on in `_view_image`, `read_stage1`, `save_stage1`, `stage1_states`, `preview`, `composite`, `ink_layer` and `_newest_cut_tone`, and type the digest of `ink_layer` and `ink_view` as `str`. `save_outline` writes into the folder `_find` returns, and `_stage1_path` resolves its folder by `_find`, per [D2](design.md#d2).
  Verify: `grep -c "^def listed(library: Path, digest: str)" isekai/pipeline/tattoos.py` prints `1`.
- [x] 1.6 In `tattoos.py` add `_settle(library)` of [D3](design.md#d3) and call it first in `_find`, `_every`, `keep` and `cut`.
  Verify: `grep -c "^def _settle" isekai/pipeline/tattoos.py` prints `1`.
- [x] 1.7 In `tattoos.py` make `keep` refuse a name any upload or any cut holds, make `cut` refuse a name an upload or a cut of its own photograph holds and keep into `_cut_folder`, and let `_publish` take the folder it publishes into, per [D2](design.md#d2).
  Verify: `grep -c "^def _publish(parent: Path" isekai/pipeline/tattoos.py` prints `1`.
- [x] 1.8 In `tattoos.py` add `remove(library, name, digest)` of [D4](design.md#d4), and rewrite the module docstring's tree and last line: the cut folder, and that a tattoo is removed and never renamed.
  Verify: `grep -c "^def remove(library: Path, name: str, digest: str)" isekai/pipeline/tattoos.py` prints `1`.
- [x] 1.9 In `tests/test_tattoo_library.py` and `tests/test_tattoo_placement.py` pass `DIGEST` in each call of the functions task 1.5 changed. Point the stage-1 assertions of `tests/test_tattoo_placement.py` on the cut `arm` at `TATTOOS / ".cuts" / DIGEST / "arm"`, and assert that folder exists, so a missing folder cannot pass them.
  Verify: `uv run pytest tests/test_tattoo_library.py tests/test_tattoo_placement.py -q` exits 0.
- [x] 1.10 Add to `tests/test_tattoo_library.py` the tests named for `tattoo_cutdir` in the Tests table of [design](design.md#tests): a cut kept under `.cuts/<digest>/`, a name read by each photograph's digest, a list for one digest, the names an upload and a cut refuse each other, and a cut whose record names another digest than its folder refused by name and by list.
  Verify: `uv run pytest tests/test_tattoo_library.py -q -k tattoo_cutdir` exits 0.
- [x] 1.11 Add to `tests/test_tattoo_library.py` the tests named for `tattoo_move`: a cut written at `.tattoos/<name>/` by hand moves once on a `listed` call with its record and outline as they were, and an upload and a folder with a damaged record stay.
  Verify: `uv run pytest tests/test_tattoo_library.py -q -k tattoo_move` exits 0.
- [x] 1.12 Add to `tests/test_tattoo_library.py` the tests named for `tattoo_remove`: an upload and a cut removed leave the others and free their names, and `..`, `.cuts`, `a/b`, an unknown name and a bad digest are refused with nothing removed.
  Verify: `uv run pytest tests/test_tattoo_library.py -q -k tattoo_remove` exits 0.
- [x] 1.13 In `isekai/interface/ui/app.py` add `_digest_asked(digest)`, which refuses a missing digest with a refusal naming the field. Make `read_tattoos` always take it and always answer `stage1`, and make `read_tattoo`, `read_tattoo_design` and `put_outline` take `?digest=`.
  Verify: `grep -l "_digest_asked" isekai/interface/ui/app.py` prints `isekai/interface/ui/app.py`.
- [x] 1.14 In `app.py` add `digest` and `flow` to `INK_KEYS`, make `post_ink` always read `held(...)` and pass its photograph and digest, and add `DELETE /api/tattoos/{name}` as `delete_tattoo`, per [D4](design.md#d4). Rewrite the route list in the module docstring.
  Verify: `grep -c "delete_tattoo" isekai/interface/ui/app.py` prints `1`.
- [x] 1.15 In `tests/test_ui_tattoo.py` and `tests/test_ui_placement.py` add the digest to each request tasks 1.13 and 1.14 changed, and rewrite the route guards `_taking_away` to find a rename and a `DELETE` of anything but `/api/tattoos/{name}`, bound to `tattoo:library:no-route-renames`. Point the stage-1 assertions of `tests/test_ui_placement.py` on the cut `arm` at `.cuts/<digest>/arm` as task 1.9 does, and add the `test_tattoo_route_delete_*` tests of the [Tests](design.md#tests) table.
  Verify: `uv run pytest tests/test_ui_tattoo.py tests/test_ui_placement.py tests/test_ui_library.py -q` exits 0.
- [x] 1.16 In `docs/decisions.md` rewrite D52 under the heading `### D52 · The tattoo library is kept whole until a tattoo is removed`. Its body and *Why* name the upload folder and the cut folder, the names, the digest, the removal, and that a baked edit keeps its own copy.
  Verify: `grep -c "^### D52 · The tattoo library is kept whole until a tattoo is removed" docs/decisions.md` prints `1`.
- [x] 1.17 Change each link whose anchor ends `never-deleted` to `d52--the-tattoo-library-is-kept-whole-until-a-tattoo-is-removed`, in `docs/decisions.md`, `docs/edit-tattoo.md`, `docs/modules.md`, `isekai/pipeline/README.md` and `ui/design/spec.md`.
  Verify: `git grep -c "never-deleted" -- docs isekai ui/design THREAT_MODEL.md` prints nothing.
- [x] 1.18 In `THREAT_MODEL.md` add to *Entry points* the bullet **A tattoo's removal**: `DELETE /api/tattoos/{name}` deletes one folder of the library's `.tattoos/`, found from a checked name and a checked digest and never from a path in the request, behind the guard every route has, and the page asks a second click first. Link [D52](docs/decisions.md#d52--the-tattoo-library-is-kept-whole-until-a-tattoo-is-removed).
  Verify: `grep -c "A tattoo's removal" THREAT_MODEL.md` prints `1`.
- [x] 1.19 In `isekai/pipeline/README.md` rewrite the `tattoos.py` row: the cut folder under `.tattoos/.cuts/<digest>/`, the digest every name call takes, and that it removes a tattoo.
  Verify: `grep -c "\.cuts/<digest>/" isekai/pipeline/README.md` prints `1`.

## 2 — The picker and the page's calls

- [x] 2.1 In `ui/src/tattoos.ts` add `tattoosPath(digest)` returning `/api/tattoos?digest=<digest>`, `armRemoval(armed, name)` returning `{ armed, remove }` and `formLine(form)` returning the upload's line and the cut's line of [D5](design.md#d5). Delete the `choosable` and `reason` fields of `Card` and the cut-of-another-photograph branch of `card`.
  Verify: `grep -c "^export function armRemoval" ui/src/tattoos.ts` prints `1`.
- [x] 2.2 In `ui/src/tattoos.test.ts` rewrite the specs of the *removed or merged* rows of [design](design.md#tests): drop the `choosable` and `reason` assertions and the other-photograph cuts, and rewrite `ui:picker:a-cut-of-another-photograph-cannot-be-chosen` over `tattoosPath` and `card`. Add `ui:picker:remove-takes-a-second-click` and `ui:picker:each-form-says-what-it-takes`.
  Verify: `grep -c "ui:picker:remove-takes-a-second-click" ui/src/tattoos.test.ts` prints `1`.
- [x] 2.3 In `ui/src/api.ts` make `tattoos` read `tattoosPath(digest)`, and give `tattooNamed`, `saveOutline` and `designAt` the digest first, sent as `?digest=`. Add `removeTattoo(digest, name)` as a `DELETE` of `/api/tattoos/<name>?digest=<digest>`, and make `inkView` take a `Place`, never `null`, whose `digest` and `flow` it always sends, per [D6](design.md#d6).
  Verify: `grep -c "^export function removeTattoo" ui/src/api.ts` prints `1`.
- [x] 2.4 In `ui/src/composables/usePlacing.ts` replace `SERVER` by `serverPorts(place)`, whose `read` is `(name) => tattooNamed(place.digest, name)`, and default `ports` to it, so `load` and `reload` do not change.
  Verify: `grep -c "^const serverPorts" ui/src/composables/usePlacing.ts` prints `1`.
- [x] 2.5 Pass the digest at each other call: `designAt`, `saveOutline`, `inkView` and `tattooNamed` in `OutlineStep.vue`; `designAt` in `StagePhoto.vue`; `inkView` in `StageRender.vue`, with `props.place`; the card `src` in `TattooPicker.vue`. Delete the `held.choosable` refusal line of `OutlineStep.vue`, which no card can reach once a cut of another photograph is not listed.
  Verify: `grep -L "designAt(props.name)" ui/src/components/OutlineStep.vue` prints `ui/src/components/OutlineStep.vue`.
- [x] 2.6 In `ui/src/components/TattooPicker.vue` add the lines under both headings from `formLine` in a `picker__note mono` paragraph. Add *Remove* on each card from `armRemoval`: a second click calls `removeTattoo` and emits `removed`, and losing focus disarms it. Delete the disabled card, its `reason` line and the `choosable` test on the flag.
  Verify: `grep -l "removeTattoo" ui/src/components/TattooPicker.vue` prints `ui/src/components/TattooPicker.vue`.
- [x] 2.7 In `ui/src/views/Place.vue` handle `removed(name)`: call `placing.forget()` when the screen holds that tattoo, then `refresh()`, showing a refusal as `kept` does.
  Verify: `grep -l "removed" ui/src/views/Place.vue` prints `ui/src/views/Place.vue`.
- [x] 2.8 In `ui/src/app.css` delete the rules `.picker__card:disabled` and `.picker__reason`, and add `.picker__remove[data-armed='true']` in the accent the armed state of a button uses elsewhere.
  Verify: `grep -L "picker__reason" ui/src/app.css` prints `ui/src/app.css`.
- [x] 2.9 In `docs/edit-tattoo.md` rewrite the library bullet and the cut bullet of *The app* for the upload folder and the cut folder, the list per photograph, the removal and that a baked edit keeps its own copy, and drop `The app deletes and renames nothing.`
  Verify: `grep -L "The app deletes and renames nothing" docs/edit-tattoo.md` prints `docs/edit-tattoo.md`.
- [x] 2.10 In `ui/design/spec.md` replace the bullet *A cut of another photograph stays listed…* by one for *Remove* and its second click, and add the form lines to the J9·1 frame.
  Verify: `grep -L "stays listed" ui/design/spec.md` prints `ui/design/spec.md`.
