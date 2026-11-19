---
bump: patch
version: 0.87.26
---

# The config loader

The config loaders' shared block becomes one helper, `read_keyed`, in a new `isekai/foundation/config.py`; every message stays as it is.

Reading map: [design](design.md) holds the helper, the pins and the test cost, [tasks](tasks.md) its phases: the pins, the helper and the switch.

## Why

`load_caption_config`, `load_ink_config` and `load_tattoo_config` each open with the same block, byte for byte: read one JSON file, refuse the keys this build does not read, refuse the keys the file lacks. No fourth copy exists. A fourth config would copy the block again, and a change to one message would have to be made in each loader.

Tests pin a part of these messages by `match=` and none pins a whole one, so a mutant of the fixed text lives. The extract is cheap only once each loader's whole message is held, so the pins come first, green on the code as it stands.

## What Changes

- Add a case for the unknown-key refusal and a case for the missing-key refusal to each loader's own test file, each comparing `str(excinfo.value)` to the whole message. They are green before any code moves.
- Run `tools.mutate` over each loader's block, one run for each, and kill every survivor.
- Add `read_keyed(path, keys)` to the new `isekai/foundation/config.py`, with its own case in `tests/test_config.py`.
- Add the helper's Files row and its *Imported by* row to `isekai/foundation/README.md`, and re-derive the tables.
- Switch `caption_config.py`, `shared/ink.py` and `pipeline/tattoos.py` to call `read_keyed`. Each keeps its loader's name, its `KEYS` and its value checks. `caption_config.py` and `ink.py` drop their `json` and `Any` imports; `tattoos.py` keeps both.
- Correct the line of `isekai/shared/README.md` that names what `ink.py` imports.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. No requirement changes, so the change carries `skip_specs: true` and an empty `specs/`.

## Impact

- Code: `isekai/foundation/config.py` (new), `isekai/foundation/caption_config.py`, `isekai/shared/ink.py`, `isekai/pipeline/tattoos.py`.
- Tests: `tests/test_config.py` (new), `tests/test_caption.py`, `tests/test_ink.py`, `tests/test_tattoo_library.py`.
- Documents: `isekai/foundation/README.md`, `isekai/shared/README.md`.
- No format version moves, no verb or flag changes, and no product output changes.

## Not in this change

- The flow's and the edit's manifest checks (`flow.py`, `edit.py`): they differ in their messages and their required sets.
- `render.json` and `ui.json`: each would change a refusal.
- `edit.py`'s missing Files row in the foundation README.
- A decision: the extract adds none, and no decision governs a config's refusals.
- Any file under `config/`, `tests/record/` or `ui/`.
