# The evaluator seams — design

Each collaborator a test patched in `evaluation/` becomes a keyword parameter that defaults to what the product uses. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The tests patch names of the evaluator's own modules, and the ratchet lists a row for each module ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)):

| module | the patched name | where it is read | the tests that patch it |
|---|---|---|---|
| `evaluation.__main__` | `_embedder` | `main`, `evaluation/__main__.py` | `tests/test_evaluation_cli.py` |
| `evaluation.recall` | `_reader` | `main`, `evaluation/recall.py` | `_run` of `tests/test_recall_cli.py` |
| `evaluation.eval_models` | `load_eval_manifest` | `_embedder`, `evaluation/__main__.py` | `tests/test_eval_manifest.py` |

The entry points are not imported by the product, so a parameter changes no caller: `python -m evaluation` and `python -m evaluation.recall` call `main(sys.argv[1:])`.

## Goals / Non-Goals

Goals:

- The rows of the modules in the table above leave `PATCHED_MODULES`, and `PATCHED_ROWS` is set to 21.
- Each test passes a fake where it patched, and no assertion changes.

Non-goals:

- A `Wiring`-style object or a class for the collaborators: a parameter is the smallest seam that removes the row.
- The patches of `isekai.boundary.wd14` and `evaluation.face`, which stay rows of the table.
- Any decision: [D61](../../../docs/decisions.md#d61--what-a-test-replaces-in-the-server-is-a-parameter-of-create_app) is the server's, and this change adds none.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the seams are keyword-only parameters, each defaulting to the product's own function | a caller that passes nothing runs the product's code, so no entry point changes | a module-level hook the test sets, which is the patch again |
| [D2](#d2) | the manifest seam is `manifest: Manifest \| None = None`, read through `load_eval_manifest()` when `None` | the default reads the file on the call, as the body does now, and no file is read at import | `manifest: Manifest = load_eval_manifest()`, which reads the file at import |
| [D3](#d3) | a phase for each seam, each ending with its row gone | each phase is green alone, and a row's removal is the proof that its patch is gone | one phase for all three, which hides which seam broke |

### D1

`main(argv, *, embedder: Callable[[Path], Embed] = _embedder)` and `main(argv, *, reader: Callable[[Path], tuple[Read, dict[str, str]]] = _reader)`. `_embedder` and `_reader` are defined above `main` in their files, so the default binds at definition. The body calls the parameter where it called the module's name.

### D2

`_embedder(models, *, manifest=)` reads `load_eval_manifest()` only when `manifest` is `None`, then goes on with `shared_with_the_graph` as now. The refusal a shared entry gives is the same text.

### D3

The order is the entry points first, the manifest last: the manifest seam sits inside `_embedder`, whose own tests the first phase leaves as they are.

## Tests

The change adds and removes no test. It moves a fake from a patch to an argument, so the count of tests is the base's.

| measure | count | command |
|---|---|---|
| tests in `tests/test_evaluation_cli.py` | 14 | `git grep -c -e "^def test_" -- tests/test_evaluation_cli.py` |
| tests in `tests/test_recall_cli.py` | 13 | `git grep -c -e "^def test_" -- tests/test_recall_cli.py` |
| tests in `tests/test_eval_manifest.py` | 12 | `git grep -c -e "^def test_" -- tests/test_eval_manifest.py` |
| patches of the evaluator's modules, before | 5, 1 and 2 | `git grep -c -E "setattr\((entry\|recall\|eval_models), " -- tests/test_evaluation_cli.py tests/test_recall_cli.py tests/test_eval_manifest.py` |
| patches of the evaluator's modules, after | 0 | the same command, which prints nothing |
| tests in `tests/test_ratchets.py` | the base's | none added or removed: the edit is to the rows of its tables, which `test_no_patched_module_is_unlisted` reads |
| end-to-end runs added | 0 | none: each test is a unit or an integration test of an entry point, at the lowest layer that holds it (`T1`) |

No test is deleted or merged, so there is no `I16` table. The patch of `isekai.boundary.wd14`'s `open_session` in `tests/test_recall_cli.py` stays: it is a row of the table this change leaves.

## Dependencies

None.

## Risks / Trade-offs

- A default binds when `main` is defined, so a test that still patches `_embedder` or `_reader` after its phase would run the real one. The phase's `Verify:` finds each remaining patch.
- A test that took `monkeypatch` only for the patch keeps an unused fixture if it is not dropped. Each phase names the tests and a `Verify:` finds the helper's old call.

## Verdict

Ready to build. Small phases, each ending with a row gone.
