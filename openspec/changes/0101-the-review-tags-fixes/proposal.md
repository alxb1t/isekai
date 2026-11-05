---
bump: minor
---

# 0101 — the review tags fixes

Every tattoo tag and `photorealistic` are kept off the Review sheet: the table excludes them, the tag search skips
them, and approval and sheet preparation refuse one.

| read | for |
|---|---|
| this file | why, and what changes |
| [the field-map delta](specs/field-map/spec.md) | the excluded list's requirement and its scenarios |
| [the sheet delta](specs/sheet/spec.md) | sheet preparation's refusal |
| [design](design.md) | the deriver, the guards, the tests |
| [tasks](tasks.md) | the phases, in build order |

```
1 the table   EXCLUDED + EXCLUDED_CONTAINING, expanded and subtracted in build(); REVISION 4; the table re-derived
2 the guards  Vocabulary.search(skip=); validate(excluded=); approve, the UI and the CLI pass it; docs D2
```

## Why

**A tattoo tag or `photorealistic` can reach a sheet, and so the prompt.** The table routes tattoo tags to
`body_shape`, `clothes` and `pose`, the autocomplete offers every vocabulary tag, and `validate()` does not read the
excluded list.

A tattoo is outside what `summon` preserves ([D29](../../../docs/decisions.md#d29--what-summon-preserves)), and
`photorealistic` names a medium, not the person.

## What Changes

- **The excluded list grows**: `photorealistic` and every vocabulary tag containing `tattoo`, expanded by
  `tools/derive_field_map.py` and subtracted from every group; `REVISION` 4 ([D1](design.md#d1), [D2](design.md#d2)).
- **`config/field_map.json` is re-derived**, never hand-edited ([D2](design.md#d2)).
- **`GET /api/tags` skips an excluded tag** through `Vocabulary.search(term, *, skip=…)` ([D3](design.md#d3)).
- **`validate()` refuses an excluded tag**, naming the tag, its field and the remedy ([D4](design.md#d4)).
- **Approval passes the excluded set**, from the UI's and the CLI's approve; sheet preparation passes its own
  field map's ([D5](design.md#d5), [D6](design.md#d6)). Saving still never validates.
- **Docs D2** names the excluded list's classes ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `field-map`: MODIFIED *The excluded list names what no criterion can hold, and nothing is in both* — the list's
  classes, the tag search skipping them, and approval refusing one.
- `sheet`: MODIFIED *Every tag in a sheet is in the vocabulary* — sheet preparation also refuses an excluded tag.

## Impact

- Changed: `tools/derive_field_map.py`, `config/field_map.json`, `isekai/shared/vocabulary.py`,
  `isekai/shared/fields.py`, `isekai/pipeline/review.py`, `isekai/pipeline/sheet.py`, `isekai/interface/cli.py`,
  `isekai/interface/ui/app.py` (at `/api/tags` and the approve handler only), `docs/decisions.md`.
- Tests: `tests/test_field_map.py`, `tests/test_vocabulary.py`, `tests/test_ui_api.py`, `tests/test_review.py`,
  `tests/test_pipeline_cli.py`, `tests/test_sheet_schema.py`, `tests/test_sheet_stage.py`.
- A new sheet's fields, so its prompt, change for the same photograph: a minor. No flow digest and no format version
  moves. Existing sheets and drafts keep their revision-3 record; approving one that holds an excluded tag is
  refused. No dependency.

## Not in this change

- `realistic`, `cosplay`, `traditional media` and the other medium tags: left as they are.
- The scored-tags panel (`SourcePanel.vue`) and `openspec/specs/ui/spec.md`: the panel stays raw and read-only.
- A refusal on save: the autosave is debounced, and saving is not approving.
- Free text in the sheet, the sheet re-thought, and the tagger choice: each waits for its own grilling.
