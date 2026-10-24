# Design — 0072 cancel approve

How an approval goes back to its draft, when it may not, and where the act shows.
**Verdict: feasible** — approving is a write and an unlink; cancelling is the same two steps reversed, gated by
listings the run directory already holds.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `59d0b2c` (`v0.44.1`):

- **Approving** writes `NNN.approved.json`, numbered as the draft, then unlinks the draft
  (`isekai/pipeline/review.py:557-567`); an approval is never replaced. `current_draft` reads a draft at or below the
  newest approval as stale (`:94-106`); `discard` refuses on an approval (`:273-293`).
- **What derives from `NNN`:** `prompts/NNN` (`prompt_artifact`, `isekai/pipeline/generate.py:196`); `outputs/NNN`
  (`group_of`, `isekai/foundation/run.py:480`); failure records in either (`record_failure`, `generate.py:256`,
  `:703`); another flow's approval whose `producer.copied_from` is `{flow, approval: NNN}` (`review.py:571-632`), and
  a copy itself carries `copied_from` (`:744`).
- **The verb:** `approve` takes `--from` (`isekai/interface/cli.py:226-232`); its step calls `approve` per flow
  (`:840-853`).
- **The surface:** `read_input` (`isekai/interface/ui/app.py:595`) returns `readonly` (`:656`); `ApproveBar` shows
  *Approve sheet* (`ui/src/components/ApproveBar.vue:67`) and, once approved, the fact (`:38-39`).
- **`0070·R11`:** `refused` resets only in `watch(current)` (`ui/src/views/Review.vue:492`), not in `reread`
  (`:166`) or `discard` (`:176`).

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_review.py` | 61 | `grep -c "def test_" tests/test_review.py` |
| tests in `tests/test_pipeline_cli.py` | 32 | `grep -c "def test_" tests/test_pipeline_cli.py` |
| e2e tests | 25 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |

## Goals / Non-Goals

**Goals:** take back an approval nothing was made from; say why when it cannot be. **Non-Goals:** cancelling a
rendered approval; a new file kind.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | **derives**: a file in the flow's `prompts/` or `outputs/` numbered `NNN` — a prompt, a render group even empty, a failure record — or another flow's approval whose `copied_from` names `NNN` | an output must keep the sheet that made it | the prompt alone |
| [D2](#d2) | `review.cancellable(run, flow) -> str \| None` — `None`, or the refusal: nothing approved; anything that derives, named, with the way on — the draft waiting above it, else each copy's cancel where only copies derive and each can go, else `isekai revise <image>` where images exist, else `review --new-version`; then a later draft (re-opened — discard it first). Derived is checked first, so a draft is never named for discarding while the cancel would still be refused | one check, for the verb and the page | the page computing it; naming a copy's source, whose cancel the copy refuses |
| [D3](#d3) | `review.cancel(run, flow) -> Path \| None` raises `cancellable`'s refusal; a copy has no draft to go back to, so it is deleted, and `approve --from` writes it again; what the flow is left on is returned — the draft open above what lies beneath, else the approval beneath, still approved, else `None`; else it writes `NNN.draft.json` through `save_draft`'s contract from the approval's body — fields, `renders`, sheet, vocabulary, schema document, field map, producer less `edited` and `approved_from` — then deletes `NNN.approved.json`; a same-numbered draft beside the approval is a cancel to finish, so `cancel` deletes the approval | the inverse of approving, crash-safe | a rename |
| [D4](#d4) | `isekai approve --cancel`: `cli.py` calls `review.cancel` per run and flow, each answered on its own; `--cancel` with `--from` is refused before any run is read | the verb composes | |
| [D5](#d5) | `read_input` adds `cancel: null \| reason` from `cancellable`; on an approved sheet `ApproveBar` shows *Cancel approve*, grey-outlined, no key, no ask; disabled with the reason beside it, and with *A render session is running* while one runs for the batch; after it Review reloads the sheet on what the flow is left on — its draft, editable, or for a copy the approval beneath, read-only; the approved note names the approval it shows | reversible: approving again writes the same | a confirm step |
| [D6](#d6) | `0070·R11`: `refused.value = null` at the start of `reread()` and `discard()` in `Review.vue` | the card's fix | |

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | every `review:cancel:` scenario of the [review](specs/review/spec.md) delta; both `cli:approve-cancel:` scenarios; `ui:review:the-sheet-says-why-it-cannot-be-cancelled` | none | `tests/test_review.py`, `tests/test_pipeline_cli.py`, `tests/test_ui_api.py` |
| e2e | `ui:review:cancel-approve-opens-the-sheet-again` | `tests/e2e/conftest.py` gains a batch the test owns; `test_approve_stays_on_the_sheet` gains a step, the bar naming its approval | `tests/e2e/test_queue.py` |

**End-to-end runs added:** one, on Chromium only (T4) — the button and the sheet editable again are a browser's (T1);
it approves in its own batch, so it leaves *approve stays*' batch alone (T3). `0070·R11` adds no test: a refused
discard needs a stale draft, and the reset is one line beside the one `watch(current)` already holds.

**Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** a render starting between the page's read and the cancel → `cancel` checks again under its own listing;
  the render job's start is refused while the slot is held.
- **[Trade-off]** a cancelled approval leaves no trace → the draft holds its content, and approving again rewrites it.

## Verdict

**Feasible.** Every check is a listing the run already answers.
