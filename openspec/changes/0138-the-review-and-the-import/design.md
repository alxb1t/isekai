# The review and the import — design

The review and the import hold their findings by tests that read the wrong evidence, and some product lines break a requirement that stands. This change pins each finding, fixes those lines, and holds both with mutants. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The audit ran each test against mutants of the product, and the findings below survived or never ran, read at the cut at `d3f72349`. `0135-the-paydown` adds the replay mode `--edits`, `tests/mutants.json` and `make mutants`; `0136-the-cli-and-the-session` and `0137-the-server` fill the file with their entries. Phase 6 appends to it.

| gap | where it lives at the cut |
|---|---|
| the budget's total and shares are never pinned: the overhead is the remainder, so the sum cannot fail | `isekai/pipeline/review.py` `token_budget`; `tests/test_review.py` |
| the warning counts the tags alone, and `approve` holds no flow to assemble a prompt from | `isekai/pipeline/review.py` `approve`, `estimate_tokens`; its callers in `isekai/interface/cli.py` and `isekai/interface/ui/app.py` |
| an approval is published by `write` after a check that cannot fire; the copy writer has no check | `isekai/pipeline/review.py` `approve`, `_copy_approval`; `isekai/foundation/artifacts.py` `create` |
| nothing asserts what the open reader is sent | `isekai/pipeline/caption.py` `OllamaReader.prompt`; `tests/test_caption.py` |
| a seal while a file is unread, and the unseal after a refused commit, run in no test | `isekai/pipeline/importing.py` `Reader.seal`, `Imports.commit`; `tests/test_importing.py` |
| a commit whose last rename fails leaves the photographs in the staging's dot folder | `isekai/pipeline/importing.py` `commit` |
| an MPO, the CR2, DNG and ARW kinds and a truncated TIFF run in no test; the empty name's rule is unheld | `isekai/pipeline/importing.py` `_decode`, `_clean`, `_raw_kind`, `_refuse_collection_name` |

```
 review.py    token_budget · approve · _publish · _copy_approval   (phases 1, 2)
 caption.py   OllamaReader.prompt                                  (phase 3)
 importing.py seal · commit · _put_back · _raw_kind · _clean       (phases 4, 5)
 tests/mutants.json ◀── mutants.json                               (phase 6)
```

## Goals / Non-Goals

**Goals**
- The budget's total and each share are literals, and a sheet past the window only when assembled warns.
- An approval is never replaced, by either writer, under a race.
- The reader's prompt is the briefing alone, and a test holds it.
- A commit never strands the photographs, and a refused commit leaves the import open.
- An MPO is staged ready, each RAW kind is refused by its header, and a cut TIFF is no RAW photograph.
- Each finding's mutant dies, and stays dead in `tests/mutants.json`.

**Non-Goals**
- A format version, a flag, a verb, a decision in force, or a requirement's text. `docs/decisions.md` is not edited.
- The review's other low findings and the importing gaps of the audit's table.
- An empty folder made in the commit's window: the final rename replaces it, as before.
- The tag stage and the boundary: `the-boundary`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | Each finding is held at the lowest layer that fails for its mutant: the function for the stages, one route and one verb for the flow's pass-through | a layer above costs seconds and hides the line | an end-to-end test for each |
| [D2](#d2) | The budget is pinned by literals from the tracked flow | overhead is the remainder, so only a literal can fail | a sum, which holds by construction |
| [D3](#d3) | `approve` takes the flow as a keyword, passed by the CLI and the server, and warns on the assembled total; without it the tags' estimate stays | the requirement names the assembled prompt; the calls in tests stay as they are | replacing `schema` with a `Flow`; loading the flow inside `approve` |
| [D4](#d4) | Both approval writers publish with `create`, a taken number refused with today's sentence | the scenario says no command overwrites an approval, and a replace after a check is a window | a lock; a second check |
| [D5](#d5) | The reader's prompt is asserted at the stage's transport and on the adapter's body | the stage test already captures the body | an assert on the briefing file |
| [D6](#d6) | A seal while a file is unread and the unseal after a refusal are tested through `Imports.commit`, the unread file held on an event | the seam is the file's own read, which blocks without a timer | a sleep |
| [D7](#d7) | A failed final move puts the photographs back, refuses a name taken in that window as a taken name, and re-raises any other failure | the scenario says a taken name is refused and the staging kept; no requirement names another failure | a link in place of a move; a retry that finds the dot folder |
| [D8](#d8) | The RAW headers are built in code, the MPO by Pillow | the kinds are read from magic bytes, and Pillow writes an MPO | a camera file in the tree |
| [D9](#d9) | Scenarios are added under the requirements that demand them; other tests carry the key that already stands | a patch adds a scenario under a requirement, never a requirement | `skip_specs`; a MODIFIED SHALL |
| [D10](#d10) | Phase 6 appends this change's mutants to `tests/mutants.json`, the product's finds written for the fixed code | a fixed line no longer holds its audit find | the audit's finds |

### D1

The tests extend the files that hold each subject. A mutant's test file is named in [mutants.json](mutants.json), and the replay runs that whole file. No test is deleted, so [Tests](#tests) holds no table of removals.

### D2

`token_budget` over the tracked flow `summon-anime-wai` and a sheet of `hair_colour` `["brown hair"]` and `clothes` `["collared shirt", "jeans"]`, every other field empty, is these literals:

| value | literal | from |
|---|---|---|
| `total` | `28` | the assembled prompt's words and separators, and the encoder's own two |
| `per_field["hair_colour"]` | `3` | its tag's words and its tag |
| `per_field["clothes"]` | `5` | its tags' words and its tags |
| every other share | `0` | no tag |
| `overhead` | `20` | `28` less the shares |

An empty sheet's `total` is `20`. The test reads the flow it pins, so a change to the flow's prefix or trailer moves these literals on purpose.

### D3

`isekai/pipeline/review.py` after the change:

```python
def approve(
    run: Run,
    flow: str,
    schema: Schema,
    vocabulary: Vocabulary,
    source: str | None = None,
    *,
    excluded: frozenset[str] = frozenset(),
    definition: Flow | None = None,
) -> tuple[Path | None, list[str]]:
```

```python
    warnings: list[str] = []
    estimate = (
        estimate_tokens(fields, schema)
        if definition is None
        else token_budget(fields, schema, definition).total
    )
    if estimate > ENCODER_WINDOW:
```

The warning's text is unchanged: it already says "the assembled prompt". `approve`'s docstring says `definition` makes the warning count the assembled prompt, and `token_budget`'s docstring drops its paragraph on leaving `estimate_tokens` alone: that function stays `approve`'s count when it is given no flow. A copy takes `source` and returns before the warning, so `approve_across` is untouched.

The CLI passes `definition=flows[name],` and the route passes `definition=one.flow,`, each as the last keyword of its `approve` call.

```
 sheet fields ──▶ definition given? ──yes──▶ token_budget(...).total ──┐
                        │ no                                           ├─▶ > ENCODER_WINDOW ─▶ warning
                        └────────────▶ estimate_tokens(...) ───────────┘
```

The page shows no approval warning, so it changes nothing. Its budget bar already uses the assembled count, so the bar and the warning now agree.

### D4

`isekai/pipeline/review.py` after the change, `create` imported from `isekai.foundation.artifacts` in the list's order:

```python
def _publish(run: Run, flow: str, path: Path, body: ReviewApproved) -> None:
    """Write `body` at `path`, refusing a number another writer has taken first."""
    try:
        create(path, APPROVED_FILE, body)
    except FileExistsError:
        raise Refusal(
            f"{path.name} already exists in {flow}/{REVIEW}/ and an approved "
            f"artifact is never replaced; run {_again(run, flow)} to correct it "
            "under the next number"
        ) from None
```

`approve` ends `path = directory / artifact_name(version, APPROVED)`, `_publish(run, flow, path, approved_body)`, `draft.unlink()`, `return path, warnings`, and its `path.exists()` check and sentence go. `_copy_approval` ends `written = directory / artifact_name(next_version(directory), APPROVED)`, `_publish(run, flow, written, copied)`, `return written`. `create` writes the bytes `write` wrote, so no file changes.

The race is a file dropped inside the publish, after the draft is read. The test wraps `create` so it writes the rival's bytes at the path and then calls the real `create`; the refusal shows, and the rival's bytes and the draft stay. The audit's seam, a patched `read` of the draft, drops the file before the check that stands today, so it would pass at `main`.

### D5

The stage test `test_the_caption_records_the_options_the_reader_sent` already reads the one request body the transport received. It also asserts `sent["prompt"]` is the briefing file's text, stripped of trailing whitespace, with one newline: what `OllamaReader.prompt` returns. `test_the_open_readers_body_carries_the_photograph_and_the_pinned_sampling` asserts `body["prompt"] == "Describe the person.\n"`, the audit's own line. One line of `caption.py` holds both mutants.

### D6

`Reader.seal` refuses while any file is `waiting` or `converting`. The test patches `importing._clean` with a function that waits on an `Event`, so the file stays unread in whichever of those states it is, and sets the event in a `finally`. The refusal reads `0 of 1 files are read`, and a second commit after the event lands.

A refused commit is a taken name, which refuses before any file moves. The test then chooses a second file, which a still-sealed import would refuse with `already committing`, and commits under a free name.

### D7

`isekai/pipeline/importing.py` after the change, in `commit`'s new-collection branch:

```python
        build = staging / _BUILD / SOURCES
        build.mkdir(parents=True)
        try:
            for path in taking:
                path.rename(build / path.name)
            os.rename(build.parent, collection)
        except BaseException:
            _put_back(build, staging)
            if collection.exists():
                raise Refusal(
                    f"{name}: a folder of that name is in the library; pick another"
                ) from None
            raise
```

```python
def _put_back(build: Path, staging: Path) -> None:
    """Move each file in `build` back into `staging`, and delete `build`'s folder."""
    for path in build.iterdir():
        path.rename(staging / path.name)
    shutil.rmtree(build.parent)
```

```
 staged files ─▶ .collection/sources/ ─▶ rename to <name>
                        │ fails                │ fails
                        └────── _put_back ◀────┘ ─▶ taken? Refusal : re-raise
```

A failure on a file's own move is rolled back the same way. The test wraps `os.rename`, which `Path.rename` calls, so it keys on the source's name: `.collection` for the final move and a staged file's name for a move of one.

For a taken name the wrapper makes `<name>` with a file in it and calls the real rename, which refuses a non-empty folder on every platform. The errno differs, so the test matches the refusal's sentence, never the errno. A patch of `importing.os` names no module of the repository, so no ratchet row is added.

### D8

`tests/images.py` gains `cr2_bytes`, `dng_bytes`, `arw_bytes` and `cut_tiff_bytes` beside `nef_bytes`, each built with `struct`:

| builder | bytes | `_raw_kind` |
|---|---|---|
| `cr2_bytes` | `b"II*\x00"`, `struct.pack("<I", 16)`, `b"CR\x02\x00"`, eight zero bytes | `CR2` |
| `dng_bytes` | `b"II*\x00"`, `struct.pack("<IH", 8, 1)`, `struct.pack("<HHI", 0xC612, 1, 4)`, `bytes([1, 4, 0, 0])`, four zero bytes | `DNG` |
| `arw_bytes` | `b"II*\x00"`, `struct.pack("<IH", 8, 1)`, `struct.pack("<HHII", 0x010F, 2, 5, 26)`, four zero bytes, `b"SONY\x00"` | `ARW` |
| `cut_tiff_bytes` | `b"II*\x00"`, `struct.pack("<I", 1000)` | `None`, by `struct.error` |

A RAW case calls `read` directly, as the animated GIF's test does, and matches `a <KIND> RAW photograph`. The cut TIFF goes on to decode, and matches `does not decode as an image`.

The MPO is built inline with Pillow: an RGB image saved as `"MPO"` with `save_all=True` and a second, smaller image appended. It is staged `ready`, the staged file opens as one frame of a JPEG, and `verify` finds nothing.

### D9

| requirement | scenario added | key |
|---|---|---|
| `review` · *Approval warns when the assembled prompt exceeds the encoder's window* | a sheet inside the window by its tags and past it assembled warns | `review:budget:a-sheet-past-the-window-only-assembled-warns` |
| `import` · *Import is staged, and a commit is one move* | a commit asked while a file is unread is refused | `import:stage:a-commit-waits-for-every-file-to-be-read` |
| the same | a refused commit leaves the import open | `import:stage:a-refused-commit-leaves-the-import-open` |
| the same | a move that fails puts the files back | `import:stage:a-failed-move-puts-the-files-back` |
| `import` · *A source is cleaned before it enters a collection* | a phone JPEG with a gain map is stripped, not refused | `import:clean:a-phone-jpeg-with-a-gain-map-is-stripped` |
| `import` · *A file that cannot be a source is refused by name* | a file that does not decode is refused, whatever its header | `import:refuse:a-file-that-does-not-decode-is-refused` |

Each requirement's text is the living one, unchanged; the delta is a MODIFIED block because it adds scenarios. The tests with no scenario of their own carry a key that stands:

| test | key it carries | because |
|---|---|---|
| the budget's literals | `review:budget:count-covers-the-assembled-prompt` and `review:budget:shares-and-overhead-sum-to-the-total` | the total and the shares are the scenarios' own words |
| both approval races | `review:approval:approved-is-not-overwritten` | no command overwrites an approval |
| the reader's prompt at the stage | `caption:inputs:only-the-photograph-is-passed` | the reader receives the briefing and nothing else |
| the RAW kinds | `import:refuse:a-raw-photograph-is-refused` | a kind of RAW is a RAW photograph |
| a name taken as the move lands | `import:stage:an-unusable-name-is-refused` | taken, refused, staging kept |

### D10

The change's mutants are in [mutants.json](mutants.json), each `tests` a list of files. The product's finds are written for the code of [D3](#d3), [D4](#d4) and [D7](#d7); the rest are the audit's lines, unchanged. Phase 6 appends them to `tests/mutants.json` and replays the file.

## Tests

Every case is a unit test: no browser, no end-to-end test is added, and none runs on an engine. The tests each file holds at the cut, by `git grep -c -E '^def test_' -- <file>`, and what it gains:

| file | tests at the cut | gains | phase |
|---|---|---|---|
| `tests/test_review.py` | 97 | the budget's literals; the warning past the window; both approval races | 1, 2 |
| `tests/test_pipeline_cli.py` | 50 | the warning through `approve` | 1 |
| `tests/test_ui_api.py` | 97 | the warning through the route; a commit whose name is taken as it lands; the stand-in `approve_` takes `definition` | 1, 4 |
| `tests/test_caption.py` | 46 | an assert in the open reader's body test and in the stage's options test | 3 |
| `tests/test_importing.py` | 26 | the seal; the unseal; the failed move and the taken name; the MPO; the RAW kinds; the cut TIFF; the empty name's message | 4, 5 |
| `tests/images.py` | helper | the byte builders | 5 |

A new test that runs over five seconds carries the `slow` marker, which `make check` skips; none is expected, as no child process starts and every wait is on an event.

`tests/mutants.json` is not a test and is not in the gate; `make mutants` replays it. The mutants, and the test file that must kill each:

| mutant | where | killed by |
|---|---|---|
| `PB-1a` | `isekai/pipeline/review.py` `token_budget`, the total's `+ 2` | `tests/test_review.py` |
| `PB-1b` | `isekai/pipeline/review.py` `token_budget`, a share's `+ len(tags)` | `tests/test_review.py` |
| `PB-2` | `isekai/pipeline/review.py` `approve`, the assembled count | `tests/test_review.py` |
| `PB-2b` | `isekai/interface/cli.py`, the `definition` keyword | `tests/test_pipeline_cli.py` |
| `PB-2c` | `isekai/interface/ui/app.py`, the `definition` keyword | `tests/test_ui_api.py` |
| `PB-3a` | `isekai/pipeline/review.py` `_publish`, `create` | `tests/test_review.py` |
| `PB-3b` | `isekai/pipeline/review.py` `_publish`, the `except` | `tests/test_review.py` |
| `PA-6` | `isekai/pipeline/caption.py`, the prompt's return | `tests/test_caption.py` |
| `PA-14` | `isekai/pipeline/importing.py` `Reader.seal`, `if unread:` | `tests/test_importing.py` |
| `PA-15` | `isekai/pipeline/importing.py` `Imports.commit`, the unseal | `tests/test_importing.py` |
| `PA-16a` | `isekai/pipeline/importing.py` `commit`, `_put_back` | `tests/test_importing.py` |
| `PA-16b` | `isekai/pipeline/importing.py` `commit`, the taken check | `tests/test_importing.py` |
| `PA-17a` | `isekai/pipeline/importing.py` `_decode`, the MPO exemption | `tests/test_importing.py` |
| `PA-17b` | `isekai/pipeline/importing.py` `_clean`, the MPO strip | `tests/test_importing.py` |
| `PA-18a` | `isekai/pipeline/importing.py` `_raw_kind`, the CR2 signature | `tests/test_importing.py` |
| `PA-18b` | `isekai/pipeline/importing.py` `_raw_kind`, the DNG tag | `tests/test_importing.py` |
| `PA-18c` | `isekai/pipeline/importing.py` `_RAW_MAKES`, ARW | `tests/test_importing.py` |
| `PA-18d` | `isekai/pipeline/importing.py` `_raw_kind`, the `struct.error` answer | `tests/test_importing.py` |
| `PA-19` | `isekai/pipeline/importing.py` `_refuse_collection_name`, the empty name | `tests/test_importing.py` |

No test is deleted or merged, so no row maps one test to another.

## Dependencies

None.

## Risks / Trade-offs

- **`create` links.** An approval is now published by a hard link, so a review directory on a filesystem with none fails the approval with an `OSError`, which `approve` does not translate. Runs already need hard links for an edit's composite, and the session record is written by `create`.
- **A patch of `os.rename` is process-wide.** The tests of [D7](#d7) read no reader thread: each stages with `read` and commits directly, and the route's test waits until its upload is read before it patches.
- **The literals are the tracked flow's.** A change to the prefix or trailer in `flows/summon-anime-wai/flow.json` moves the literals of [D2](#d2) on purpose.
- **A `find` that moves makes the replay refuse.** Phases 1 to 5 write each product line of [D3](#d3), [D4](#d4) and [D7](#d7) as quoted, so phase 6's finds stand; its first tasks check them.
- **The approve stand-in in the API tests.** `_update_during_approval` replaces `app_module.approve` with a function that takes no `definition`, so phase 1 gives it the keyword.

## Verdict

Ready to build. Each phase ends on a green `make gate`, and phase 6 on a replay with no survivor. Nothing is irreversible: no format version, requirement text or decision moves, and each product edit is a few lines under a requirement that stands.
