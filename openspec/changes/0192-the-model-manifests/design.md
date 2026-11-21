# The model manifests — design

A model opener takes its manifest's path and `unpack.main` its fetcher, so no test patches either, and the row of `unpack` leaves the ratchet. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Each model opener reads a manifest by a name a test replaces. The tagger and the vocabulary read `VOCABULARY_MANIFEST_PATH` through `provision.load_manifest`; the pose finder and the segmenter read `unpack.PLACEMENT_MANIFEST_PATH`. Tests patch `provision.load_manifest`, `provision.VOCABULARY_MANIFEST_PATH` and `unpack.PLACEMENT_MANIFEST_PATH` to point them at a manifest of their own. `unpack.main` builds a `HuggingFaceFetcher`, which a test replaces.

The patch ratchet counts a patch when the module binds the name at its top level, and holds the rows, not the patches: a row with no patch is red, so a row leaves in the phase of its last patch. `provision.py` is copied into the pod image and does not change.

```
before:  test ──setattr──▶ provision.load_manifest ◀── wd14.verified_paths
         test ──setattr──▶ unpack.PLACEMENT_MANIFEST_PATH ◀── pose / sam2
         test ──setattr──▶ unpack.HuggingFaceFetcher ◀── unpack.main
after:   test ──manifest=<path>──▶ the opener
         test ──fetcher=<factory>──▶ unpack.main
```

## Goals / Non-Goals

- Goal: no test patches `provision.VOCABULARY_MANIFEST_PATH`, `unpack.PLACEMENT_MANIFEST_PATH` or `unpack.HuggingFaceFetcher`, and a patch of `provision.load_manifest` stays only in the tripwires.
- Goal: the row `isekai.boundary.unpack` is gone from `PATCHED_MODULES`.
- Goal: every keyword defaults to what the product reads today, so no caller changes and no printed byte moves.
- Non-goal: `provision.py`, its tripwires and its recording spy.
- Non-goal: a refusal for a damaged vocabulary, or a table of manifests.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `manifest=` is a keyword-only path on `wd14.verified_paths`, `wd14.open_session`, `wiring.load_vocabulary`, `pose.verified_paths`, `pose.open_pose` and `sam2.open_segmenter`; `wd14` and `wiring` default it to `None` and read the tracked path when it is `None` | a test already holds the path; `wd14` and `wiring` import `provision` inside the function to stay off `python -m isekai`'s import graph, so a module-level default would import it | a default `VOCABULARY_MANIFEST_PATH` at module level: it imports `provision` at import and turns the tripwire red |
| [D2](#d2) | `unpack.main(argv, *, fetcher=HuggingFaceFetcher)`, a factory called once | the test already passes a factory, and a default that is the class needs no `None` branch | a `Fetcher` instance as the default: a call in a default argument |
| [D3](#d3) | Each test that patched a manifest or the fetcher passes it; the tripwires and the recording spy stay patched | the tripwires prove `provision` is not reached at import and cannot be parameters; the spy replaces `provision.fetch` under `provision.main`, which does not change | a keyword on `provision.main`: the file is frozen into the image |
| [D4](#d4) | The row `isekai.boundary.unpack` leaves `PATCHED_MODULES` in the phase of the last patch, and `PATCHED_ROWS` is 17 | a row with no patch is red, and a row with a patch must stay | a phase for the ratchet alone: it would be red between the last patch and the row |
| [D5](#d5) | The *Known breaks* of *A component is a contract* names each module `PATCHED_MODULES` still lists, with its reason | the sentence that named them all by the list's name gave no reason, and the list is what a reader needs | a new principle: no rule changes |
| [D6](#d6) | The standing mutants `BD-1` and `BD-10b` are re-pointed to the edited lines of `wd14.py` | each finds its line by text, and the lines change | leaving them: the replay stops on a find that is gone |
| [D7](#d7) | One case is added: `unpack.main` defaults to the Hugging Face fetcher. No decision is added or amended | with the patch gone, no case reaches the default, and a mutant of it would survive | none: the version moves what a test passes, not what it proves |

### D1

`wd14.verified_paths` and `wiring.load_vocabulary` read the manifest through `provision`, imported inside the function. The loaded manifest takes the name `declared`, since `manifest` is now the path.

```python
def verified_paths(
    models_dir: Path = DEFAULT_MODELS_DIR, *, manifest: Path | None = None
) -> tuple[Path, Path, dict[str, DigestRecord]]:
    ...
    source = VOCABULARY_MANIFEST_PATH if manifest is None else manifest
    declared = load_manifest(source)
    ...  # resolve(dest, models_dir, declared), undeclared(dest, source), entry_for(declared, dest)
```

`wd14.open_session(models_dir=DEFAULT_MODELS_DIR, *, manifest=None)` calls `verified_paths(models_dir, manifest=manifest)`. `wiring.load_vocabulary` has the same lines and the same names: `source` names the path in its refusal, `declared` is passed to `resolve` and `entry_for`. A refusal for an undeclared artifact names the path it was given.

`pose` and `sam2` import `unpack` at module level already, so their default is the constant itself:

```python
def verified_paths(
    models_dir: Path = DEFAULT_MODELS_DIR, *, manifest: Path = PLACEMENT_MANIFEST_PATH
) -> tuple[Path, Path]:
    declared = provision.load_manifest(manifest)
    ...  # provision.resolve(dest, models_dir, declared)
```

`open_pose(models_dir, runtime, *, manifest=PLACEMENT_MANIFEST_PATH)` and `open_segmenter(models_dir, runtime, *, manifest=PLACEMENT_MANIFEST_PATH)` pass it on, and `open_segmenter` reads `declared` with `unpack.resolve_member`. `pose.py` imports the constant beside `PLACEMENT_REMEDY` and no longer imports the module `unpack`; `sam2.py` still calls `unpack.resolve_member`, so it keeps both. The wiring's `Proposers` and `tagger_for` call these with no argument, so the defaults are what a verb calls.

### D2

```python
def main(
    argv: list[str], *, fetcher: Callable[[], Fetcher] = HuggingFaceFetcher
) -> int:
    args = _parser().parse_args(argv)
    source = PLACEMENT_MANIFEST_PATH if args.manifest is None else Path(args.manifest)
    return fetch(provision.load_manifest(source), args.models_dir, fetcher())
```

`Callable` and `Fetcher` are imported by `unpack.py` already. `python -m isekai.boundary.unpack` still calls `main(sys.argv[1:])`.

### D3

| patch | before | after |
|---|---|---|
| `provision.load_manifest` in the label-index, digest and path cases of `tests/test_wd14.py` and in the opener cases of `tests/test_wd14_runtime.py` | returns a dict | `manifest=` names a file the case wrote |
| `provision.VOCABULARY_MANIFEST_PATH` in `tests/test_vocabulary_manifest.py` | points the tracked path at a copy | `manifest=` names the copy |
| `unpack.PLACEMENT_MANIFEST_PATH` in `tests/test_pose.py` and `tests/test_sam2.py` | points the constant at a file | `manifest=` names the file |
| `unpack.HuggingFaceFetcher` in `tests/test_provision_unpack.py` | returns a fake | `fetcher=` is the same lambda |
| `provision.load_manifest` and `provision.resolve` in the tripwires of `tests/test_wd14.py` | refuse | unchanged |
| `provision.fetch` in `tests/fakes.py` | records | unchanged |

### D4

The row `"isekai.boundary.unpack": 3,` and the count `PATCHED_ROWS = 17` change in phase 2, which removes the last patch of the module. The rows of `isekai.boundary.provision` and `isekai.boundary.wd14` stay: the tripwires and the spy patch `provision`, and the recall case and the runtime cases patch `wd14`'s opener and its import seam.

### D5

The bullet replaces the *Known breaks* bullet under *A component is a contract* in `docs/principles.md`. Each module `PATCHED_MODULES` lists after phase 2 appears in it:

```
- **Known breaks:** a module global the suite patches is not a parameter, so two roots in one process
  means patching global state. Each module `PATCHED_MODULES` of `tests/test_ratchets.py` lists stays for
  one reason:
  - **a failure or a race a test injects:** `pipeline/edit.py`, `pipeline/generate.py`,
    `pipeline/importing.py`, `pipeline/review.py` and `pipeline/tattoos.py` — a write that fails, a rival
    that takes a name, a read held open;
  - **a recording spy:** `interface/ui/events.py`, `interface/ui/library.py` and `shared/ink.py` — a
    wrapper that counts a call or signals when it ran — and `shared/chain.py`'s `_kernel`;
  - **a constant:** `shared/chain.py`'s `CHUNK`, `interface/render.py`'s session id and timing, and
    `pipeline/importing.py`'s upload limit;
  - **the runs root:** `foundation/run.py`'s `RUNS_ROOT`, and `interface/cli.py`'s `RUNS_ROOT` and
    `wiring`, which a test points at a temporary library;
  - **the server's start:** `interface/ui/__init__.py`'s `serve`, which a test replaces with a recorder of
    its port;
  - **a runtime or an opener a test stands in for:** `evaluation/face.py`'s `_import`, and
    `boundary/wd14.py`'s `_require`, `import_module` and `open_session`;
  - **the Ollama safety net:** `boundary/ollama.py`'s `MODEL_RECORDS`, `_verified_build` and `OPENER`,
    which keep a test from reaching a daemon or a home directory;
  - **the frozen `boundary/provision.py`:** the image copies it, so its import-time tripwires and its
    recording spy are patched, not parameters.
```

### D6

`BD-1` of `tests/mutants.json` finds `            resolved.append(resolve(dest, models_dir, manifest))` and replaces it with a line that reads `manifest`; both read `declared` after this version. `BD-10b` finds `    labels_path, model_path, pins = verified_paths(models_dir)` and the lines after it; the find and the replace read `verified_paths(models_dir, manifest=manifest)`. The replay holds each: a find that is gone stops it with an error.

### D7

```python
def test_unpack_cli_defaults_to_the_hugging_face_fetcher() -> None:
    assert (
        inspect.signature(unpack.main).parameters["fetcher"].default
        is unpack.HuggingFaceFetcher
    )
```

The case carries `spec_exempt("structural: the command line fetches over Hugging Face unless a test gives its own")`. No decision is added: [D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets) says a row is removed by the version that removes its offender, and its text stands.

## Tests

The version adds one case and removes none; it changes the arrangement of the cases that patched. Counts, each from its command:

| layer | added | changed | command |
|---|---|---|---|
| unit | the default fetcher of `unpack.main` | the tagger's path and digest cases, the vocabulary's undeclared case, the pose finder's and the segmenter's opening cases, the unpack command line case | `git grep -n -e 'provision, "load_manifest"' -e 'provision, "VOCABULARY_MANIFEST_PATH"' -e 'unpack, "' -- tests` prints 11 lines before and 2 after |
| end-to-end | none | none | no browser test is touched |

| test | reason |
|---|---|
| `test_unpack_cli_defaults_to_the_hugging_face_fetcher` in `tests/test_provision_unpack.py` | the patch was the only case that reached the default; `T1`, a unit case, `structural:` exempt |

No test is deleted or merged, so the `I16` table is empty. The tripwire and its twin, `test_importing_the_boundary_opens_no_file_and_computes_no_digest` and `test_the_boundary_reaches_provisioning_at_its_first_use`, stand with their patches.

| arrangement | before | after |
|---|---|---|
| `_planted` of `tests/test_wd14.py` | returns the manifest dict | still does; a new `_declared` writes it to a file and returns the path |
| `_provisioned` of `tests/test_pose.py` and `tests/test_sam2.py` | patches `unpack.PLACEMENT_MANIFEST_PATH`, returns the models directory | returns the models directory and the manifest's path |
| `_declaring_none` of `tests/test_vocabulary_manifest.py` | patches `provision.VOCABULARY_MANIFEST_PATH` | returns the path |
| opener cases of `tests/test_wd14_runtime.py` | patch `provision.load_manifest` with the dict `_planted` returns | pass `manifest=` the file `_declared` wrote |
| standing mutants of `tests/mutants.json` | `BD-1` and `BD-10b` find the old lines of `wd14.py` | the find and the replace read the edited lines |
| patch ratchet of `tests/test_ratchets.py` | the row `isekai.boundary.unpack` and `PATCHED_ROWS = 18` | the row gone and `PATCHED_ROWS = 17` |

## Dependencies

None.

## Risks / Trade-offs

| risk | answer |
|---|---|
| a default read at import: `manifest=PLACEMENT_MANIFEST_PATH` binds when `def` runs | the constant is set at import and never rebound; no test patches it after this version |
| `wd14` reaches `provision` at import through a default | its default is `None`, and the tripwire and its twin hold the import |
| `BD-1` and `BD-10b` find their lines by text | phase 1 re-points both and replays them |
| the *Known breaks* bullet misnames a reason | each reason is the patch site's: the sites are in the tests named by [D3](#d3) and the ratchet's own listing |

## Verdict

Ready to build, each phase green alone: the openers, the fetcher with the ratchet row, and the documents.
