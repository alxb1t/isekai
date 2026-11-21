# The delete owner — design

A render's and an edit's delete move into one foundation module that drops every thumbnail an image names while the image is a file, then deletes the files, then the approval; the verb and the route call it. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

A render's delete is chained from `discard_render` of `isekai/pipeline/generate.py`, `withdraw` and `_holds_render` of `isekai/pipeline/review.py`, `delete_edits` of `isekai/foundation/layout.py` and `drop_thumbnails` of `isekai/foundation/library.py`. An edit's delete is `discard_edit` of `isekai/pipeline/edit.py`. Each front end chains them by hand.

```
now                                          after
verb  ─▶ drop_thumbnails (the render's)      verb  ─┐
      ─▶ discard_render ─▶ withdraw                 ├─▶ foundation/discard.py
      edit path: discard_edit, no thumbnail  route ─┘     delete_render  delete_edit
route ─▶ drop_thumbnails (render, each edit)               1 thumbnails, while the images are files
      ─▶ discard_render ─▶ withdraw                        2 the files: discard_render · discard_edit
        (both returned lists thrown away)                  3 the approval: withdraw
```

A thumbnail is named by its image's digest, so it goes before its image does. The verb drops the render's alone and, on an edit's path, none; the route drops the render's and each edit image's. The principles list that difference as a break, and the spec of the page says deleting a render deletes its bakes' thumbnails with its own.

[The thumbnail names](../0180-the-thumbnail-names/design.md) put `thumbnail_of`, `file_digest` and `drop_thumbnails` in `isekai/foundation/library.py`, and [the layout tail](../0179-the-layout-tail/design.md) put `current_draft`, `source_copy` and `EDIT_SUFFIXES` in `isekai/foundation/layout.py`. Each moved body reads foundation names alone, so the owner can sit in the foundation, where a stage may not import another and `run.py`'s siblings may not call `rendered_at` ([D62](../../../docs/decisions.md#d62--the-run-directory-is-runpy-its-siblings-imported-through-it)).

## Goals / Non-Goals

- Goals: a delete is one call; the verb drops the thumbnails of a render's edits and, on an edit's path, the edit's and its chain's; no loop is left in a front end; the two *Known breaks* of the principles leave.
- Non-Goals: see [proposal](proposal.md#not-in-this-change). In short, the guards, `_derived`, a route that deletes an edit and the making of a thumbnail are not here.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `isekai/foundation/discard.py` holds the bodies of `discard_render`, `withdraw`, `_holds_render` and `discard_edit`, moved unchanged, each bound back at its old home as `X as X` | the owner needs them below the stages, and a move that re-binds changes no importer and no test | a copy in the foundation beside the stage's; repointing the tests' imports |
| [D2](#d2) | `Deleted(files, thumbnails)`, `delete_render(image)` and `delete_edit(image)`: refuse an unnamed path, drop the thumbnails, delete the files, then for a render the approval | a thumbnail is named by its image's digest, so it goes first; a path that names nothing must delete nothing | returning the thumbnails from the delete's own list: it cannot name them once the image is gone |
| [D3](#d3) | `_chain(group, seed, number)` is split out of `discard_edit`, which calls it | the owner must know the chain's numbers before it deletes any of them; the unreadable-record refusal stays before every delete | the owner reading the chain a second way |
| [D4](#d4) | the verb and the route call the owner and write no loop; the guards stay where they are | one owner is the point, and the guards are the acts' | the owner taking the job slot or the session's lock |
| [D5](#d5) | the bodies are pre-flighted before they move; the survivors of `withdraw` are killed by cases first | a move is pre-flighted, and a survivor is killed by a test or named equivalent | naming the survivors equivalent: neither is, the product's layout only never reaches one |
| [D6](#d6) | the owner's cases are written before it, each of the verb's scenarios gets a case that fails before the switch, and a case holds that the verb and the route leave one cache | red first proves the owner and the switch; the twin guards the route's | one end-to-end test: the cache is a folder of files |
| [D7](#d7) | D72 is added; the page's D4 and D69 name the owner; the *Known breaks* of the stage principle leave `docs/principles.md` | the choice in force is edited where it lives | a new decision for each |

### D1

`discard.py` imports the names its bodies read from `isekai.foundation.run`, as `isekai/foundation/library.py` does, and `read` and `EDIT_FILE` from `isekai.foundation.artifacts`. It is no sibling `run.py` re-exports, so `run.py` does not import it. Its docstring cites D72 as a plain `D72`.

```python
"""The bodies of a render's and an edit's delete, bound back at the stages that held them (D72).

Stdlib only, and on `python -m isekai`'s import graph.
"""
```

`generate.py` binds `from isekai.foundation.discard import discard_render as discard_render`, `edit.py` binds `discard_edit as discard_edit`, and `review.py` binds `withdraw as withdraw` and `_holds_render as _holds_render`. The tests import the public names from the stages, and no code reads `_holds_render` outside `withdraw`; it is bound for the old home's sake, as [the decision of the cascade](../../../docs/decisions.md#d68--the-collections-names-and-the-sessions-read-side-are-foundationlibrarypy-re-bound-at-their-old-homes) binds a name the old home no longer reads. `ruff check --fix` drops each import a stage read for these bodies alone.

### D2

The module's docstring becomes the owner's when the owner is added:

```python
"""A delete's one owner: a render's or an edit's files, their thumbnails and the approval.

`delete_render` and `delete_edit` drop the thumbnail of every image that goes while the
image is still a file, since its bytes name the thumbnail, then delete the files, then,
for a render, the approval its last render leaves (D72). The bodies they call are here
too, bound back at the stages that held them.

Stdlib only, and on `python -m isekai`'s import graph.
"""
```

```python
class Deleted(NamedTuple):
    """What a delete removed: the run's files, then the library's thumbnails."""

    files: list[Path]
    thumbnails: list[Path]


def delete_render(image: Path) -> Deleted:
    """Delete a render, its edits, each one's thumbnail and the approval its last leaves.

    The path is checked first, so one naming no render deletes nothing. The thumbnails
    go while their images are files: the render's, then each edit's in number order.
    e.g. outputs/001/42.png, with 42.edit-1.png -> files [..., 42.png, ...], thumbnails [42, 42.edit-1]
    """
    ref = rendered_at(image)
    group = image.absolute().parent
    thumbnails = drop_thumbnails(ref.run, image)
    for number in edit_numbers(group, ref.seed):
        if (own := edit_files(group, ref.seed, number)[0]).is_file():
            thumbnails += drop_thumbnails(ref.run, own)
    files = [*discard_render(image), *withdraw(ref.run, ref.flow, ref.version)]
    return Deleted(files, thumbnails)


def delete_edit(image: Path) -> Deleted:
    """Delete an edit and every edit made from it, with each one's thumbnail.

    An edit whose record cannot be read is refused before anything is deleted.
    e.g. 42.edit-1.png, with 42.edit-2 made from it -> thumbnails [edit-1, edit-2]
    """
    ref = edit_at(image)
    group = image.absolute().parent
    numbers = _chain(group, ref.seed, ref.k)
    thumbnails: list[Path] = []
    for number in numbers:
        if (own := edit_files(group, ref.seed, number)[0]).is_file():
            thumbnails += drop_thumbnails(ref.run, own)
    return Deleted(delete_edits(group, ref.seed, numbers), thumbnails)
```

`delete_render` reads the version from the path, where the route read it from the address; the image of the route's address is `group_of(run, flow, version) / <seed>.png`, so both name one group. A pending edit has no image, so it has no thumbnail and no line.

### D3

`discard_edit` keeps its docstring and its answer; its body is the chain's loop moved to `_chain`, which returns the numbers ascending, and a call of `delete_edits`:

```python
def _chain(group: Path, seed: int, number: int) -> list[int]:
    """Return edit `number` of `seed` and every edit whose source chain reaches it.

    An edit whose record cannot be read is refused, so a caller deletes nothing first.
    e.g. 42.edit-1, with 42.edit-2 made from it -> [1, 2]
    """
    sources: dict[int, str | None] = {}
    for held in edit_numbers(group, seed):
        record = edit_files(group, seed, held)[1]
        sources[held] = read(record, EDIT_FILE)["source"] if record.is_file() else None
    taken = {number}
    while grown := {
        held
        for held, source in sources.items()
        if held not in taken
        and source in {edit_files(group, seed, each)[0].name for each in taken}
    }:
        taken |= grown
    return sorted(taken)


def discard_edit(image: Path) -> list[Path]:
    ref = edit_at(image)
    group = image.absolute().parent
    return delete_edits(group, ref.seed, _chain(group, ref.seed, ref.k))
```

The cases of `tests/test_edit_session.py` that run `discard_edit` hold it, and they change none of their assertions.

### D4

`run_discard` reads the run from the ref, asks the disk whether a render session holds the collection, calls `(delete_edit if edited else delete_render)(image)` and prints, as before, each file from the runs root and then each thumbnail from the library:

```python
deleted = (delete_edit if edited else delete_render)(image)
for path in deleted.files:
    print(f"discard deleted {path.relative_to(run.path.parent)}", file=wired.out)
for path in deleted.thumbnails:
    print(f"discard deleted {path.relative_to(run.path.parents[2])}", file=wired.out)
return 0
```

`ImageRoutes.delete_render` keeps `self.surface.rendered(...)`, the draft lock and its job-slot refusal, and calls `delete_render(image)` where it chained the owners. The verb's printed lines are today's on a tree with no edit thumbnail. [The acts](proposal.md#not-in-this-change) own the guards' gaps.

### D5

The pre-flight is `tools.mutate` over each body, one run a range, on the tests that reach it. The cut ran each at `3dc8274b`; `0179` moves the lines of `edit.py` and `review.py` by one and by twenty-two, so the ranges below are the ones it leaves.

| function | range at `0179`'s tip | result at the base |
|---|---|---|
| `discard_render` | `isekai/pipeline/generate.py:337-366` | 7 killed, 0 survived |
| `discard_edit` | `isekai/pipeline/edit.py:329-350` | 5 killed, 0 survived |
| `_holds_render` | `isekai/pipeline/review.py:571-574` | 3 killed, 0 survived |
| `withdraw` | `isekai/pipeline/review.py:577-635` | 25 killed, 2 survived |

The tests for `discard_render` and `discard_edit` are `tests/test_generate.py`, `tests/test_edit_session.py`, `tests/test_edit_placement.py` and `tests/test_pipeline_cli.py`; for `_holds_render` and `withdraw`, `tests/test_review.py`, `tests/test_pipeline_cli.py`, `tests/test_edit_session.py`, `tests/test_ui_api.py` and `tests/test_generate.py`, the last two with `"-k not test_without_the_lock_an_update_writes_after_the_approval"`, which races by design and times a mutant out.

The survivors of `withdraw` are the `rmdir` of a group of failure records, which every case asserts by the returned list and none by the disk, and the `reverse=True` of the deepest-first order, which no layout a stage writes reaches. Each is killed by a case in `tests/test_review.py` before the body moves:

| case | holds |
|---|---|
| `test_a_withdrawn_failure_only_group_is_gone_from_disk` | the setup of `test_an_older_approval_whose_group_holds_failure_records_alone_goes`, then `group.exists()` is false; binds `image-generation:discard:a-group-of-failure-records-is-no-render` |
| `test_a_nested_folder_under_a_flows_own_folder_goes_with_it` | a flow with one approval and a folder holding a file under its `sources/`; after `withdraw` the flow's directory is empty; binds `image-generation:discard:a-flow-with-no-approval-keeps-its-assignment` |

A build whose base differs from `0179`'s tip finds each range with `git grep -n -e "^def <name>"` and runs the same command over `def` to the last line; a rescue re-fits the ranges below if the text differs. A range with no mutant is refused with exit 2.

### D6

The cases sit at the lowest layer that can fail. The owner's are unit cases over a group in a collection built under `tmp_path`: `lib/b/sources/`, and `lib/b/runs/0123456789ab_a/` holding `run.json`, the group `<FLOW>/outputs/001` and the edits `_chain` writes. A thumbnail is the file `thumbnail_of(lib, run, image)` names, holding `b"jpg"`, and another collection's is a file beside it named `<stem>.other.jpg`.

| case | file | holds |
|---|---|---|
| `test_edit_discard_the_owner_takes_a_render_its_edits_and_their_thumbnails` | `tests/test_edit_session.py` | `delete_render` of `42.png` with edits 1 and 2 imaged and 3 pending: `Deleted.thumbnails` are the render's, edit 1's and edit 2's in that order, each file is gone, `Deleted.files` equal what `discard_render` returned on a twin, and `.other.jpg` stays |
| `test_edit_discard_the_owner_takes_the_last_renders_approval_with_it` | `tests/test_edit_session.py` | `delete_render` of the only render of `counted`'s approval, which has an edit and a thumbnail: `Deleted.files` hold the group and the approval, the approval is gone, and the thumbnail is returned |
| `test_edit_discard_the_owner_takes_an_edit_its_chain_and_their_thumbnails` | `tests/test_edit_session.py` | `delete_edit` of `42.edit-1.png`: the thumbnails of edits 1 and 2 are gone and returned in that order, the render's stays |
| `test_edit_discard_the_owner_refuses_an_unreadable_chain_before_dropping_a_thumbnail` | `tests/test_edit_session.py` | `42.edit-2.json` holds `{ not json`: `delete_edit` of edit 1 raises naming it, and every file and thumbnail is as it was |
| `test_edit_discard_the_verb_takes_a_renders_edits_thumbnails_with_it` | `tests/test_edit_session.py` | `isekai discard` of a render with edits 1 and 2 in `counted`'s collection: the thumbnails are printed after the run's files, the render's first, and gone; binds `cli:discard:a-render-takes-its-edits-thumbnails-with-it` |
| `test_edit_discard_the_verb_takes_an_edits_thumbnail_and_its_chains` | `tests/test_edit_session.py` | `isekai discard` of edit 1 with edit 2 made from it: both thumbnails printed and gone in order, the render's stays; binds `cli:discard:an-edit-takes-its-own-thumbnail-and-its-chains` |
| `test_the_verb_and_the_route_leave_one_cache_with_edits_seeded` | `tests/test_ui_api.py` | the library copied whole, the verb run on the copy's render and the route on the original's, bake 1 and bake 2 imaged and their thumbnails made: the verb's cache and the route's hold the same files |

The owner's cases carry `spec_exempt("structural: ...")`, and the twin too: the scenarios they would bind are held by the verb's cases and the page's existing ones. The verb's cases fail before the verb is switched, because it drops no edit's thumbnail; the owner's fail before the owner exists, by a collection error. The twin passes before the route's switch, because the route already drops each edit's, and guards it after.

### D7

- D72 is added after D71 of `docs/decisions.md`: the owner's name and what it does in the bold paragraph, *Why* the owners were chained by hand and the digest's order, *Accepts* the guards, `_derived`, `review.discard` and `tattoos.remove` staying, and *Made by* `0181`.
- [D4 of the page](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children), in its sentence on writes through the function that owns them, names `delete_render` and `delete_edit` for a deleted render, its edits and thumbnails and the approvals its last render leaves, where it named `drop_thumbnails`, `discard_render` and `withdraw`; its *Made by* gains `0181`.
- D69's bold paragraph no longer lists `discard_render` among what the stage keeps, and says it is bound there from the foundation; its *Made by* gains `0181`.
- `docs/principles.md` loses the sentence that the discard of a render is spelled twice and the *Known breaks* bullet of the stage principle, whose breaks are this owner's.
- `docs/modules.md`, `docs/data-flow.md`, the READMEs of `isekai/foundation/` and `isekai/interface/` and the docstring of `isekai/interface/ui/app.py` name the owner; `tools.derive_imported_by` writes the derived rows.

## Tests

The change adds unit tests and no end-to-end run, and removes no test, so no table maps a deleted test. No existing test's assertion changes, and the move's phase changes no file under `tests/`. The pre-flight runs read the suite and change none of it.

| count | command | prints |
|---|---|---|
| cases added | `git grep -c -E "^def test_(a_withdrawn_failure_only\|a_nested_folder_under\|edit_discard_the_(owner\|verb_takes)\|the_verb_and_the_route)" -- tests/test_review.py tests/test_edit_session.py tests/test_ui_api.py` | `tests/test_review.py:2`, `tests/test_edit_session.py:6` and `tests/test_ui_api.py:1` |

The cases extend the files that already hold the delete's cases and reach their state by the same helpers ([T2](../../../CODING_STANDARDS.md#project-rules)); the twin is a step beside the route's own cases, over a copied library with no browser ([T1](../../../CODING_STANDARDS.md#baseline), [T6](../../../CODING_STANDARDS.md#baseline)).

## Dependencies

None.

## Risks / Trade-offs

- **The ranges of D5 rest on `0179`'s tip.** `0179` is built, not released, at this cut; a different base moves them, and a rescue re-fits them. After phase 2 the bodies sit in `isekai/foundation/discard.py`, and the plan check re-runs each range there: `discard_render` 44-73, `discard_edit` with its `_chain` 143-173, `_holds_render` 76-79, `withdraw` 82-140.
- **A thumbnail goes before its image.** A delete cut short leaves files with no thumbnail, which the page's view makes again; the other order cannot name the thumbnail.
- **`delete_render` reads the run from the path.** The route's address named the same run and version, and the twin case holds that the verb and the route leave one cache.
- **`_holds_render` is bound and read by no one.** It is a private name, bound for the old home as D1 says; a later version may drop the line.
- **The edit's path gains a thumbnail drop.** The verb's requirement says only the image's own thumbnail; if conformance holds that an edit's path has no requirement for it, that half becomes a card and the rest ships.

## Verdict

Ready to build, in the phases of [tasks](tasks.md).
