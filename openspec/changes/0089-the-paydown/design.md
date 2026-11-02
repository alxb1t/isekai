# Design — 0089 the paydown

Each card's fix, grouped by area, and the browser tests merged. **Verdict: feasible.**

## Context

`.minions/backlog.md` holds forty-one cards. Each was read against `main` at `8a88389`. The paid ones need no pod and no
network; the closed ones are moot or already fixed; the kept ones need a rebuild, a design or a later trigger.

## Goals / Non-Goals

**Goals:** every paid card's fix, each held by a test or a visible line; the flaky stream test steady.

**Non-Goals:** `isekai/boundary/pod_start.py`, which is baked into the image; any change to a sheet, a prompt or an image.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | `close_once_open` in `tests/test_ui_jobs.py` publishes `events.CLOSE` rather than calling `broadcast.close()` | the queue is already subscribed, so the snapshot is sent before the close is read | dropping `events.py`'s closed checks, which end streams on shutdown |
| <a id="d2"></a>**D2** | Evaluation's spec says "the digest prefix its frame records" and states the unreadable frame's rule; `read` in `isekai/foundation/artifacts.py` refuses an `OSError` on `path.read_text()` by name, with its remedy | the code names a run by its frame's digest; recall and cohort must not end on one file | |
| <a id="d3"></a>**D3** | `read_env` in `isekai/boundary/gpu.py` strips a leading `export `, cuts an unquoted ` #` comment, and drops an empty value before the merge | `.env` then reads as the shell read it; a blank `.env` value can no longer override an exported key | blanking a key from `.env` |
| <a id="d4"></a>**D4** | A failed teardown in `isekai/interface/render.py` prints `refused: <cause>` when its `__cause__` is a `Refusal`, before the teardown line. The unreachable endpoint's refusal in `isekai/boundary/comfy/client.py` names the endpoint and a dropped tunnel first, and offers `python -m isekai render` as the way into a session | the operator learns why the session ended; the client cannot tell whether it runs inside a session | |
| <a id="d5"></a>**D5** | `put` in `isekai/pipeline/importing.py` catches `Exception` around the hold and records `refused`; `_refuse_name` refuses a NUL byte; the `MAX_PIXELS` comment says the bound refuses some full-resolution photographs | a write that fails is refused alone, as the ui spec requires | raising the bound past Pillow's warning |
| <a id="d6"></a>**D6** | Cancel: a flow with a draft and no approval is a no-op saying so; with neither, the refusal names `review`. `drafting_approval`'s refusal names the held approvals with `--version` when the source holds any. When a drafted approval's cancel goes first, the refusal names the whole chain — that cancel, that flow's `--discard`, then this cancel — and says the discard drops that flow's fields. The cancel requirement says "copied or drafted" | every printed way on succeeds; a re-run is a no-op, as approve's is | counting a drafted cancel as not first, which contradicts `review:draft-from:what-is-drafted-from-it-refuses-the-sources-cancel` |
| <a id="d7"></a>**D7** | `_every_refusal` in `tests/test_resume.py` provokes a draft's refusals, `draft_from`'s, and a cancel of each kind; `_unrunnable` accepts a `draft` command by its images; `AVAILABLE` gains the prefixes they print | a remedy the guard never sees can break silently | |
| <a id="d8"></a>**D8** | `set` in `ui/src/slots.ts` compares and keeps seeds as `String(BigInt(seed))`; `change()` in `RendersBlock.vue` clears every refusal when the count changes; the revision-only comments name a drafted draft too; `README.md` describes the chooser and the single flow's head; the sheet spec's Purpose names the source flow; `docs/decisions.md` records that an approval with a repeated seed is refused on every read | each says what holds | reading an old repeat leniently, a product change |
| <a id="d9"></a>**D9** | `tests/test_ui.py`'s bundle-timeout test waits for its stand-in's pid file before the ceiling starts; the `SHOWN` comment says a routes test needs it to hold no waiting sheet; `tests/e2e/test_review.py`'s tests merge per [Tests](#tests) | a loaded machine no longer reddens the gate; a merged test spends no extra page | |

**The cards closed with no work:** `0072·R7` (its merge would leave an e2e key untested), `0073·R10` (the lock is
checked before parsing), `0076·R9` (Compare's order is the pick), `0076·R11` (reflowed), `0081·R3` (an archived design).

## Tests

| layer | adds | removes |
|---|---|---|
| unit | `test_an_unreadable_file_is_refused_by_name`, `test_a_failed_body_is_named_beside_a_failed_teardown`, `test_a_name_holding_a_nul_byte_is_refused_alone`, `test_a_flow_with_no_approval_has_nothing_to_cancel`, `test_a_missing_version_names_the_held_approvals`; steps in existing tests for D3, D6, D7 and D8 | none |
| end-to-end | none | the three below, merged |

`tests/e2e/` holds 32 tests at the base (`grep -c '^def test_' tests/e2e/*.py`), on Chromium alone; this change leaves 29.

| removed test | its key | carried by |
|---|---|---|
| `test_a_tag_is_committed_from_the_ranked_autocomplete` | `ui:vocabulary:matches-are-ranked-by-post-count` | its unit tests in `tests/test_ui_api.py`; its chip step moves into `test_a_command_waits_until_the_field_is_left` |
| `test_an_approved_input_opens_read_only` | `ui:approval:approved-input-opens-read-only` | its unit test in `tests/test_ui_api.py`; its no-input step moves into `test_the_photograph_opens_in_the_viewer` |
| `test_mod_k_opens_the_cheatsheet` | `ui:cheatsheet:every-declared-criterion-is-answered` | its unit test in `tests/test_ui_api.py`; its `Mod+K` steps move into `test_the_photograph_opens_in_the_viewer`, the cheatsheet closed before `⌃P` |

## Dependencies

None.

## Risks / Trade-offs

- **A cancel's refusal text changes** → `ui/src/composables/useSheet.test.ts` and the Review reason read it; their
  needles are named in the tasks.
- **`read` refuses where it raised** → no test expects an `OSError` from a read; the write-side ones stay.
- **D4 relies on gpunit chaining the body's exception** → the test raises the teardown `from` a `Refusal`; gpunit's own
  chaining is not read here, and with no cause the line is simply absent.

## Verdict

**feasible.** Every file named exists at `8a88389`, each fix is required by an existing requirement or states what
already holds, and nothing moves a format, a verb or the product.
