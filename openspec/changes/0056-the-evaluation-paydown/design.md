# Design — 0056 the evaluation paydown

How a record names a run, which scenario the empty latest group gets, and why one card is retired. **Verdict:
feasible** — one function, its callers, two fixture pairs, one rebound test.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`7f61f56`):

- **A run's id.** `run_id` returns `digest[:ID_DIGEST_CHARS]`, the separator, then `slug(stem)`
  (`isekai/foundation/run.py:206-208`; `ID_DIGEST_CHARS = 12`, `:75`). A second photograph with the same prefix is
  refused (`:329-342`), so a prefix names one run.
- **Recall.** `_row` writes `"run": run.id` (`evaluation/recall.py:304`); the table prints `row["run"][:12]`
  (`:197`). `tests/test_recall_cli.py:192` asserts the rows' runs equal `{b.id}`.
- **The cohort evaluator.** `_rows` passes `run.id` to `unscored` and `scored` (`evaluation/__main__.py:133-138`),
  which store it as `"run": run` (`evaluation/cohort.py:187`); `_row_line` prints it whole on every non-hit line
  (`cohort.py:256`). The error stream's lines name `run.id` (`__main__.py:114`, `:171-175`), as the spec asks.
- **The shared module.** `evaluation/record.py` holds `runs_in` and `destination`; both commands import it.
- **The fixtures.** `tests/cohort/evaluation.json` holds runs `5f3a9c1e2b7d-p1-1`, `0c4e8a2d6f1b-p1-2`,
  `9b2d7e4f1a3c-p2-1`, `3e7f1c9a5d2b-p2-2`; `tests/recall/recall.json` holds `187ec7dce855aaaa`,
  `28c3bb7ce031bbbb`, `d2043248d6e1cccc`. Each has a `.txt` a test re-derives from it.
- **The empty latest group.** `test_a_latest_group_holding_no_render_is_not_rendered`
  (`tests/test_evaluation_cli.py:166-167`) is bound to `evaluation:table:the-latest-group-is-ranked`, as is
  `test_the_first_seed_of_the_latest_render_group_is_the_one_ranked` (`:143-144`).
- **The spec.** `openspec/specs/evaluation/spec.md` — *Every render is a row* (`:157`), its latest-group scenario
  (`:238-243`); the recall requirement (`:285`).
- **0055·R12** names `openspec/changes/archive/0055-attribute-recall/tasks.md`.

## Goals / Non-Goals

**Goals:** no photograph's filename in either record or table; a scenario for the empty latest group; an empty
backlog.

**Non-Goals:** the command line's ids; the error stream; a run's directory name; an archived file.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `run_prefix(run)` in `evaluation/record.py`, the first `ID_DIGEST_CHARS` characters of the digest the run's frame records; both commands write it into their rows; recall's table prints the row's value unsliced | one rule for both records; the prefix names one run; a slug can be a person's name | recall alone; recording why the full id is fine |
| [D2](#d2) | the delta's `evaluation:table:an-empty-latest-group-is-not-rendered` scenario; the test rebound to it | a behaviour gets a scenario of its own | leaving the SHALL to imply it |
| [D3](#d3) | 0055·R12 is listed and retired | an archived `tasks.md` records what was true at each commit | editing the archive |

### D1

**The prefix.** In `evaluation/record.py`:

```
def run_prefix(run: Run) -> str:
    """Return the digest prefix of a run's photograph: what a record names it by."""
    return run.photo_record["sha256"][:ID_DIGEST_CHARS]
```

`ID_DIGEST_CHARS` is imported from `isekai.foundation.run`. The digest is read from the frame rather than sliced
from the directory's name, so a run directory renamed by hand never lends its new name to a record; for a run
`open_run` named, the two are the same twelve characters. `evaluation/__main__.py:133-138` passes it in each
of its three calls; `evaluation/recall.py:304` writes it, and `:197` prints `row["run"]` with no slice. Recall
reads no frame otherwise, so a run whose frame does not read is noted on the error stream and its renders are not
read, as the cohort evaluator already treats one. `cohort.py` is untouched: it stores and prints what it is given.
The notes on the error stream keep `run.id`.

The fixtures: each run value in `tests/cohort/evaluation.json` and `tests/recall/recall.json` becomes its first
twelve characters, then each `.txt` is written from its `.json` by the module's own `table`, never by hand.

### D2

**The scenario.** `test_a_latest_group_holding_no_render_is_not_rendered` carries
`evaluation:table:an-empty-latest-group-is-not-rendered`; the other test keeps
`evaluation:table:the-latest-group-is-ranked`. No code changes.

### D3

**The retired card.** 0055·R12 asks for three counts in an archived `tasks.md` to match what the head prints.
An archived change is frozen: its ticked `Verify:` lines say what was true at their commits. The card is listed
in the proposal's `backlog:` so the release deletes it.

## Dependencies

None.

## Risks / Trade-offs

- **A record's row no longer names its run in full** → the prefix is unique under a runs directory, and
  `ls <runs> | grep '^<prefix>'` finds it.
- **A record written before this change holds full ids** → no code reads a record back; the next run of either
  command rewrites it.

## Verdict

**feasible** — one function and its callers, two fixture pairs, one marker.
