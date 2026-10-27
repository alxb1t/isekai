# Design — 0085 draft from

How one act replaces Revise and *Conjure from this*: the stage's two writers stay, the verb, the route and the
dialog become one. **Verdict: feasible** — `revise` and `draft_from` already write both cases; what changes is who
chooses between them, and the waiting-draft rule they share.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `d71f5ab` (`v0.57.0`):

- **The stage:** `revise(run, flow, version, seed)` (`isekai/pipeline/review.py:198`) refuses any waiting draft through
  `refuse_revision` (`:392`); `draft_from` (`:224`) records the image without listing its seed; `waiting_edit` (`:320`)
  names a waiting draft with edits of its own; `_revise_command` prints `isekai revise <image>` (`:384`).
- **The verbs:** `revise` (`isekai/interface/cli.py:323–329`, `_revise` `:515`); `review --from` and `--version`
  (`:307`); `approve --from` (`:269`); `draft_across` fills a target with no sheet (`isekai/interface/drafting.py:18`).
- **The page:** `POST /api/c/{collection}/review/{digest}/{flow}/draft-from` (`isekai/interface/ui/app.py:872`) and
  `POST /api/c/{collection}/revise` (`:918`); the large view's targets are the sheet-alone flows (`sheet_alone`, `:450`;
  `targets`, `:1057`); `⇧E` and `⇧F` (`ui/src/views/RenderLarge.vue:143`, `:149`); `⇧E` on a Renders selection
  (`ui/src/views/Renders.vue:185`); `ReviseConfirm.vue`; `revise` and `draftFrom` (`ui/src/api.ts:222`, `:210`).
- **Review** shows the photograph beside the image a draft records (`revised`, `ui/src/views/Review.vue:58`).
- **The app offers** `summon-anime-wai`, `summon-flat-anime-wai`, `conjure-anime-wai` (`config/ui.json`).

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_review.py` | 78 | `grep -c "def test_" tests/test_review.py` |
| tests in `tests/test_pipeline_cli.py` | 37 | `grep -c "def test_" tests/test_pipeline_cli.py` |
| tests in `tests/test_ui_api.py` | 78 | `grep -c "def test_" tests/test_ui_api.py` |
| e2e tests | 32 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |

## Goals / Non-Goals

**Goals:** one act from an image to any offered flow. **Non-Goals:** changing what a revision or a cross-flow draft
holds; a copied approval.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | **a revision's waiting draft:** `refuse_revision` refuses only a waiting draft `waiting_edit` names; `revise` writes over one equal to its sheet, at its number | one waiting-draft rule for both writers | refusing every waiting draft |
| [D2](#d2) | **a draft from an image** lists `{count: 1, seeds: [seed]}` beside `image`, as a revision does | the closest start; editable | no renders |
| [D3](#d3) | **the verb** `isekai draft --flow FLOW <image>…`: reads each image's run, flow, version and seed; checks all first — the image, its approval, no target's edited waiting draft, no two images on one run and target; writes `revise` for the image's own flow and `draft_across` for another; `revise` and `review --from`/`--version` deleted; refusals print `isekai draft --flow …` | one verb names the act | keeping `revise` as an alias |
| [D4](#d4) | **one route** `POST /api/c/{collection}/draft {flow, images}`: each image answered with its draft, or a waiting edit as `waiting` — written nothing — or a refusal, all or none; the large view's `targets` are every offered flow, the image's own first; `/draft-from` and `/revise` deleted | one act, one route | |
| [D5](#d5) | **the dialog** `DraftDialog.vue`, replacing `ReviseConfirm.vue`: headed *Draft from this · <flow> v<N> · seed <S>* — or *· n images* over a selection — a row per target, the image's own first and named *revise*, focused; `j` `k` move, `↵` drafts and opens Review on the first draft, `Esc` closes; a refusal per image as today; `⇧D` on the large view and on a Renders selection; `⇧E` and `⇧F` deleted; the large view's button column holds *Draft from this* `⇧D` in the writes group | one key, one dialog | a button per flow |
| [D6](#d6) | **the waiting draft:** the page opens a target's edited waiting draft and writes nothing for it; the verb refuses it, naming the draft and its discard; both replace an unedited one | the work in hand on the page; the verb asks for a write | |
| [D7](#d7) | **the docs:** `README.md`'s `isekai revise` and `review --from` → `isekai draft --flow`; `docs/data-flow.md`'s `revise` and `review --from` lines → one `draft` line; `ui/design/spec.md`'s J5, routes and key rows → *Draft from this* `⇧D` | the docs name the act | |

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | `review:revise:an-unedited-waiting-draft-is-replaced`; `review:draft-from:a-draft-from-an-image-prefills-its-seed`; `cli:draft:another-flow-is-drafted-from-the-image`; `ui:draft-from:an-unedited-waiting-draft-is-replaced`; `ui:draft-from:a-selection-drafts-into-the-flow-chosen` | `review:revise:a-waiting-draft-refuses` — an edited draft; the `cli:revise:` tests through `draft --flow`; `cli:review-from:a-target-with-no-sheet-is-filled-first` through `draft --flow`; the revise and draft-from API tests to `/draft`; `ui:conjure-from:the-large-view-names-its-targets` — every offered flow | `tests/test_review.py`, `tests/test_pipeline_cli.py`, `tests/test_ui_api.py` |
| e2e | none | `test_revise_opens_review_on_the_revision` and `test_conjure_from_this_opens_review` press `⇧D`, then `↵` on their row | `tests/e2e/test_render.py` |

**End-to-end runs added:** none.

**Removed or merged:**

| test | where | goes to |
|---|---|---|
| `test_review_from_drafts_each_flow_from_the_newest_approval_or_the_one_named` | `tests/test_pipeline_cli.py` | retired by [D3](#d3): the verb drafts from an image's approval, never a newest |
| `test_review_from_beside_a_conflicting_option_is_refused_before_any_run_is_read` | `tests/test_pipeline_cli.py` | retired by [D3](#d3): `review --from` and `--version` are deleted |

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** an unedited revision's waiting draft replaced where the operator meant to keep it → it holds its sheet's
  fields and nothing else, as conjure's rule has since `v0.53.0`.
- **[Trade-off]** the newest-approval draft of `review --from` goes → a draft starts from an image, which names its
  approval.

## Verdict

**Feasible.** The writers stay; the act around them becomes one.
