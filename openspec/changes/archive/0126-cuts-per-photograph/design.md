# Cuts per photograph — design

A cut moves under its photograph's digest, a name resolves by that digest, and a tattoo can be removed. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Every tattoo is one folder `.tattoos/<name>/`, and a name is kept once library-wide. A cut records `cut_from`, the run digest, and the list returns every tattoo, cuts of other photographs too. The page greys those out as *not this render's*, and the server refuses them.

Every route that reads a tattoo by name takes the name alone. Nothing deletes or renames.

```
before   .tattoos/<name>/                 upload or cut, one list, one namespace
after    .tattoos/<name>/                 an upload
         .tattoos/.cuts/<digest>/<name>/  a cut of that photograph
         list(digest) = the uploads + .cuts/<digest>/*
```

The person's first session on *Place a tattoo* found a cut of another photograph on every render, no way to remove the test cuts `test` and `test1`, and forms with no word on which to use. The outline-gestures change is this one's sibling. It is the page's alone and shares with this one only the ui spec and the changelog, by the plan.

Facts the cut rests on, each at the base commit of this branch:

- `check_name` refuses a leading dot and `_every` skips dot folders, so a folder named `.cuts` is neither a name nor a tattoo (`isekai/pipeline/tattoos.py`).
- A run-level folder reads as a flow, and one photograph's digest can be a run in several collections (`isekai/foundation/run.py`).
- A placement record copies the tattoo's name, `cut_from` and stage-1 pairs, and nothing reads it back (`isekai/pipeline/edit.py`, `isekai/foundation/artifacts.py`).
- The debt file holds no card this change closes, and neither manifest changes.

## Goals / Non-Goals

Goals:

- A cut is found, listed and named on its photograph alone.
- One name resolves to one tattoo on a render.
- A tattoo can be removed, with a second click.
- The picker says what each form takes.

Non-Goals:

- Renaming a tattoo.
- Listing a cut of another photograph, in any state.
- Mounting components in the UI tests.
- The page's gestures and keys.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | A cut lives at `.tattoos/.cuts/<digest>/<name>/` | keyed by the photograph, one cut serves its renders in every collection; the dot keeps it out of upload names and `_every` | a run-level folder, which reads as a flow |
| [D2](#d2) | A name is unique among what one render lists, and every name function and route takes the render's digest | the person sees one list per render, and a name on it is one tattoo | names library-wide, as before |
| [D3](#d3) | A cut kept today moves to its photograph's folder the first time the library is read | the person's `test` and `test1`; no step for the operator | a migration verb |
| [D4](#d4) | A tattoo is removed by `remove` and `DELETE /api/tattoos/{name}`; D52 reads *kept until removed* | the test cuts and a tattoo kept by mistake can go; no baked edit reads the library back | keeping every name for good |
| [D5](#d5) | The picker lists no cut of another photograph, offers *Remove* with a second click and puts a line under each form's heading | a cut belongs to its photograph, and the person could not tell which form to use | the greyed-out card; an undo for a removal |
| [D6](#d6) | The page passes the render's digest to every name call | the server needs it to resolve a name | a digest the server guesses from the session |

### D1

**Where a cut lives.** `CUTS = ".cuts"` is a folder of `.tattoos/`, and a cut is `.tattoos/.cuts/<digest>/<name>/` with the same files as before: `tattoo.json` and `outline.json`. An upload is `.tattoos/<name>/` as before.

The record keeps `cut_from`. A cut whose record names another digest than its folder is a damaged record, refused naming the folder by `_find` and by `_every` alike. `_publish` builds in a hidden `.keep-` folder inside the folder the tattoo is published to, then renames it, so a reader sees the whole tattoo or none.

### D2

**One name, one tattoo.** `_find(library, name, digest)` checks the name and the digest, and returns the upload folder when it holds a record, else the cut folder `.cuts/<digest>/<name>/`. A name neither holds is refused; when a cut of it sits under another digest, the refusal says `<name> is cut from photograph <digest>, not this render's; open it on a render of that photograph`, which is the refusal the library gives today.

`keep` refuses a name any upload or any cut holds, and `cut` refuses a name an upload or a cut of its own photograph holds. A cut of another photograph may share a name. A render's list repeats no name, so a reader meets one tattoo.

```
name asked + digest
   ├─ .tattoos/<name>/tattoo.json            → the upload
   ├─ .tattoos/.cuts/<digest>/<name>/        → the cut
   └─ neither → refused (names the photograph of a cut elsewhere)
```

The functions that take the digest, third, after the name: `named`, `design_bytes`, `read_outline`, `save_outline`. `listed(library, digest)` lists for it. `ink_layer`, `ink_view`, `preview` and `composite` already take it; its type is `str`, never `None`. `read_stage1`, `save_stage1` and `stage1_states` already take it. The old per-photograph filter goes: the resolver is its check.

A writer or a path builder takes the folder from `_find`, never from `_folder(library, name)`: `save_outline` writes the outline there, and `_stage1_path` builds from it.

### D3

**The move.** `_settle(library)` runs first in `_find`, `_every`, `keep` and `cut`. It moves each folder of `.tattoos/` whose name does not start with a dot, so a `.keep-` folder mid-publish stays, that holds a `tattoo.json` and no `design.png`, whose record says `kind` is `cut` and whose `cut_from` is a digest, to `.cuts/<cut_from>/<name>/` by one rename.

A record it cannot read is left for the read that follows, which refuses it naming the folder. A source another reader already moved is no error, and a destination that exists is left alone. A rename that fails refuses, naming the folder and the fix.

### D4

**Removal.** `remove(library, name, digest)` finds the tattoo as `_find` does, renames its folder to a hidden `.removed-` folder beside it, then deletes that folder, so a reader sees the whole tattoo or none. It removes a cut's `<digest>` folder when that is left empty. A bad name, a bad digest or an unknown tattoo is refused before anything is touched, and the path comes from the checked name and digest, never from the request.

`DELETE /api/tattoos/{name}?digest=<digest>` answers `{}`. The routes keep the guard that refuses a foreign `Origin` or `Host` before any handler. A baked edit keeps its own copy, so a removal changes no edit.

D52 in `docs/decisions.md` is amended in place, its title included, and every link to its old heading follows. `THREAT_MODEL.md` names the removal among the entry points.

### D5

**The picker.** `TattooPicker.vue` asks `tattoos(digest)`, so its cards are the uploads and this photograph's cuts. `card` loses its `choosable` and `reason` fields, and the picker its disabled state.

*Remove* is a button on each card. `armRemoval(armed, name)` in `ui/src/tattoos.ts` returns `{ armed, remove }`: a press on a card other than the armed one arms it and removes nothing, a second press on the armed card removes it. The button disarms when it loses focus, and a removal refreshes the list.

`formLine(form)` returns the line under a heading. Upload: *the tattoo's design on its own — a flat image, not a photo of skin*. Cut: *the tattoo as it shows on this render's photograph*.

### D6

**The page's calls.** `tattoos`, `tattooNamed`, `saveOutline`, `designAt` and `removeTattoo` in `ui/src/api.ts` take the digest first, and `inkView` takes a `Place` it always sends. `usePlacing` builds its server ports from its `place`, so `Ports.read` keeps its shape and `load` and `reload` stay as they are.

## Tests

The library and the routes are tested in Python and the page's rules in vitest. No end-to-end test is added (T1): no browser shows what a function and a route cannot. `git grep -c -i -E "tattoo|outline" -- tests/e2e` prints nothing, so no end-to-end test touches a tattoo to extend (T2).

**Added, by layer.** Each is named by its prefix so a `-k` finds it.

| layer | file | tests | binds |
|---|---|---|---|
| unit | `tests/test_tattoo_library.py` | `test_tattoo_cutdir_a_cut_is_kept_under_its_photographs_folder` | `tattoo:cut:a-cut-holds-no-image` |
| unit | `tests/test_tattoo_library.py` | `test_tattoo_cutdir_a_name_resolves_by_the_digest`, `test_tattoo_cutdir_a_cut_is_listed_on_its_photograph_alone` | `tattoo:library:a-name-resolves-by-the-renders-digest`, `tattoo:library:the-list-names-each-tattoo` |
| unit | `tests/test_tattoo_library.py` | `test_tattoo_cutdir_an_upload_and_a_cut_refuse_each_others_names` | `tattoo:library:a-name-is-one-tattoo-on-a-render` |
| unit | `tests/test_tattoo_library.py` | `test_tattoo_move_a_cut_kept_the_old_way_moves_once`, `test_tattoo_move_leaves_an_upload_and_a_damaged_record` | `tattoo:library:a-cut-kept-the-old-way-moves` |
| unit | `tests/test_tattoo_library.py` | `test_tattoo_remove_takes_an_upload_and_a_cut_and_frees_the_name`, `test_tattoo_remove_reaches_only_the_named_tattoo` | `tattoo:library:a-removed-tattoo-is-gone`, `tattoo:library:a-removal-reaches-only-the-named-tattoo` |
| unit | `tests/test_ui_tattoo.py` | `test_tattoo_route_delete_removes_an_upload_and_a_cut`, `test_tattoo_route_delete_refuses_a_missing_digest_and_an_unknown_name` | `tattoo:library:a-removed-tattoo-is-gone`, `tattoo:library:a-removal-reaches-only-the-named-tattoo` |
| unit | `ui/src/tattoos.test.ts` | `ui:picker:remove-takes-a-second-click`, `ui:picker:each-form-says-what-it-takes` | the same keys |

**Changed in place.** The calls of `tests/test_tattoo_library.py`, `tests/test_tattoo_placement.py`, `tests/test_ui_tattoo.py` and `tests/test_ui_placement.py` take the digest. The route-guard tests of `tests/test_ui_tattoo.py` and `tests/test_ui_placement.py` assert that nothing renames, and that `DELETE /api/tattoos/{name}` is the one route that removes. Their key becomes `tattoo:library:no-route-renames`.

**Removed or merged** (T5):

| test or assertion | carried by |
|---|---|
| the `choosable` and `reason` assertions of `spec('ui:picker:a-cut-of-another-photograph-cannot-be-chosen', …)` in `ui/src/tattoos.test.ts` | the same spec, rewritten over `tattoosPath` and `card`; it keeps its assertion that an upload reads the same on every render, and `choosable` and `reason` are retired with the disabled card |
| the *other photograph's cut* lines of `ui:picker:a-card-is-ready-for-this-photograph` and `ui:picker:not-on-this-photo-is-offered-on-an-upload-alone` in `ui/src/tattoos.test.ts` | retired with the path: no cut of another photograph reaches a card; the same tests keep every other assertion |
| `test_tattoo_route_guard_none_under_api_tattoos_deletes_or_renames` and its twin, `test_placement_route_guard_no_route_naming_a_tattoo_deletes_or_renames_one` and its twin | the same tests, rewritten for rename alone; the delete half is retired by [D4](#d4) |
| `test_tattoo_route_guard_twin_finds_a_delete_and_a_rename_when_one_is_added` | `test_tattoo_route_guard_twin_finds_a_rename_and_a_delete_elsewhere_when_added`, the same twin renamed for the route guard it now holds |

## Dependencies

None.

## Risks / Trade-offs

- **Between phases.** The first phase moves the server and the second the page, so the page between them asks routes that now need a digest. Each phase ends green; the change releases whole.
- **Shared files.** The outline-gestures change edits `ui/src/components/OutlineStep.vue`, `StageRender.vue`, `ui/src/composables/usePlacing.ts`, `ui/src/tattoos.ts`, `ui/src/app.css` and `ui/design/spec.md`. This change edits other lines of the same files; a merge that conflicts is one for the integrate step, and the digest passes through one line each.
- **A removal is final.** The second click is the only guard, and the folder is deleted. No baked edit reads it back.
- **A race.** Requests that keep one name at once can pass the check before either renames in `_publish`; the library serves one operator, so the later rename fails and refuses as a taken name.
- **A hand-edit for the release.** The Purpose paragraph of `openspec/specs/tattoo/spec.md` says each tattoo is kept "never deleted", and a delta folds requirements alone. The release rewrites that clause to *kept whole until it is removed*.
- **A cut in another digest's folder.** A cut whose record names another digest than its folder is refused as damaged, never listed under the wrong photograph.

## Migration Plan

A cut kept at `.tattoos/<name>/` moves by one rename the first time the library is read, and an upload does not move. A failed read leaves the folder where it was, and the next read tries again. Nothing for the operator to run: the person's `test` and `test1` move on the first `isekai ui` read.

## Verdict

Ready to build, the server first, with no package added and no format version moved.
