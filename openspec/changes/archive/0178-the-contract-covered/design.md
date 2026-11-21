# The contract covered — design

A golden's own `schema.name` says which kind it pins, and one test compares those names with `VERSIONS`. Verdict: ready to build, in the phase of [tasks](tasks.md).

## Context

[`VERSIONS`](../../../isekai/foundation/artifacts.py) maps each artifact kind's name to its version. It is built from every `Artifact` descriptor in the module, so a new kind joins it with no hand edit. [`tests/test_artifact_bytes.py`](../../../tests/test_artifact_bytes.py) pins each kind's bytes against a file under `tests/golden/`, driven from its own `KINDS` table, which is keyed by golden file name and holds the writer.

Nothing ties the two together. A kind added to the contract with no golden and no `KINDS` row passes every test. The goldens `draft`, `draft-saved` and `approved` share the name `review`, and `sheet-empty` shares `sheet`, so a golden's file name is not its kind: only its `schema.name` is.

## Goals / Non-Goals

**Goals:**

- Fail when a name of `VERSIONS` has no golden under `tests/golden/`.
- Read the kind off each golden's `schema.name`, never off its file name.
- Hold the check with a twin that fails on a name with no golden.

**Non-Goals:**

- A golden for the tattoo library's `tattoo.json`, `outline.json` and stage record. They carry no kind, so no name of `VERSIONS` is theirs, and a schema block would change their bytes.
- A new golden, a change to a golden, or a change to `KINDS`.
- Any line under `isekai/`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `kinds_without_golden(names, directory)` returns the names no golden under `directory` holds as `schema.name`. | The check is a function of its inputs, so the twin runs it on a directory it builds. | An assertion inline in the test, which no twin could drive. |
| [D2](#d2) | One test asserts it empty over `VERSIONS` and `GOLDEN`; its twin asserts it returns the missing name over a built directory. | A golden is one file per kind, so a missing one is a name left over. | Comparing file names with `KINDS`: `draft` and `sheet-empty` are not kinds. |
| [D3](#d3) | Both tests are `spec_exempt` with a `structural:` reason, and no spec delta is written. | The change adds no behaviour; `tests/test_spec_bindings.py` takes a structural reason for a test that holds a rule. | A scenario under the run directory's capability: nothing the operator sees changes. |

### D1

The helper sits in the golden section of `tests/test_artifact_bytes.py`, after `test_an_edit_record_holds_whatever_level_its_png_was_deflated_at`. It reads each `*.json` under `directory` with `json.loads` and takes `["schema"]["name"]`:

```
tests/golden/*.json ──▶ schema.name ──▶ {run, error, caption, ...}
VERSIONS keys ─────────────────────────▶ minus the set above ──▶ names with no golden
```

The result is a `set[str]`, so the test's failure message names every missing kind at once.

### D2

The twin builds a directory under `tmp_path` holding `run.json` and `sheet-empty.json`, each only a `schema` block, and asks for `run`, `sheet` and `ghost`. It expects `{"ghost"}`: `sheet` is covered by a file whose name is not `sheet`.

### D3

The reasons follow the file's own: `structural: every kind of the contract has a golden`, and `structural: twin of test_every_artifact_kind_has_a_golden`.

## Tests

The change adds unit tests to `tests/test_artifact_bytes.py` and removes none; the table holds each count with the command that produced it.

| layer | file | added | removed | command |
|---|---|---|---|---|
| unit | `tests/test_artifact_bytes.py` | 2 | 0 | `git grep -n -e "^def test_every_artifact_kind_has_a_golden" -e "^def test_the_check_catches_a_kind_with_no_golden" -- tests/test_artifact_bytes.py` prints two lines |
| end-to-end | none | 0 | 0 | no browser test changes: `git diff --name-only main -- ui` prints nothing |

Both tests sit at the lowest layer (`T1`): they read files and a mapping, and boot nothing. The twin is a unit test of the helper, as `T6` asks.

## Dependencies

None.

## Risks / Trade-offs

- A kind written by a writer that is not a contract descriptor never enters `VERSIONS`, so this test cannot see it. `test_only_the_contract_writes_a_run_file` is the rule for that.
- The check reads every `*.json` under `tests/golden/`. A golden with no `schema` block fails with a `KeyError`, which names the file in the traceback. Every golden today has one.

## Verdict

Ready to build as one phase: the helper, the test and its twin land together, so the phase ends green.
