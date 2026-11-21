# The upload session — design

Move `Reader` and `Imports` from `isekai/pipeline/importing.py` to `isekai/interface/ui/uploads.py`, which reads the stage only through the module, so the stage leaves the long files and each injected failure still reaches. Verdict: feasible, in the phases of [tasks](tasks.md); the classes are copied first and leave the stage last, so each phase ends green.

## Context

`importing.py` holds the import stage: `read`, `verify`, `commit`, `cancel`, `sweep` and the previews. It also holds the app's upload session: `Reader`, which reads one open import's uploads in turn on a thread, and `Imports`, every open import of a library. Only the app calls those two: `create_app` builds `Imports`, `Surface` types it, and the staging routes call its methods.

Tests inject a failure by name: a test of the API replaces `importing.read`, and a test of the imports replaces `importing.commit`. A module that read either by `from … import` would not see the patch, so the session keeps calling them as `importing.read` and `importing.commit`.

```
before                                     after
pipeline/importing.py                      pipeline/importing.py
  read · verify · commit · cancel            read · verify · commit · cancel
  stage · sweep · previews                   stage · sweep · previews
  Reader · Imports   ◀── app calls           refuse_name · CLAIM  (were private)
                                           interface/ui/uploads.py
app.py ──▶ importing.Imports                 Reader · Imports ──▶ importing.<name>
surface.py ──▶ importing.Imports           app.py · surface.py ──▶ uploads.Imports
```

## Goals / Non-Goals

- Goal: `Reader` and `Imports` are defined in `uploads.py`, their lines unchanged but for the reads of [D1](#d1), and defined nowhere else.
- Goal: each read of the stage in `uploads.py` is `importing.<name>`, so a test that replaces `importing.read` or `importing.commit` reaches it.
- Goal: `importing.py` leaves the long files, and no row of `tests/test_ratchets.py` names it.
- Non-goal: a message, a state, a record or a parameter of the moved code; `Upload` and `State`, which stay so the page's file type keeps its module; `staged_file`, `verify`, `preview`, `STAGING` and `sweep`.
- Non-goal: a decision, a scenario, a spec delta, and any file under `ui/`, `tools/` or `evaluation/`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `uploads.py` holds `Reader`, `Imports` and the names only they read, and reads `importing` only as `importing.<name>` | tests replace `importing.read` and `importing.commit`, and a name bound by `from … import` does not see a patch | a `from isekai.pipeline.importing import read, commit`, which the patch misses; a re-export in `importing.py`, which makes the pipeline import the interface |
| [D2](#d2) | `_refuse_name` becomes `refuse_name` and `_CLAIM` becomes `CLAIM`, in `importing.py`, and `uploads.py` reads both through the module | `read` and `staged_file` still read both, and the session reads both from another layer | a copy of the name rule and of the lock, which each reader would have to keep equal; a private name read across modules; a new `unstage` function, which moves the lines of `remove` |
| [D3](#d3) | The lines that name `importing.Reader` or `importing.Imports` read `uploads`; so do the lines that patch `tempfile.mkdtemp` through `importing` | `Reader.put` is the one reader of `tempfile` in the stage, so `importing` stops importing it; the module object is the same, so the patch reaches the same function | an unused `import tempfile` kept in `importing.py`, which ruff fails; patching the standard library's `tempfile` by its own name, which changes a line's meaning for no gain |
| [D4](#d4) | Phases: the copy, the readers, the delete, the documents | the tests name `importing.Reader` and the app builds `importing.Imports`, so a delete before the readers move is red; the copy keeps the old classes until the new are proven | one phase of the whole move, which cannot be checked apart |
| [D5](#d5) | The long-file row of `importing.py` goes in the delete's phase, and the patched-module table does not change | the ratchet reads a row whose offender no longer offends as red, and the file is over its ceiling until the delete; `importing.py` is still patched, by name, for `read`, `commit`, `verify` and others | a row removed in the copy's phase, red there |
| [D6](#d6) | The standing mutants `PA-14` and `PA-15` take the path of `uploads.py` in the readers' phase, their text unchanged | a mutant is found by its path and its exact text, and from that phase the tests reach the new classes, so a mutant left in `importing.py` survives | a new mutant, or a mutant left on a copy no test reaches |
| [D7](#d7) | No decision is added or amended | no decision in force names the session's home; the documents that do are amended in phase 4 | a decision for a move that sets no rule |

### D1

`uploads.py` imports `queue`, `shutil`, `tempfile`, `threading`, `Callable`, `Iterable`, `Mapping`, `Path`, `Any`, `Refusal` and `importing`, and no web framework. It holds `_record`, `Reader`, `_UNREAD`, `_STAGED`, `_closed`, `_failed` and `Imports`, in the order they have in `importing.py`, each with its docstring and comments. The other names a class reads are the stage's, and each is read as `importing.<name>`:

| in | before | after |
|---|---|---|
| `_record`, `_set` | `state: Upload` | `state: importing.Upload` |
| `Reader.put` | `refuse_name(name)` | `importing.refuse_name(name)` |
| `Reader.remove` | `refuse_name(name)` and `with CLAIM:` | `importing.refuse_name(name)` and `with importing.CLAIM:` |
| `Reader._run` | `staged = read(held, self._staging, self._limit)` | `staged = importing.read(held, self._staging, self._limit)` |
| `Reader._run` | `state: Upload = staged.state` | `state: importing.Upload = staged.state` |
| `Imports.open` | `folder = stage(self._library)` | `folder = importing.stage(self._library)` |
| `Imports.commit` | `) -> Committed:` | `) -> importing.Committed:` |
| `Imports.commit` | `done = commit(folder, self._library, name, as_is, add=add)` | `done = importing.commit(folder, self._library, name, as_is, add=add)` |
| `Imports.cancel` | `cancel(folder)` | `importing.cancel(folder)` |

`ruff format` wraps `_record`'s and `_set`'s signatures. No other line differs. The mutants of [D6](#d6) find `            if unread:` and `        except BaseException:` with `            reader.unseal()` below it, both unchanged.

`ty` holds `importing.Upload` as it holds `Upload`. `tests/test_ratchets.py`'s `unread_patches` counts `importing.read` and `importing.commit` read as attributes of the bound module, so each patch of them stays read.

### D2

`refuse_name` keeps its body and docstring. `CLAIM` keeps its comment: held from picking a staged name until the file under it is written and verified. `read` and `staged_file` read the new names in `importing.py`. No test, document or other module reads either name by its old private spelling.

### D3

Every line of `tests/test_importing.py` that reads `importing.Reader`, `importing.Imports` or `importing.tempfile` reads `uploads` in its place, and the file imports `uploads` from `isekai.interface.ui`. `tests/test_ui_api.py` imports `isekai.interface.ui.uploads as uploads_module`, as it imports `importing_module`, and the lines naming `importing_module.Reader` and `importing_module.Imports` read it. The lines that read `importing.os`, `importing._clean`, `importing.commit` and each other name of the stage stay, since `commit` and `read` still read them. No assertion changes.

The ratchet counts a patch only when its target resolves to a module of the repository: `uploads.Reader`, `uploads.tempfile` and `importing.tempfile` resolve to none, so no row of the patched-module table moves.

### D4

| phase | what | the tests that hold it |
|---|---|---|
| 1 | `uploads.py` holds a copy, reading `importing`; `importing.py` keeps its classes and renames `_refuse_name` and `_CLAIM` | the suite, which still reaches the old classes |
| 2 | the app, the surface, the tests and the mutants `PA-14` and `PA-15` read the new classes | the suite and the mutants, now on `uploads.py` |
| 3 | the old classes, the imports only they read, the long-file row | the ratchets, the layers and the suite |
| 4 | the documents | `tests/test_docs.py` and the suite |

### D5

After the delete `importing.py` holds the stage alone, and the file is under the ceiling by the ratchet's own measure. `FILE_ROWS` is set to the rows left, whatever they are when the phase runs. `PATCHED_MODULES` keeps its row for `isekai.pipeline.importing`: `read`, `commit`, `verify`, `upload_limit`, `_clean` and `write_atomically` are still patched there.

### D6

| finding | text of | path now | path after |
|---|---|---|---|
| PA-14 | `Reader.seal`'s `if unread:` | `isekai/pipeline/importing.py` | `isekai/interface/ui/uploads.py` |
| PA-15 | `Imports.commit`'s unseal | `isekai/pipeline/importing.py` | `isekai/interface/ui/uploads.py` |

Each `find`, `replace`, `tests` and `why` is unchanged. The other mutants of `importing.py`, `PA-16a` to `PA-19`, hold text that stays.

### D7

`docs/decisions.md` names `importing.py` once, in [D68](../../../docs/decisions.md#d68--the-collections-names-and-the-sessions-read-side-are-foundationlibrarypy-re-bound-at-their-old-homes)'s *Accepts*, for the hand copy of `is_collection`'s test, which stays in `importing.py`. No decision names `Reader`, `Imports` or the session's home.

## Names

| names | module after | read by |
|---|---|---|
| `Reader`, `Imports`, `_record`, `_UNREAD`, `_STAGED`, `_closed`, `_failed` | `uploads.py` | `app.py`, `surface.py`, `tests/test_importing.py`, `tests/test_ui_api.py` |
| `refuse_name`, `CLAIM` | `importing.py` | `read`, `staged_file` and `uploads.py` |
| `read`, `commit`, `cancel`, `stage`, `Staged`, `Committed`, `Upload` | `importing.py` | `uploads.py`, as `importing.<name>` |
| `staged_file`, `preview`, `past_limit`, `verify`, `STAGING`, `upload_limit`, `sweep`, `UI_CONFIG` | `importing.py` | the staging and tattoo routes, `app.py`, `ui/__init__.py`, `ui/library.py`, the verbs, the tests |

## Tests

No test is added, deleted or merged, no assertion changes, and no end-to-end run is added. The test files change import lines and the lines named in [D3](#d3); `tests/test_ratchets.py` loses a row, `tests/mutants.json` re-points `PA-14` and `PA-15`, and `tests/test_docs.py` re-derives the tables.

| measure | command | before | after |
|---|---|---|---|
| tests in the import file | `git grep -c -e "^def test_" -- tests/test_importing.py` | `tests/test_importing.py:33` | `tests/test_importing.py:33` |
| tests in the API file | `git grep -c -e "^def test_" -- tests/test_ui_api.py` | `tests/test_ui_api.py:115` | `tests/test_ui_api.py:115` |
| tests in the ratchets file | `git grep -c -e "^def test_" -- tests/test_ratchets.py` | `tests/test_ratchets.py:15` | `tests/test_ratchets.py:15` |

The proof is the suite, the standing mutants, `tests/test_ratchets.py`, `tests/test_layers.py` and `tests/test_derive_wire.py`, which holds `ui/src/wire.ts`. The code moves as it is, so no range of it is run by `tools.mutate` ahead of the move: the whole import file reaches it, and `PA-14` and `PA-15` replay on its new home. No test is deleted or merged, so no `I16` table is due.

## Dependencies

None.

## Risks / Trade-offs

- A read of the stage by a bare name in `uploads.py` breaks a patch without failing a test of its own. `ruff` finds an undefined name, and the first phase checks that `uploads.py` imports no name from `importing`.
- Until phase 3, each class is defined in both modules. From phase 2 the suite reaches only the new, and the old is dead code that no module reads.
- `ruff format` may wrap a line the table of [D1](#d1) gives on one line. That is a layout, not a change.
- The rows of `tests/test_ratchets.py` and the paths of `tests/mutants.json` are named by their key and text, never by line, since earlier versions of the chain edit both.

## Verdict

Feasible. Each phase ends with its tests passing; the old session leaves the stage once nothing reads it.
