---
bump: patch
after: [0132-the-prototypes-ink]
---

# The base

Tests alone pin the foundation, the session's record, the delete and the lock, so the refactor that moves them cannot turn one green by accident.

Reading map: [design](design.md) holds the decisions, the test cost and the mutants each test must kill, [tasks](tasks.md) holds the phases.

## Why

The audit found tests that cannot fail, boundaries held from one side, and whole outputs asserted by a few names. A refactor of `isekai/foundation/`, `isekai/interface/render.py`, `isekai/pipeline/review.py` and the delete paths leans on those tests. Each gap is a mutant that survives or a path a delete may drop without a test saying so.

```
retry rule ─▶ names ─▶ record's ends ─▶ delete's paths ─▶ "rendered" ─▶ refused whole
 run.py       run.py     render.py        generate/review   review/library   the two
 budget       slug       Record           edit/cli/app      sites            CLI discards
```

## What Changes

- **Phase 1** — the budget's boundary is held from below for `caption` and `tags`, and `attempts` reads one version's records at a time ([D1](design.md#d1)).
- **Phase 2** — the slug's bound and alphabet, the instruction record's path outside the repository, and a stray directory a second pass leaves ([D2](design.md#d2)).
- **Phase 3** — the session's record is read back after a stop, a raised flow, a failed flow, a done bake, a lost create and a failed teardown ([D3](design.md#d3)).
- **Phase 4** — each delete returns every path it removes, and the app's delete leaves the tree the CLI's leaves ([D4](design.md#d4)).
- **Phase 5** — a render group reads as rendered only where every site agrees ([D5](design.md#d5)).
- **Phase 6** — the CLI's discards of a render and of an edit under a running session leave the whole tree unchanged ([D6](design.md#d6)).

No file under `isekai/` changes. No spec file changes: the change declares `skip_specs`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Every new case rides under a scenario that exists, or carries a `structural:` exemption where none fits ([D7](design.md#d7)).

## Impact

- Test files: `tests/test_run_directory.py`, `tests/test_caption.py`, `tests/test_resume.py`, `tests/test_migrate.py`, `tests/test_render.py`, `tests/test_edit_session.py`, `tests/test_generate.py`, `tests/test_review.py`, `tests/test_edit_placement.py`, `tests/test_ui_api.py`, `tests/test_pipeline_cli.py`, `tests/test_ui_library.py`.
- No tool, workflow, document or product file.

## Not in this change

- The differences between the app and the CLI: the app's guard under a terminal render, `discard`'s edit thumbnails, `approve --cancel` unguarded. They stay pinned nowhere until the refactor fixes them with their tests ([D6](design.md#d6)).
- A lone image or a lone sidecar as "rendered". It waits for the refactor's render group ([D5](design.md#d5)).
- Version 1000 invisible to `versions`, and the plain `runs/` folder the lock guard never covers. Each needs a product edit.
- The routes that need a running child, the stages' importing and placement, the browser harness.
- The equivalent survivors, `isekai/foundation/artifacts.py:541` and `isekai/foundation/run.py:287` ([D8](design.md#d8)).
