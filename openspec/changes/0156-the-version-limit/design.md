# The version limit — design

`next_version` asks `is_version` about the number it is about to return, and refuses when the answer is no. Verdict: ready to build, in the phase of [tasks](tasks.md).

## Context

An artifact is named `NNN.json`, three digits. `next_version(directory)` returns `latest + 1`, so a directory holding `999.json` returns 1000. The write goes to `1000.json`, which `ARTIFACT` does not match: `latest` stays 999, and the next write takes 1000 again and overwrites the file.

```
999.json present     next_version -> 1000     write 1000.json
                                              latest -> 999      (1000.json is no artifact)
                     next_version -> 1000     write 1000.json    overwrites
```

`is_version` in `isekai/foundation/layout.py` already says `1000 -> False`, and no code asks it. The callers that take the next number are `caption` in `isekai/pipeline/caption.py`, `tag_wd14` and `tag_hosted` in `isekai/pipeline/tagging.py`, and `draft_from`, `_copy_approval` and the review's number in `isekai/pipeline/review.py`. Each reaches the number through `next_version`. `caption`, `tag_wd14` and `tag_hosted` return before asking when the stage is already complete, so a re-run at 999 stays a no-op.

The requirement is *Artifacts are append-only and numbered, and re-running a command is a no-op* ([spec](specs/run-directory/spec.md)): a written artifact is never overwritten. The fix is required by it, so the change is a patch: a scenario is added under a requirement that already demands it.

## Goals / Non-Goals

Goals:

- A directory that holds version 999 takes no further artifact, and says why and what to do.
- One place covers every caller.

Non-goals:

- Wider numbers, or a change to the artifact's name format: both move a run file's format.
- Any caller's own handling of the refusal. A `Refusal` is what every stage already reports.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `next_version` raises `Refusal` when `is_version` says the number is no version | `next_version` numbers every caller, and `is_version` is the rule that exists | a check in each caller: each stage repeats it, and a new stage forgets it |
| [D2](#d2) | The message names the directory by its parent and its own name, says it holds the last version a name can spell, and says to move it out of the run | `layout.py` knows a directory, not a run; the parent separates `<flow>/review` from `<other flow>/review`; the way out is the one `migrate.py` already gives for files that must leave | the full path: it holds the operator's home, which the repository never transcribes |
| [D3](#d3) | The number tested is the one returned: `latest + 1`, so version 999 is taken and 1000 is refused | the last spellable name is `999.json` | refusing at 999: loses a number a name can spell |
| [D4](#d4) | `layout.py`'s docstring is amended; no decision is added in `docs/decisions.md` | the rule is held by the requirement, and no decision sets a new one | a decision for the limit: it would restate the requirement |

### D1

`next_version` becomes:

```python
def next_version(directory: Path) -> int:
    number = (latest(directory) or 0) + 1
    if not is_version(number):
        raise Refusal(...)
    return number
```

`Refusal` is already imported by `layout.py`. `is_version` is defined below `next_version` in the same module; it is read at call time, so the order stands.

### D2

```
before:  (no message: 1000.json is written)
after:   photo/captions holds version 999, the last a three-digit name can spell;
         move photo/captions out of the run, then run the command again
```

`<parent>/<name>` is `directory.parent.name` and `directory.name`. Moving the directory out starts its numbering at 1, and keeps the old artifacts where the operator put them.

### D3

`latest` of a directory with no artifact is `None`, so the first number is 1, and one holding 998 as its newest returns 999. A directory holding 999 refuses; no number is skipped.

### D4

Decision D62 in [the decisions in force](../../../docs/decisions.md) says the foundation's siblings are imported through `run.py`; the tests import `next_version` from `isekai.foundation.run` and keep doing so.

## Tests

The change adds tests to `tests/test_run_directory.py`, at the unit layer, and no end-to-end run. Counts, from `git grep -c "run-directory:numbering:a-full-directory-refuses-a-new-version" -- tests` after the build: one file, two tests.

| test | layer | proves | why this layer |
|---|---|---|---|
| `test_a_directory_holding_version_999_refuses_the_next_number` | unit | `next_version` refuses at 999, names the directory, and the directory is as it was | [T1](../../../CONTRIBUTING.md): the rule is one function over a directory listing |
| `test_the_number_after_998_is_still_taken` | unit | 999 is returned, so the refusal is not off by one | the boundary the first test cannot show |

Each binds `run-directory:numbering:a-full-directory-refuses-a-new-version`. The first fails with the refusal removed: `next_version` returns 1000 and `pytest.raises(Refusal)` does not see it. No existing test is deleted, merged or changed, so the removed-test table is empty.

An existing file turns red under no task: no test builds a directory of 999 artifacts.

## Dependencies

None.

## Risks / Trade-offs

- A directory at 999 was already broken: its next write overwrote `1000.json`. The refusal turns a silent loss into a named stop.
- The way out loses nothing but position: moving the directory leaves the artifacts where the operator put them, and the stage writes `001.json` again, as for a new run.

## Verdict

Ready to build in one phase: the refusal and its tests. No caller changes, and nothing moves, renames or deletes.
