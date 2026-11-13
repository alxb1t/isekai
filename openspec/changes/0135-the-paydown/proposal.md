---
bump: patch
debt: [0131·S4, 0131·S5, 0129·S1, 0120·R4, 0121·R4, 0119·R4, 0119·S4, 0121·S3, 0126·R4, 0133·R1]
---

# The paydown

The mutation runner replays the audit's mutants, so every finding the series closed stays closed, and the cards of `debt:` close.

Reading map: [design](design.md) holds the decisions, the mutants each test must kill and the card table, [tasks](tasks.md) holds the phases, [mutants.json](mutants.json) holds the audit's entries the build copies.

## Why

The audit named mutants for the findings the series closed, and nobody has run them: a fix may be green by accident. `tools/mutate.py` cannot replay them. It edits one line of a function body with its own operators, and the audit's mutants are text edits, some in specs and documents. Beside that, the runner's copy has no `.git`, so tests that ask git fail there at the baseline, and it links directories a test might write through.

```
 the runner      the replay      the audit's        the two        the scanner     the prose
 holds           --edits         mutants            left           reads scope     cards
 tools/mutate    tools/mutate    tests/mutants.json test_review    test_ratchets   app.py
 test_mutate     test_mutate     make mutants       test_ui_library                 ui/design/spec.md
```

## What Changes

- **Phase 1** — the runner's copy is a git repository and links `models/` alone, and a run under a `--timeout` below the baseline reports a survivor, not a timeout ([D1](design.md#d1), [D2](design.md#d2)).
- **Phase 2** — `--edits <json>` replays text edits: a path, a find that occurs once, its replacement and its tests, in any file ([D3](design.md#d3)).
- **Phase 3** — `tests/mutants.json` holds the audit's mutants of the findings the series closed, `make mutants` replays them outside the gate, and every one dies ([D4](design.md#d4), [D5](design.md#d5)).
- **Phase 4** — a discard beside another draft's source copy, and a damaged sheet, tag list and approval read by the hub, each get the test that kills its mutant ([D6](design.md#d6)).
- **Phase 5** — the patch scanner binds an alias by its lexical scope ([D7](design.md#d7)).
- **Phase 6** — a comment on the bake-digit limit and the design spec's bake-view paragraph are corrected; the cards whose premise is gone close with no edit ([D8](design.md#d8)).

No requirement is touched. The change declares `skip_specs`. One comment line under `isekai/` changes and no behaviour does.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. Every new case rides under a scenario that exists, or carries a `structural:` exemption where none fits ([D9](design.md#d9)).

## Impact

- Tools and their tests: `tools/mutate.py`, `tests/test_mutate.py`, and a new `tests/mutants.json`.
- Build files and documents: `Makefile` gains a `mutants` target and `gate` is unchanged, `CONTRIBUTING.md`, `ui/design/spec.md`.
- Test files: `tests/test_review.py`, `tests/test_ui_library.py`, `tests/test_ratchets.py`.
- One comment in `isekai/interface/ui/app.py`.
- Debt: the cards of `debt:` close at release; `0124·S2` stays open.

## Not in this change

- `0124·S2`, the cancel of an approval that goes stale while the render moves. It is a product edit to `ui/src/views/Review.vue`, and the page's version reads that view.
- The browser tests of the tattoo screens, a MinionsFactory step that runs the browser tests before a merge, and the scenarios bound to the wrong tests.
- The survivors the audit calls equivalent, `isekai/foundation/artifacts.py:541` and `isekai/foundation/run.py:287`: no test can reach them without a product edit.
- Mutants for the findings the audit found no mutant for. Their tests hold them.
- Mutants of the refactor: each refactor version adds its own entries to `tests/mutants.json` when it runs its pre-flight ([D4](design.md#d4)).
- A copy of `ui/dist` or `ui/node_modules` in the runner's copy: no test outside the browser's reads them ([D1](design.md#d1)).
