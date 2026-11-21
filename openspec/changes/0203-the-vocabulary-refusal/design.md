# The vocabulary refusal — design

`load_vocabulary` turns a `DigestMismatch` into a `Refusal` worded as `tagger_for`'s, one case holds it, and the prose that said otherwise is corrected. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`load_vocabulary` resolves the label index through `provision.resolve`, which hashes the file and raises `DigestMismatch` when the bytes differ (`isekai/boundary/provision.py:275-286`, `isekai/boundary/provision.py:342-364`). The function catches `UnknownArtifact` and `FileNotFoundError` and lets the mismatch through (`isekai/interface/wiring.py:332-344`). No front end handles it, though [the tagging requirement](../../specs/tagging/spec.md) says the system refuses naming the fetch when the bytes differ.

`tagger_for` in the same module already turns the mismatch of the tagger's model and label index into a `Refusal` (`isekai/interface/wiring.py:166-172`), and `proposer_of` does the same for the placement models (`isekai/interface/wiring.py:223-231`). `DigestMismatch` is imported at module scope there (`isekai/interface/wiring.py:31`), and `ollama.py` imports `load_manifest` from `provision` at module scope (`isekai/boundary/ollama.py:57`). So the docstring's reason for `load_vocabulary`'s lazy import, that it keeps `provision` off the entry point's graph, is false (`isekai/interface/wiring.py:318-319`).

A patch meets each condition of [CONTRIBUTING](../../../CONTRIBUTING.md): no format version moves; the fix is required by the existing requirement, so a scenario is added under it and no requirement; no verb or flag is deprecated; no sheet field, prompt or image changes for the same inputs, since only a damaged file's outcome moves, from a traceback to a refusal.

## Goals / Non-Goals

- **Goals:** a label index whose bytes differ is refused by `load_vocabulary`, naming the file, both digests and the fetch; a case fails first and holds it; the docstring and the principles say what is true.
- **Non-Goals:** a change to `wd14.verified_paths` or `tagger_for`; a move of the import to module scope; a new decision; a changed default of `manifest`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `load_vocabulary` adds a third `except` to its existing `try`, binding `altered`, and raises a `Refusal` in the words of `tagger_for` | Q328: the requirement refuses a label index whose bytes differ; the fix sits in the wiring, beside the refusals the function already makes | a catch in each front end, which composes twice a rule the wiring owns; a shared helper, which edits `tagger_for` and its standing mutant |
| [D2](#d2) | `wd14.verified_paths` keeps raising the raw mismatch | Q328: a test holds that `wd14` itself raises it, and `tagger_for` turns it into a refusal | a refusal in the boundary, which changes the tagger's route for no gain |
| [D3](#d3) | The docstring's reason for the lazy import is replaced by the true one; the import and the keyword's defaults stay | Q329: a comment that states a wrong reason misleads the next change | moving the import to module scope, which edits the lazy edges `docs/modules.md` lists |
| [D4](#d4) | The case and the refusal are one phase, and the mutation run before the edit is its first task | C31: a case that fails first leaves the gate red until the fix, so they cannot be green apart | the brief's separate case phase, which ends on a red gate |
| [D5](#d5) | The spec delta is a MODIFIED block holding the requirement's text as it stands, its existing scenarios and one more | CONTRIBUTING: a patch may add a scenario under an existing requirement and may not add a requirement | an ADDED requirement for the damaged index |

### D1

The clause is added after `except FileNotFoundError` in the `try` that holds `resolve`:

```python
    except DigestMismatch as altered:
        raise Refusal(
            f"{altered}; delete that file, run `{VOCABULARY_REMEDY}`, then this "
            "command again"
        ) from altered
```

The words are `tagger_for`'s, so one damaged file reads the same from either verb. `DigestMismatch` is already imported at module scope, and `VOCABULARY_REMEDY` is already one of the module's imports. The binding is `altered`, so `except DigestMismatch as swapped` still occurs once in the module, which is where the standing mutant BD-1b finds its text (its entry in `tests/mutants.json`).

### D2

`tests/test_wd14.py` holds that `verified_paths` leaves the mismatch a `DigestMismatch`, for the label index and for the model (`tests/test_wd14.py:224-242`). The case of this change adds no test there.

### D3

The sentence that starts `` `provision` is imported here rather than at module scope`` is replaced by:

```
    `provision` is on `python -m isekai`'s import graph already, through `ollama.py`
    and this module's own `DigestMismatch`; its names are read here, at the call, as
    `wd14.verified_paths` reads its own.
```

The sentence `It lives here because `shared` only parses: the boundary verifies, and the front end composes the two.` stays. The docstring also gains the sentence `Bytes that differ from the pin are a `Refusal` naming the file and the fetch, as `tagger_for`'s are.`, after the sentence on the digest check.

### D4

The pre-flight of [CONTRIBUTING](../../../CONTRIBUTING.md) runs `tools.mutate` over the lines of `load_vocabulary` before the edit and over the same lines after it. The copy it works in takes the working tree's tracked files, so the case, once added to its tracked file, is read by the run before the phase's commit.

A survivor of the run before the edit is the baseline: it sits in lines the change does not touch, and the commit body lists it. A survivor after the edit that the baseline does not list is killed by an assertion in the case, or named equivalent in the commit body.

### D5

The delta repeats the requirement's paragraph and its existing scenarios word for word. Its new scenario carries the key `tagging:pin:a-damaged-label-index-is-refused-when-the-vocabulary-loads`, which the case binds. The release folds the scenario into `openspec/specs/tagging/spec.md`.

## Tests

The change adds one unit test and removes none. Its case plants a label index of other bytes under a temporary models directory and loads the tracked manifest's vocabulary. No end-to-end run is added ([T1](../../../CODING_STANDARDS.md#baseline): the lowest layer that can fail).

| layer | tests before and after | command |
|---|---|---|
| unit, `tests/test_vocabulary_manifest.py` | the count rises by the one case | `git grep -c -F "def test_" -- tests/test_vocabulary_manifest.py` prints the path and `18` at the cut, `19` after the build |
| unit, `tests/test_wd14.py` | unchanged | `git grep -c -F "def test_" -- tests/test_wd14.py` prints the same count before and after |

The case, in the style of its neighbour `test_an_unprovisioned_vocabulary_refuses_naming_the_command`:

```python
@pytest.mark.spec("tagging:pin:a-damaged-label-index-is-refused-when-the-vocabulary-loads")
def test_a_label_index_whose_bytes_differ_is_refused_naming_the_fetch(
    tmp_path: Path,
) -> None:
    planted = tmp_path / VOCABULARY
    planted.parent.mkdir(parents=True)
    planted.write_bytes(b"other bytes")

    with pytest.raises(Refusal) as refused:
        load_vocabulary(tmp_path)

    message = str(refused.value)
    assert f"SHA-256 mismatch for {planted}" in message
    assert (
        "delete that file, run `uv run python -m isekai.boundary.provision fetch "
        "config/vocabulary.json`, then this command again"
    ) in message
```

Before the fix the call raises `DigestMismatch`, which is no `Refusal`, so the case fails. No test is deleted or merged, so there is no `I16` table.

## Dependencies

None.

## Risks / Trade-offs

- **The case passes before the fix** → the premise is false: a **HALT CHECK** stops the build, and a rescue reads where the mismatch is caught.
- **A mutant survives in the new clause** → an assertion in the case kills it ([D4](#d4)); the message's file and its remedy are both asserted for that reason.
- **The `swapped` mutant text occurs twice** → the standing mutants fail to find their line: [D1](#d1) binds another name, and a task checks the count.

## Verdict

Ready to build, in the phases of [tasks](tasks.md): the refusal with its case, then the documents.
