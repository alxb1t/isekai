---
bump: patch
---

# The render names

`render_image` and `render_record` in `isekai/foundation/layout.py` name a render's image and record, and the sites that only build a name call them.

Reading map: [design](design.md) holds the builders, the sites and the proof, [tasks](tasks.md) holds the phases: the builders, the stage, the other sites and the documents.

## Why

A render's image is `<seed><suffix>` and its record is `<seed>.render.json`, and lines in the stage, review, the app, the comparison page and the evaluator spell that by hand. `image_of` already names a render's file in the stage and again in the edit, so each new spelling is one more to keep true. The next versions of the render group (a named type for a render's address, one rule for "rendered") need one place that says how a render is named.

## What Changes

- `isekai/foundation/layout.py` gains `render_image(group, seed, suffix)` and `render_record(group, seed)`; `run.py` re-exports both.
- The paid stage calls them in `image_of`, `discard_render` and `render`'s loop. `image_of` stays and calls the builder.
- `draft_from` in `isekai/pipeline/review.py`, `_renders` in `isekai/interface/compare_view.py`, `evaluation/recall.py` and `evaluation/__main__.py` call them.
- The sites that spelled a group's folder by hand, `compare_view.py`, `recall.py` and `__main__.py`, call `group_of`.
- [D69](../../../docs/decisions.md#d69--a-render-groups-files-are-listed-in-foundationlayoutpy-and-a-module-above-the-pipeline-reads-the-listing-from-the-foundation)'s *Accepts* is amended; the change adds no decision.
- No requirement changes, so there is no spec delta.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change carries `skip_specs: true`: a render is named as it was, byte for byte, and the suite holds it as it stands.

## Impact

- Code: `isekai/foundation/layout.py`, `isekai/foundation/run.py`, `isekai/pipeline/generate.py`, `isekai/pipeline/review.py`, `isekai/interface/compare_view.py`, `evaluation/recall.py`, `evaluation/__main__.py`.
- Tests: cases for the builders are added to `tests/test_generate.py`; no existing assertion changes.
- Documents: `docs/decisions.md` (D69), `isekai/foundation/README.md`, the docstring of `isekai/foundation/layout.py`.
- No format version moves and no run file changes.

## Not in this change

- The sites where a name is a test for "rendered": `drafting_approval`, `refuse_revision` and `_refuse_unchanged` in `isekai/pipeline/review.py`, and `Surface.rendered` in `isekai/interface/ui/surface.py`. They wait for the rule that rewrites them.
- A new `image_of`: the stage's stays, and the edit's is another thing.
- A builder that takes a `Flow`.
- A scenario or a spec delta.
