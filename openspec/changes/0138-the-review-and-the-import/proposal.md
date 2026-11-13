---
bump: patch
after: [0137-the-server]
---

# The review and the import

The review's budget, approval and caption reader, and the import's seal, commit and kinds, are held by tests that read the wrong evidence, and some product lines each break a requirement that already stands. This change reads it right, fixes those lines, and pins both with mutants.

Reading map: [design](design.md) holds the decisions, the exact product lines and the tests, [tasks](tasks.md) its phases, [mutants](mutants.json) the entries phase 6 replays.

## Why

The audit ran each test against mutants of the product. The findings below survived or never ran, and the refactor's review and import versions move the code they guard.

| finding | what it leaves unheld |
|---|---|
| `PB-1` | the token budget's total and shares: overhead is the remainder, so no test can fail the sum |
| `PB-2` | the over-window warning counts the tags alone, while its requirement names the assembled prompt |
| `PB-3` | an approval is published by a replace after a check that cannot fire; the copy writer has no check |
| `PA-6`, `PA-7` | what the open reader is sent |
| `PA-14`, `PA-15` | a seal while a file is unread; the unseal after a refused commit |
| `PA-16` | a commit whose last rename fails leaves the photographs hidden in the staging's dot folder |
| `PA-17`, `PA-18` | an MPO; the CR2, DNG and ARW kinds and a truncated TIFF |
| `PA-19` | the empty collection name's own rule |

## What Changes

- Tests pin the budget by value, the warning at the window, both approval writers under a race, the reader's prompt, the seal, the unseal, a failed commit, the MPO and the RAW kinds. No test is deleted or merged.
- `isekai/pipeline/review.py`: `approve` takes the flow as a keyword and warns on the assembled total, and both approval writers publish with `create`. The CLI and the server pass the flow.
- `isekai/pipeline/importing.py`: a failed final move puts the photographs back, and a name taken in that window is refused as a taken name.
- `tests/mutants.json` gains this change's mutants, replayed by `make mutants`.

Each requirement the delta touches:

- `review` · *Approval warns when the assembled prompt exceeds the encoder's window*: gains a scenario for a sheet inside the window by its tags and past it assembled.
- `import` · *Import is staged, and a commit is one move*: gains a scenario for a commit asked while a file is unread, one for a refused commit, and one for a failed final move.
- `import` · *A source is cleaned before it enters a collection*: gains a scenario for a phone JPEG with a gain map.
- `import` · *A file that cannot be a source is refused by name*: gains a scenario for a file that does not decode.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `review`: one scenario under an existing requirement.
- `import`: scenarios under existing requirements.

## Impact

- Product: `isekai/pipeline/review.py`, `isekai/pipeline/importing.py`, `isekai/interface/cli.py` (the `approve` call), `isekai/interface/ui/app.py` (the approve route).
- Tests: `tests/test_review.py`, `tests/test_pipeline_cli.py`, `tests/test_ui_api.py`, `tests/test_caption.py`, `tests/test_importing.py`, `tests/images.py`.
- Specs: the review and import capabilities, by the delta of this change.
- Waits for `0137-the-server`: both append to `tests/mutants.json`, and the CLI and the route this change edits are its neighbours.
- A patch by [CONTRIBUTING](../../../CONTRIBUTING.md): no format version moves, no verb or flag changes, each fix is required by a requirement that stands, and a sheet's fields, the prompt and the image are the same for the same inputs.

## Not in this change

- The tag stage, the tagger, the provisioner, pose and Ollama: `the-boundary`.
- The review's other low findings, `PB-4`, `PB-13`, `PB-18` and `PB-19`, and the importing gaps of the audit's table: the sweep after the refactor's last version (Q59).
- The mis-bound scenarios: the spec audit.
- An empty folder created in the commit's window, which the final rename still replaces: it needs the collection claimed before it is complete, against [import](../../specs/import/spec.md)'s rule that a collection never looks complete early.
- Any page change: the page never shows approval warnings.
