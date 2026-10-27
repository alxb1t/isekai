# Design — 0081 the fourth walkthrough

How a draft records the image it was written from, and how Review reads it. **Verdict: feasible** — one optional
producer key, written by the functions that already know the image, read where Review today guesses it.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `3b61916` (`v0.53.0`):

- **The producer:** `CopiedFrom = {flow, approval}` (`isekai/foundation/artifacts.py:161–165`); `ChainProducer`
  `{implementation, from, source, drafted_from?}` (`:168–176`); `ApprovedProducer` adds `edited`, `approved_from`,
  `copied_from?` (`:179–184`) and is written from the draft's producer.
- **The writers:** `revise(run, flow, version, seed)` writes the draft with the seed listed, recording `from` alone
  (`isekai/pipeline/review.py:197–207`); `draft_from(run, flow, source, version, schema)` (`:214`) records
  `drafted_from` (`:257`) through `_write_draft` (`:585–595`); `draft_across` calls it
  (`isekai/interface/drafting.py:18–45`); the page posts `{source, version}` (`draftFrom`, `ui/src/api.ts:207–213`;
  `ui/src/views/RenderLarge.vue:117`) to `post_draft_from` (`isekai/interface/ui/app.py:833–866`). The CLI revises
  through `revise` (`isekai/interface/cli.py:491–508`), the page through `post_revise` (`app.py:870`, `:919`).
- **The reader:** `_revision` takes the first of the body's seeds rendered under its origin (`app.py:1212–1238`);
  `_drafted` serves the flow, the approval and the target sheet's fields (`:1241–1257`); `read_input` reads both for a
  draft and an approval (`:661–676`). Review draws `revised` (`ui/src/views/Review.vue:57`) in the source pane's pair,
  headed `render being revised · seed …` (`ui/src/components/SourcePanel.vue:101–109`).

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_review.py` | 75 | `grep -c "def test_" tests/test_review.py` |
| tests in `tests/test_ui_api.py` | 75 | `grep -c "def test_" tests/test_ui_api.py` |
| e2e tests | 32 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |

## Goals / Non-Goals

**Goals:** the image a draft came from, kept and shown. **Non-Goals:** a CLI seed for `review --from`; a format
version.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | **`DraftImage = {flow, version, seed}`**; `ChainProducer` gains `"image": NotRequired[DraftImage]`; the approval carries it through `**producer` | one record of where a draft came from, beside the seeds the operator edits; D32 | the seed matched against the draft's seeds |
| [D2](#d2) | **the writers:** `_write_draft(…, image=None)`; `revise` passes `{flow, version, seed}` always; `draft_from(…, seed: int \| None = None)` passes `{source, approval, seed}` where `seed` is given; `draft_across` takes `seed`; `post_draft_from` reads an optional decimal `seed`; `draftFrom` sends `place.seed` | the functions that know the image write it | a new endpoint |
| [D3](#d3) | **the reader:** `_revision` names the recorded image, else today's first rendered seed; `_drafted` adds `image: {flow, version, seed}` where recorded | old records read as before | |
| [D4](#d4) | **the page:** `revised` comes from `revision`, else from `drafted.image`, its `src` at `drafted.image.flow`; the source pane heads it `render being revised · seed S` for a revision and `drafted from F vN · seed S` for a drafted draft; `⌃P` *Side by side* opens on either | one way to show where a draft came from | |
| [D5](#d5) | **the docs:** `ui/design/spec.md`'s large-view bullet `which marks its draft against that flow's sheet` → `which shows the summon image beside the photograph and marks its draft against that flow's sheet`; *The revision's sheet* bullet gains `; the image it revises stays, whatever its seeds become` | the docs name what Review shows | |

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | `review:revise:a-revision-records-its-image`; `review:draft-from:a-draft-from-an-image-records-it`; `ui:revise:a-revision-keeps-its-image-after-its-seed-changes` | `test_a_revision_copies_the_images_approval_and_keeps_its_seed` — its producer gains `image` | `tests/test_review.py`, `tests/test_ui_api.py` |
| e2e | none | `test_conjure_from_this_opens_review` — the summon image beside the photograph | `tests/e2e/test_render.py` |

**End-to-end runs added:** none; the conjure test reaches the page (T2).

**Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** a seed past JavaScript's exact integers → the page sends it as the decimal string it holds, and the
  server parses it, as Revise's request does.
- **[Trade-off]** a CLI conjure draft shows no image → the CLI names none.

## Verdict

**Feasible.** One key, its writers and its reader.
