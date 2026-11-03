# Coding standards

The rules code, tests and specs are written to here. The rules every component follows are
[`docs/principles.md`](docs/principles.md)'s.

## Baseline

The active change's **`design.md`** is authoritative for that change, with this file behind it — read
it. **`docs/decisions.md` records the decisions in force; a change's `design.md` records why one was
taken**, and is frozen when the change is archived.

**Tests are bound to the spec.** Each behaviour a test holds carries its key: one
`@pytest.mark.spec("<key>")` per scenario it proves, or one `@pytest.mark.spec_exempt("<reason>")`, alone, if it is
genuinely structural. A vitest test binds through `spec("<key>", …)` or `spec(["<key>", …], …)`. Both markers are
registered in `[tool.pytest.ini_options] markers` — registration is load-bearing, because pytest only warns on an
unregistered marker, so an unregistered one would bind nothing while looking exactly like a binding. Behaviour gets a
scenario first; a new test, or a step that adds a behaviour, gets a binding.

**A comment says what and why, in the present tense.** It names a decision in force as a plain `D27`, never a link,
and carries no version, change id or design citation; the archive keeps the history.

## Project rules

***Extend before adding*** — a new case goes into an existing test that reaches the same state, as a step carrying
its key. A new browser test names, in its commit, why none fits: its context and page boot are most of its cost.

***How a spec reads*** — the rule every requirement and every delta follows;
`tests/test_spec_prose.py` holds what a test can check of it.

- **A requirement is one SHALL paragraph** — what the system does, testable. Then one *why*
  paragraph, in the present tense. A decision in force is linked, not retold.
- **A scenario has one WHEN, one THEN and at most two AND**, each on one line where it fits. It
  carries no reasons.
- **A flow, a state or a layout gets an ASCII diagram**, in a fenced block.
- **No history** — no version, no change id, no "used to", no "this change". A figure stays only when
  it is the rule.
- **`## Purpose` is one or two sentences.**

Before, `run-directory`'s *A run root is under the ignored root or outside the repository* stated its
SHALL, then a paragraph of reasons, then a paragraph on how its first implementation failed. After:

```
The system SHALL refuse a run root inside the repository's working tree unless it is under the ignored
data root, and SHALL accept one outside the repository. It SHALL decide containment by the identity of
the directories, never by comparing the text of their paths.

A run holds a copy of the photograph, so a run root git can reach is one `git add` from publishing a
likeness ([D18](../../../docs/decisions.md#d18--runs-stay-out-of-what-git-tracks)). Two spellings of
one directory are one directory, and only its identity says so.
```
