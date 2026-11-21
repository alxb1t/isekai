# The wiring's resolvers — design

Each name a test patches in the wiring becomes a keyword defaulting to that name, and the wiring's row leaves the ratchet. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`isekai/interface/wiring.py` resolves what the verbs reach: a reader, the taggers, a proposer, and the rule that bounds where a run may sit. Tests replace these names in it by `monkeypatch.setattr`: the proposer's cache `_proposer` and its openers `open_pose` and `open_segmenter`; the roots `REPOSITORY` and `DATA_ROOT` that `trackable` reads; the tagger's `open_session`; and the caption config's `load_caption_config`.

The patch ratchet counts a patch only when the module binds the name at its top level, and holds the rows, not the patches: a row with no patch is red, so the row leaves in the phase of its last patch. The placement routes read the proposer through `Wiring` and stay as they are.

```
before:  test ──setattr──▶ wiring.open_pose ◀── proposer_for ◀── Wiring.proposer
after:   test ──Proposers(open_pose=…)──▶ Wiring.proposer          (proposer_for reads PROPOSERS)

before:  test ──setattr──▶ wiring.REPOSITORY ◀── trackable ◀── destination ◀── main
after:   test ──main(…, repository=, data_root=)──▶ destination ──▶ trackable(…, repository=, data_root=)
```

## Goals / Non-Goals

- Goal: no test patches a name of `isekai.interface.wiring`, and the row `isekai.interface.wiring` is gone from `PATCHED_MODULES`.
- Goal: every keyword defaults to the name the product reads today, so no caller changes and no printed byte moves.
- Non-goal: grouping `Wiring`, or changing `place.py`, the placement routes or `Wiring.proposer`'s type.
- Non-goal: the model openers' `manifest=` and `unpack`'s row, which belong to *the model manifests*.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The proposer's cache is `Proposers`, a callable object holding `open_pose`, `open_segmenter` and the lock, with one default instance `PROPOSERS` that `proposer_for` calls | a test builds its own cache and passes it as `Wiring.proposer`, so no test resets a global and the autouse fixture goes | parameters on `proposer_for`: the cache would still be a module global a test must reset |
| [D2](#d2) | `trackable(directory, *, repository=REPOSITORY, data_root=DATA_ROOT)`; `destination` and the evaluators' `main`s take both keywords and pass them on | the roots are paths a test already holds, and the evaluator is the only caller that needs them | a `Roots` pair: a type for a pair of paths |
| [D3](#d3) | `tagger_for(open_session=open_session)`; `reader_for` and `hosted_tagger_for` take `config=load_caption_config`, a loader | a loader is what the product calls and what the test's `lambda: configured` already is | the loaded `CaptionConfig` as the default: it would read `config/caption.json` at import |
| [D4](#d4) | The row `isekai.interface.wiring` leaves `PATCHED_MODULES` in the phase of the last patch, and `PATCHED_ROWS` is 18 | a row with no patch is red, and a row with a patch must stay | a phase for the ratchet alone: it would be red between the last patch and the row |
| [D5](#d5) | No existing test's assertion changes; the arrangement does. One case is added: the default cache holds the boundary's openers | the version moves what a test passes, not what it proves | a case that opens the real models: 467 MB and a manifest |
| [D6](#d6) | No decision is added or amended | the version applies D61's rule to the wiring; the rule stands as written | an amendment to D61: its *Accepts* names the server's seams |

### D1

`Proposers` replaces `_proposer`, `_PROPOSER_OPENING` and the `global` of `proposer_for`. The refusal is not kept, and the check and the opening share one lock, as today.

```python
class Proposers:
    """The pose finder and the segmenter behind the proposed pairs, opened once and kept.

    Each verifies its files against the placement manifest before a session opens, and
    refuses naming the fetch when a file is absent. A refusal is not kept: the next
    ask opens again. The check and the opening share one lock, since the route runs in
    a thread each and two first asks must not open the models twice.
    """

    def __init__(
        self,
        *,
        open_pose: Callable[[], PoseFinder] = open_pose,
        open_segmenter: Callable[[], Segmenter] = open_segmenter,
    ) -> None:
        """Hold the two openers; nothing opens until the first ask."""
        self.open_pose = open_pose
        self.open_segmenter = open_segmenter
        self._lock = threading.Lock()
        self._proposer: Proposer | None = None

    def __call__(self) -> Proposer:
        """Return the proposer, opening the models on the first ask."""
        with self._lock:
            if self._proposer is None:
                self._proposer = Proposer(self.open_pose(), self.open_segmenter())
            return self._proposer


PROPOSERS = Proposers()


def proposer_for() -> Proposer:
    """Open the pose finder and the segmenter once, and keep them for the process."""
    return PROPOSERS()
```

`wiring_from` still sets `proposer=proposer_for`, and `tests/test_propose.py` keeps its assertion that it does. A test passes `replace(wired, proposer=Proposers(open_pose=…, open_segmenter=…))`.

### D2

```python
def trackable(
    directory: Path, *, repository: Path = REPOSITORY, data_root: Path = DATA_ROOT
) -> bool:
    """Decide whether `directory` is inside the working tree and outside the data root."""
    resolved = directory.resolve()
    return _is_within(resolved, repository) and not _is_within(resolved, data_root)
```

`destination(runs, name, *, repository=REPOSITORY, data_root=DATA_ROOT)` calls `trackable(target.parent, repository=repository, data_root=data_root)`. `main(argv, *, embedder=_embedder, repository=REPOSITORY, data_root=DATA_ROOT)` and `main(argv, *, reader=_reader, repository=REPOSITORY, data_root=DATA_ROOT)` pass both to `destination`. `evaluation/record.py`, `evaluation/__main__.py` and `evaluation/recall.py` import the roots from `isekai.foundation.run`, which each already imports.

### D3

```python
def reader_for(config: Callable[[], CaptionConfig] = load_caption_config) -> Reader:
    return OllamaReader(model=config().model)


def hosted_tagger_for(
    config: Callable[[], CaptionConfig] = load_caption_config,
) -> Tagger:
    return OllamaTagger(model=config().model)


def tagger_for(
    open_session: Callable[[], LocalTagger] = open_session,
) -> LocalTagger: ...  # the body as it stands, `open_session()` read from the parameter
```

`CaptionConfig` is imported from `isekai.foundation.caption_config`. `tagger_for`'s `except DigestMismatch as swapped:` line stays as it is: the standing mutant `BD-1b` finds it by its text. The wiring still hands these to `Wiring` as zero-argument thunks, so the defaults are what a verb calls.

### D4

A row with no patch is red, and a row with a patch must stay, so the row `isekai.interface.wiring` and the count `PATCHED_ROWS = 18` change in the phase that removes the last patch. The ratchet's own twin is untouched.

### D5

Each case that patched keeps its assertions and changes what it passes. The added case reads the default cache's attributes and opens nothing.

### D6

D61 says what a test replaces in the server is a parameter, and this version applies the same rule to the wiring. No decision is added, and none is amended: D61's *Accepts* names the server's seams.

## Tests

The version adds one case and removes none; it changes the arrangement of the cases that patched. Counts, each from its command:

| layer | added | changed | command |
|---|---|---|---|
| unit | the default cache holds the boundary's openers | the proposer's wiring cases, the evaluators' refusal cases, the local tagger's cases, the pipeline CLI's cases | `git grep -n -F "setattr(wiring," -- tests` prints the patches before, and nothing after |
| end-to-end | none | none | no browser test is touched |

| test | reason |
|---|---|
| `test_propose_wiring_the_default_cache_opens_the_boundary_models` in `tests/test_propose.py` | `proposer_for` reads `PROPOSERS`, whose openers must be the boundary's: no other case reaches the default, since each builds its own cache; `T1`, a unit case, `structural:` exempt |

No test is deleted or merged, so the `I16` table is empty. The twin of the ratchet, `test_the_check_catches_a_patched_module`, stands: its tree patches by its own names.

| arrangement | before | after |
|---|---|---|
| proposer cases of `tests/test_propose.py` | `setattr(wiring, "open_pose", …)`, `setattr(wiring, "_proposer", None)` in an autouse fixture | `Proposers(open_pose=…, open_segmenter=…)` passed as `Wiring.proposer`; no fixture |
| refusal cases of `tests/test_evaluation_cli.py` and `tests/test_recall_cli.py` | `setattr(wiring, "REPOSITORY", …)` and `"DATA_ROOT"` | `repository=` and `data_root=` passed to `main` |
| local tagger cases of `tests/test_tagging.py` and `tests/test_pipeline_cli.py` | `setattr(wiring, "open_session", …)` | `tagger_for(open_session=…)` |
| config case of `tests/test_pipeline_cli.py` | `setattr(wiring, "load_caption_config", …)` | `reader_for(config=…)` and `hosted_tagger_for(config=…)` |
| patch ratchet of `tests/test_ratchets.py` | the row `isekai.interface.wiring` and `PATCHED_ROWS = 19` | the row gone and `PATCHED_ROWS = 18` |

## Dependencies

None.

## Risks / Trade-offs

| risk | answer |
|---|---|
| a default read at import: `repository=REPOSITORY` binds the value when `def` runs | `REPOSITORY` and `DATA_ROOT` are constants of `isekai.foundation.run`, set at import and never rebound; no test patches them after this version |
| the standing mutant `BD-1b` finds its text | the `except DigestMismatch as swapped:` line is not touched; the replay in phase 3 holds it |
| `Proposers` keeps the models open for the process, as the global did | the default instance is the one `wiring_from` hands out; a test's own instance dies with the test |

## Verdict

Ready to build, each phase green alone: the cache, the roots, and the openers with the ratchet row.
