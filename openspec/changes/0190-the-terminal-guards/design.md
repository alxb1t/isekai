# The terminal guards — design

A render session holds the folder beside its runs root, and the app already refuses while it does. This version gives the terminal's discard and cancel the same refusal, and stops a delete leaving a thumbnail behind. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

A render session writes its record to `<runs root>/../sessions/<id>.json` and holds the lock of `<id>.lock` until it ends, for any runs root it renders (`isekai/interface/render.py`). `collection_held(folder)` in `isekai/foundation/library.py` reads those locks. The app's guard, `Surface.rendering`, asks it for a collection.

The terminal's guards have gaps:

```
discard        render_running(run) ─▶ no, unless the root is named runs and its parent holds sources/
approve --cancel   (no guard)       ─▶ cancel(run, flow) at once
after          render_running(run) ─▶ collection_held(the folder beside the run's root)
               approve --cancel    ─▶ render_running(run) ─▶ refuse, else cancel(run, flow)
```

`delete_render` and `delete_edit` in `isekai/foundation/discard.py` drop each thumbnail while its image is a file, then delete the files. A thumbnail requested in between is rebuilt under the same name and nothing deletes it (card `0181·S1`).

## Goals / Non-Goals

- Goal: `isekai discard` of a render and of an edit refuses while a session holds the run's runs root, a collection's or not.
- Goal: `isekai approve --cancel` refuses each run whose runs root a session holds, with the app's sentence, and cancels the others.
- Goal: a delete leaves no thumbnail of an image that went.
- Non-Goals: see [proposal](proposal.md#not-in-this-change). In short, the app's guard, the gap between a check and a delete, the window before a record opens and a lock an act holds are not here.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `render_running` asks the folder beside the run's runs root, whatever the root is named and holds | a session writes its record beside any runs root, so the question is one function of the root | keeping the collection test, which is the defect; a second function for plain roots |
| [D2](#d2) | the verb asks `render_running` in the approve builder, before the stage's cancel | the discard asks in the verb and the app in its route; the stage's cancel stays an act that decides nothing about a render | a guard inside `cancel`, which every caller would pay |
| [D3](#d3) | `named_thumbnail` joins the library, and the owner names each thumbnail first, drops them, deletes the files, then unlinks any named one that came back | a thumbnail is named by its image's digest, so the names are read while the images are files; dropping only afterwards leaves an orphan when a delete is cut short | the card's fix alone, which has the same names but no first drop |
| [D4](#d4) | the spec delta changes the text of the cancel's requirement, the discard's and the edit's, and adds a scenario under each | no requirement demands either guard, so the sentences change and each gets a scenario | a patch, which may add none; a new requirement |
| [D5](#d5) | the cases come first, fail on the missing guard, and patch no first-party module | a case that fails before the switch proves the switch; a patch would add a row to the patch ratchet | patching `render_running`, which is what a guard test must not do |
| [D6](#d6) | D74 records the guards; D72 names the second drop and the guards' new home; D68 names `named_thumbnail` | the documents a version makes false are amended in its diff | a note in the changelog alone |
| [D7](#d7) | a mutation run follows each phase's lines, on the cases that reach them | the guards are one-line conditions a survivor could hide in | the standing replay alone |

### D1

`render_running` ends on one line. Its docstring and its body are exactly this, so a mutation range is known:

```python
def render_running(run: Run) -> bool:
    """Return whether a render process holds the runs root `run` sits in.

    A session writes its record beside any runs root, a collection's or not, so
    the folder the root sits in is asked. Liveness alone is read, from each
    session's lock, so a record that does not read still counts.
    e.g. `<dir>/runs/<id>` with `<dir>/sessions/<t>.lock` locked -> True
    """
    return collection_held(run.path.absolute().parent.parent)
```

The `.absolute()` stays: a run named by a relative path, its root the working directory, has `Path("id").parent.parent` equal to `.`, which is the root and not the folder beside it. `collection_held` and the app's guard do not change. `isekai/interface/ui/__init__.py` still wraps the function for `discard`, as [D68](../../../docs/decisions.md#d68--the-collections-names-and-the-sessions-read-side-are-foundationlibrarypy-re-bound-at-their-old-homes) accepts.

### D2

`isekai/interface/verbs/runner.py` imports `render_running` from `isekai.foundation.library`, between the imports of `flow` and `refusal`. The foundation module is on `python -m isekai`'s import graph, as `discard.py` already imports it; the UI package is off it. The cancel branch of `_approve_step`'s `approve_flow` becomes:

```python
        if item.args.cancel:
            if render_running(run):
                raise Refusal(
                    f"{run.id}: A render session is running. Wait for it to end, "
                    "then cancel the approval again."
                )
            left, changed = cancel_approval(run, name)
```

The sentence is the app's, [`post_cancel`](../../../isekai/interface/ui/routes/reviewing.py)'s, with the run's id first as the review stage's own refusals have it. The refusal rides `_reported` and `across` as any other, so each run is answered on its own and the progress line says `refused`. A run named by an absolute path is read under any root, which is how a case holds one run and not another.

### D3

`isekai/foundation/library.py` gains `named_thumbnail(run, image)`, after `thumbnail_of`. It is the rule `drop_thumbnails` held inline, so `drop_thumbnails` calls it and its answers do not change:

```python
def named_thumbnail(run: Run, image: Path) -> Path | None:
    """Return where `image`'s thumbnail sits in its library's cache, made or not.

    None for a run outside a collection, which has no library. The image must
    exist, since its bytes name the file.
    e.g. `<lib>/b/runs/<id>/…/001/42.png` -> `<lib>/.cache/<digest>/…/001/42.<d>.jpg`
    """
    folder = run.path.absolute()
    if not (folder.parent.name == RUNS and is_collection(folder.parent.parent)):
        return None
    return thumbnail_of(folder.parents[2], run, image)
```

`drop_thumbnails` keeps its signature and docstring and ends on `own = named_thumbnail(run, image)`, `if own is None or not own.is_file(): return []`, `own.unlink()`, `return [own]`. The owner no longer calls it; `isekai/interface/ui/library.py` still re-binds it, and its case in `tests/test_ui_library.py` still reads it.

`isekai/foundation/discard.py` imports `Callable` and `Iterable` from `collections.abc` and `named_thumbnail` in place of `drop_thumbnails`. It gains the helpers `_edit_images`, `_named`, `_unlinked` and `_deleted` after `Deleted`, and `delete_render` and `delete_edit` become:

```python
def _edit_images(group: Path, seed: int, numbers: Iterable[int]) -> list[Path]:
    """Return the images of edits `numbers` of `seed` that are files, in order."""
    return [
        own
        for number in numbers
        if (own := edit_files(group, seed, number)[0]).is_file()
    ]


def _named(run: Run, images: Iterable[Path]) -> list[Path]:
    """Return where each of `images`' thumbnails sits, made or not.

    A run outside a collection has no library, so no thumbnail. The images must still
    be files: their bytes name the thumbnails.
    """
    names = (named_thumbnail(run, image) for image in images)
    return [name for name in names if name is not None]


def _unlinked(names: Iterable[Path]) -> list[Path]:
    """Delete each of `names` that is a file; return those, in order."""
    found = [name for name in names if name.is_file()]
    for name in found:
        name.unlink()
    return found


def _deleted(names: list[Path], delete: Callable[[], list[Path]]) -> Deleted:
    """Return what `delete` removed, with the thumbnails of `names` unlinked twice.

    Once before the files go, and once after, for a thumbnail a request rebuilt in
    between: it names an image that is gone, and nothing else would delete it.
    """
    dropped = _unlinked(names)
    files = delete()
    late = [name for name in _unlinked(names) if name not in dropped]
    return Deleted(files, [*dropped, *late])


def delete_render(image: Path) -> Deleted:
    """Delete a render, its edits, their thumbnails and the approval its last leaves.

    The path is checked first, so one naming no render deletes nothing. The thumbnails
    go while their images are files: the render's, then each edit's in number order.
    e.g. outputs/001/42.png, with 42.edit-1.png
    -> files [..., 42.png, ...], thumbnails [42, 42.edit-1]
    """
    ref = rendered_at(image)
    group = image.absolute().parent
    edits = _edit_images(group, ref.seed, edit_numbers(group, ref.seed))
    return _deleted(
        _named(ref.run, [image, *edits]),
        lambda: [*discard_render(image), *withdraw(ref.run, ref.flow, ref.version)],
    )


def delete_edit(image: Path) -> Deleted:
    """Delete an edit and every edit made from it, with each one's thumbnail.

    An edit whose record cannot be read is refused before anything is deleted.
    e.g. 42.edit-1.png, with 42.edit-2 made from it -> thumbnails [edit-1, edit-2]
    """
    ref = edit_at(image)
    group = image.absolute().parent
    numbers = _chain(group, ref.seed, ref.k)
    return _deleted(
        _named(ref.run, _edit_images(group, ref.seed, numbers)),
        lambda: delete_edits(group, ref.seed, numbers),
    )
```

The module docstring's first paragraph keeps its length, so no line number below it moves:

```
`delete_render` and `delete_edit` name the thumbnail of every image that goes while it
is a file, drop them, delete the files and, for a render, the approval its last render
leaves (D72), then unlink any named thumbnail that came back. The bodies they call are
here too, bound back at the stages that held them.
```

The order the existing cases hold stays: the render's thumbnail, then each edit's in number order, printed after the run's files; an unreadable chain is refused before any name is read. A thumbnail that was dropped and came back is returned once, in the first group.

### D4

`specs/cli/spec.md` holds a `## MODIFIED Requirements` block for the cancel's requirement and one for the discard's, each its living text as it stands with the new sentence and a new scenario; `specs/edit/spec.md` holds one for the edit's discard. The cancel's and the discard's paragraphs say "the app's" where they compare with the app's guard.

| scenario key | case | layer |
|---|---|---|
| `cli:approve-cancel:a-running-render-refuses-it` | `test_approve_cancel_is_refused_under_a_runs_root_a_session_holds` | unit |
| `cli:discard:a-session-beside-a-plain-runs-root-refuses-it` | `test_discard_is_refused_beside_a_session_under_a_plain_runs_root` | unit |
| `edit:discard:a-session-beside-a-plain-runs-root-refuses-it` | `test_edit_discard_a_session_under_a_plain_runs_root_refuses_an_edits_path` | unit |

### D5

Each case writes `<root>/../sessions/<id>.json` and locks its `.lock` file through a second open file with `fcntl.flock(held, fcntl.LOCK_EX)`, as the neighbouring discard cases do, and builds its run under a root with no `sources/`. The cancel's case holds a run under one root and names a second run, under another root, by its absolute path; it asserts the held run's approval on disk and the other a draft again. The discard and edit cases assert the exit, the sentence and an unchanged `tree(...)`.

The rule's case in `tests/test_ui_library.py` is `spec_exempt`, a structural test of a foundation function, like its neighbours: a plain root, a collection's root, a free lock, a root the working directory names by a relative path.

The thumbnail's case in `tests/test_edit_session.py` is `spec_exempt` too. It wraps `Path.unlink` through `monkeypatch.setattr(Path, "unlink", …)` so that unlinking the render's image rewrites its dropped thumbnail, a request landing in the gap. `pathlib` is no first-party module, so no ratchet row is added. Before the change the thumbnail is left; after it, gone and returned once.

### D6

`docs/decisions.md` gains D74 after D73, in the page's form:

```markdown
### D74 · A terminal delete or cancel refuses beside a live render

**`render_running(run)` of `isekai/foundation/library.py` reads the sessions beside the run's runs root, whether or not the root sits in a collection, and `isekai discard` and `isekai approve --cancel` refuse a run while it answers yes. A session writes its record beside any runs root, so the question is one function of the root.**

- **Why:** the verb's guard answered no for a root outside a collection, and `approve --cancel` asked nothing, so a delete or a cancel could run beside a live render.
- **Accepts:** the gap between a check and a delete, the window before a record opens and a lock an act holds stay as they are, and the review stage's cancel decides nothing about a render. Reopen when a lock both a session and an act take is added.
- **Made by:** `0190`.
```

D72's bold paragraph becomes: `**`isekai/foundation/discard.py` holds `delete_render(image)` and `delete_edit(image)`, which name the thumbnail of every image that goes while it is still a file, drop them, delete the files and, for a render, the approval its last render leaves, then unlink any named thumbnail that came back, and return `Deleted(files, thumbnails)`. …`** The rest of the paragraph is as it was. Its *Why* ends `so it is named before its image goes, and one rebuilt in between is unlinked by that name.` Its *Accepts* line becomes: `the guards stay with the acts: the app's, which refuses while its render slot runs or a session holds the collection (0182), and the verbs', which refuse while a session holds the run's runs root (D74). `_derived`, `review.discard` and `tattoos.remove` stay where they are. Reopen when a delete's guards move into the owner.` Its *Made by* gains `0190`. D68's bold paragraph names `named_thumbnail` between `thumbnail_of` and `drop_thumbnails`, and its *Made by* gains `0190`; its *Accepts* line is as it was.

The `library.py` and `discard.py` rows of `isekai/foundation/README.md` say `named_thumbnail` and the second drop. The `verbs/runner.py` and `verbs/drafts.py` rows of `isekai/interface/README.md` say the cancel and the discard refuse beside a render session. The `--cancel` bullet of `README.md` and the sentence of `docs/edit-tattoo.md` that ends "holds the collection" say the runs root.

### D7

Each phase's moved lines get one `tools.mutate` run a range, on the tests that reach them: the rule's line, the cancel's branch, and the new and changed lines of the library and the owner. A survivor is killed by a further assertion in that phase's cases. `tools.mutate` mutates only a node that starts and ends on one line, so the cancel's guard, an `if` over a call and a `raise` over four lines, holds no site: its run is not made, and its one mutant, the cancel not refused, is the case of D5 that fails before the guard stands.

## Tests

Added tests are unit tests: a case of the rule in `tests/test_ui_library.py`, the cases of [D4](#d4) in `tests/test_pipeline_cli.py` and `tests/test_edit_session.py`, and the thumbnail's case in `tests/test_edit_session.py`. No end-to-end test is added or removed, so no engine runs any. Each count is the command's output.

| layer | measure | command | before | after |
|---|---|---|---|---|
| unit | cases of the verbs' scenarios in the CLI file | `git grep -h -c -e "a-session-beside-a-plain-runs-root-refuses-it" -e "cli:approve-cancel:a-running-render-refuses-it" -- tests/test_pipeline_cli.py` | nothing | `2` |
| unit | the edit's scenario case | `git grep -h -c -F "edit:discard:a-session-beside-a-plain-runs-root-refuses-it" -- tests/test_edit_session.py` | nothing | `1` |
| unit | the rule's case | `git grep -h -c -e "^def test_a_run_is_held_by_a_session_beside_its_runs_root" -- tests/test_ui_library.py` | nothing | `1` |
| unit | the thumbnail's case | `git grep -h -c -e "^def test_edit_discard_the_owner_unlinks_a_thumbnail_rebuilt" -- tests/test_edit_session.py` | nothing | `1` |
| e2e | runs added | none: no page code changes | — | — |

No test is deleted or merged, so there is no `I16` table. No existing test's assertion changes.

## Dependencies

None.

## Risks / Trade-offs

- `render_running` now reads the session locks of the folder beside any runs root, so a plain root pays the read a collection's did. The default root's folder holds no records until a session renders it.
- A session that starts after the check, and the window before its record opens, still pass the guard. They need a lock both a session and an act take, which is *the session queue*'s.
- `drop_thumbnails` loses its one product caller, the owner. It stays for `isekai/interface/ui/library.py`'s re-binding and its case; removing it is a later paydown, and the owner now reads the same rule through `named_thumbnail`.
- A thumbnail whose image is not a file when the names are read has no name, so none is unlinked late. An edit's image that is not a file has no thumbnail to leave.

## Verdict

The change is the rule, the cancel's guard, the second drop, their scenarios and cases, and the documents they make false. It is ready to build in the phases of [tasks](tasks.md).
