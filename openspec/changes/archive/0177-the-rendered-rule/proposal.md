---
bump: patch
version: 0.87.33
---

# The rendered rule

A seed is rendered in a group when its image is a file there, and review's sites ask that one rule.

Reading map: [design](design.md) holds the rule, the sites that ask it, the proof and the folders where an answer changes, [tasks](tasks.md) holds its phases, and [the delta](specs/review/spec.md) holds the scenarios.

## Why

Review asks "is this seed rendered?" differently at each of its sites. `refuse_revision` and `_refuse_unchanged` ask for the record, `drafting_approval` asks for both files, and the paid stage's resume check asks for the image alone. A folder with a record and no image is rendered to the first two and unrendered to the stage, which would render it again.

The record alone is no render: the spec says a record with no image reads as unrendered, and the stage's check is the one that spends money. The rule is the stage's, written once in `isekai/foundation/layout.py`, where [D69](../../../docs/decisions.md#d69--a-render-groups-files-are-listed-in-foundationlayoutpy-and-a-module-above-the-pipeline-reads-the-listing-from-the-foundation) says to reopen it.

No folder the product writes differs between the record's answer and the image's. A record is written beside its image, and a delete removes both.

## What Changes

- `is_rendered(group, seed, suffix)` in `isekai/foundation/layout.py`, re-exported by `run.py`: true when the seed's image is a file in the group.
- `refuse_revision` refuses a seed with a record and no image, and writes a revision of a seed with an image and no record.
- `_refuse_unchanged` approves an unchanged revision over a seed with a record and no image, and refuses one over an image with no record.
- `drafting_approval` writes a draft from a seed with an image and no record. A seed with a record and no image stays refused.
- `copied_renders` and `_first_image` list a group by `rendered_seeds` and review's suffix.
- `Surface.rendered` and the revision's `_revision` ask the rule. Their answers and texts are as before.
- Requirement *A revision is a draft from the approval that made the image, its seed prefilled*: a scenario for each of a record with no image and an image with no record.
- Requirement *Approval refuses a revision that would reproduce its images*: a scenario for each of a record with no image and an image with no record.
- Requirement *A draft is written once from another flow's approval, holding its own fields, seeds and image*: a scenario for an image with no record.
- D71 records the rule, and D69's *Accepts* drops the sites this change switches.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `review`: scenarios under the requirements named above. No requirement's text changes.

## Impact

- `isekai/foundation/layout.py` and `isekai/foundation/run.py` gain a name.
- `isekai/pipeline/review.py`, `isekai/interface/ui/surface.py` and `isekai/interface/ui/routes/reviewing.py` ask it.
- `tests/test_generate.py` holds the rule's cases and `tests/test_review.py` holds each scenario's.
- `docs/decisions.md` and `isekai/foundation/README.md` say so.
- No format version moves, no flow re-pins, no image rebuilds, and no `ui/` file changes.

## Not in this change

- The group-level rule `withdraw` applies, and `_holds_render`.
- `rendered_at`, which has no flow to ask.
- `render_groups`' `str.isdigit`.
- Review's `OUTPUT_SUFFIX`: review has a flow's name and no flow, so it still reads the suffix as a constant.
- An `is_file` check in `is_render`.
- The spec's own readings of a group holding a lone record.
- A requirement's text.
- A signature that takes a ref, which is `the-render-ref`'s.
