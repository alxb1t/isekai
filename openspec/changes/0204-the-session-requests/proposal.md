---
bump: patch
after: [0203-the-vocabulary-refusal]
---

# The session requests

The parsing of a render's requests and the building of the argv it runs `generate` and `edit` with leave `isekai/interface/render.py` for `isekai/interface/requests.py`, and the wide signatures of `_asked` and `Record.__init__` narrow.

Reading map: [design](design.md) holds the move, the keywords and the documents it corrects, [tasks](tasks.md) its phases.

## Why

`render.py` holds the runner, the session's record and the group that reads the operator's requests and builds the argv. The group is a block no test patches and no other part of the file calls into, so it moves whole. With the plan and the lines gone before it, the file falls under the long-file ceiling and its row leaves the ratchet ([D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)).

`_asked` and `Record.__init__` are listed wide functions that no test calls past their fourth positional parameter, so their last parameters become keyword-only and both rows go. `_session` and `_rendered` stay listed, and the principles name each with its reason.

## What Changes

- `REQUEST`, `Generate`, `Request`, `parse_request`, `in_session_sources`, `again`, `without_flags`, `_taken`, `run_ids`, `_asked`, `_requested` and `_edit_argv` move to `isekai/interface/requests.py`, unchanged.
- `Generate`, `parse_request`, `in_session_sources`, `again`, `_taken`, `run_ids`, `_asked` and `_edit_argv` are imported in `render.py`, and `without_flags` is bound back as `without_flags as without_flags`. `REQUEST`, `Request` and `_requested` are not.
- `render.py` drops the imports it no longer reads, and its row leaves the long files of `tests/test_ratchets.py`.
- `_asked`'s `generate` and `Record.__init__`'s `planned`, `others` and `order` become keyword-only, and both wide rows leave.
- The standing mutants in `_asked` name `isekai/interface/requests.py`.
- `docs/principles.md` names `_session` and `_rendered` with their reason, and the interface README and `isekai/README.md` list the new module.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The change is a move: every argv byte, refusal text and session record is as it was, so no requirement moves and `skip_specs` is set.

## Impact

- Code: `isekai/interface/render.py`, `isekai/interface/requests.py`.
- Tests: `tests/test_ratchets.py` and `tests/mutants.json` alone.
- Docs: `docs/principles.md`, `isekai/interface/README.md`, `isekai/README.md` and the derived *Imported by* tables.
- No format version moves, no verb or flag changes, and the product is the same for the same inputs.

## Not in this change

- One batch function for the free pass and the paid loop: `_session` and `_rendered` keep their rows, and the session queue reshapes that loop.
- A default for `_asked`'s `generate` or for the keywords of `Record.__init__`.
- `quote` and `Record` leaving `render.py`, and any change to a line, a message or an argv.
- A decision in `docs/decisions.md`: none is added.
- Any image-frozen file, and any file under `ui/`, `tools/` or `evaluation/`.
