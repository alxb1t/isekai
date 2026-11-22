---
bump: patch
version: 0.88.12
after: []
---

# The vocabulary refusal

A label index whose bytes differ from its pin is refused, naming the fetch, instead of ending a verb in a traceback.

Reading map: [design](design.md) holds the refusal, its case and the documents it corrects, [tasks](tasks.md) its phases.

## Why

`load_vocabulary` verifies the label index through `provision.resolve`, which raises `DigestMismatch` for bytes that differ from the pin. The function turns an absent or undeclared index into a `Refusal` and lets this one through, so neither front end handles it, though [the tagging requirement](../../specs/tagging/spec.md) says the system refuses naming the fetch when the bytes differ. The tagger beside it, `tagger_for`, already refuses in those words.

The function's docstring also gives a reason for its lazy import that other modules already contradict.

## What Changes

- `load_vocabulary` in `isekai/interface/wiring.py` turns a `DigestMismatch` into a `Refusal` worded as `tagger_for`'s.
- A case in `tests/test_vocabulary_manifest.py` plants a label index of other bytes, and fails before the fix.
- The docstring's reason for the import is corrected, and the principles' *Known breaks* bullet names an altered vocabulary.
- Requirement *The model and its label index are verified together or not used* (`tagging`): gains one scenario, its text unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `tagging`: one scenario under *The model and its label index are verified together or not used*.

## Impact

- Code: `isekai/interface/wiring.py`.
- Tests: `tests/test_vocabulary_manifest.py`.
- Docs: `docs/principles.md`.
- No format version moves, no verb or flag changes, and the product is the same for the same inputs.

## Not in this change

- `wd14.verified_paths` and `tagger_for`: the first keeps raising the raw mismatch, held by an existing test, and the second is not edited.
- The manifest keyword's defaults, and the import's place: both stay.
- A decision in `docs/decisions.md`: none is added.
- Any image-frozen file, and any file under `ui/`, `tools/` or `evaluation/`.
