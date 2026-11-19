# The config loader — design

This change moves the block the config loaders share into one helper and holds every message whole before it moves. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`load_caption_config` in `isekai/foundation/caption_config.py`, `load_ink_config` in `isekai/shared/ink.py` and `load_tattoo_config` in `isekai/pipeline/tattoos.py` each read one JSON file and refuse with `Refusal`. Each opens with the same block, byte for byte:

```
document: Any = json.loads(path.read_text())
unknown = sorted(key for key in document if key not in KEYS)    -> refuse: "<file> declares <unknown>, which this build does not read; ..."
missing = [key for key in KEYS if key not in document]          -> refuse: "<file> declares no <missing>; add the key to <file>"
```

What differs is below the block: each loader's `KEYS`, its value checks and its result type. No fourth copy exists: the flow's and the edit's manifest checks are cousins that name the manifest and a required set, in messages of their own.

`foundation` is the lowest layer, and `ink.py` and `tattoos.py` already import from it. `refusal.py` imports nothing by design, so the helper goes in a module of its own.

## Goals / Non-Goals

Goals:

- One block, in `isekai/foundation/config.py`.
- Each loader keeps its name, its `KEYS`, its value checks and every message as it is today.
- Each refusal's whole message is held by a test before the block moves.

Non-goals: the manifest checks of `flow.py` and `edit.py`, `render.json`, `ui.json` and any decision. See [the proposal](proposal.md#not-in-this-change).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The helper is one function, `read_keyed(path, keys) -> Any`, in `isekai/foundation/config.py`: it reads the JSON, raises its refusals as today and returns the document | the block is all the loaders share | a base class or a `load_config(path, keys, check)`: the value checks and the result types differ |
| [D2](#d2) | Each loader keeps its name, its `KEYS` and its value checks; `caption_config.py` and `ink.py` drop their `json` and `Any` imports, `tattoos.py` keeps both | no caller changes, and the block was the only reader of `json` and `Any` in the first two | renaming a loader, or a shared `KEYS` |
| [D3](#d3) | The pins come first: each loader gains a case per refusal, comparing `str(excinfo.value)` to the whole message, in its own test file under the marker that file uses, green on the code as it stands; a mutation run over each loader's block follows | a pin of a part leaves the rest of the text free to drift in the switch | pinning the helper's messages alone: the switch would then change a loader's message unseen |
| [D4](#d4) | The helper's own case sits in `tests/test_config.py`, `structural:` exempt, and patches nothing | the loaders' cases reach both refusals; a patched module is a ratchet row | a patch of `read_keyed` in a loader's test |
| [D5](#d5) | The foundation README gains `config.py`'s Files row and its *Imported by* row, derived; the shared README's line on what `ink.py` imports is corrected in the switch | the derived table is held by `tests/test_docs.py`; the prose line goes stale with the switch and no test reads it | also adding `edit.py`'s missing Files row: not this change's file |
| [D6](#d6) | The caption, ink and tattoo loaders alone: the flow's and the edit's manifest checks, `render.json` and `ui.json` stay out | the manifest checks differ in their messages and their required sets; each other config would change a refusal | folding them in |
| [D7](#d7) | This change adds no decision | an extract settled by an earlier plan; no decision governs a config's refusals | a new decision in `docs/decisions.md` |

### D1

`isekai/foundation/config.py` holds the block with `KEYS` replaced by its `keys` parameter, and ends on `return document`:

```
def read_keyed(path: Path, keys: Sequence[str]) -> Any:
    document: Any = json.loads(path.read_text())
    unknown = sorted(key for key in document if key not in keys)
    ...   # the two refusals, text unchanged
    return document
```

It imports the standard library and `isekai.foundation.refusal`, so `python -m isekai` still loads no wheel.

### D2

A loader's call is `document = read_keyed(path, KEYS)`. The value checks below it read `document` as they do now. Callers import the same names from the same modules.

### D3

The whole messages, per loader, with `<file>` the file's name:

| refusal | message | document |
|---|---|---|
| unknown | `<file> declares <sorted unknown, comma and space>, which this build does not read; the keys it reads are <KEYS in order, comma and space> -- correct the spelling` | every key, and the unknown keys `zeta` then `alpha`, out of alphabetical order |
| missing | `<file> declares no <missing in KEYS order, comma and space>; add the key to <file>` | keys absent: caption both of its keys, ink `floor` and `reach`, tattoo `outline_min` and `floor_stage1`, so that the ink and the tattoo pins hold `KEYS` order against alphabetical order |

The messages the new cases compare to, each one line:

```
caption  unknown  caption.json declares alpha, zeta, which this build does not read; the keys it reads are briefing, model -- correct the spelling
caption  missing  caption.json declares no briefing, model; add the key to caption.json
ink      unknown  ink.json declares alpha, zeta, which this build does not read; the keys it reads are reach, white, floor, photo_depth, image_depth, depth_min, depth_max -- correct the spelling
ink      missing  ink.json declares no reach, floor; add the key to ink.json
tattoo   unknown  tattoo.json declares alpha, zeta, which this build does not read; the keys it reads are long_side, outline_min, outline_max, view_quality, floor_stage1, floor_stage2, floor_direct, preview_floor, preview_margin, preview_wait_ms, pair_radius, region_min -- correct the spelling
tattoo   missing  tattoo.json declares no outline_min, floor_stage1; add the key to tattoo.json
```

The new cases are named for the whole message, each ending `_in_full`. The part pins already in the loaders' test files stay. `KEYS` of the caption config is alphabetical, so its pins cannot tell `KEYS` order from sorted order; the ink and the tattoo pins can.

### D4

```
tests/test_config.py        read_keyed returns the document it read
```

The loaders' unknown and missing cases reach each refusal through `read_keyed`, so the helper's own case holds its return.

### D5

The foundation README's rows for `config.py` are written by hand with `—` for the importers, then `tools.derive_imported_by` fills them. The shared README's prose line is the one place no test reads, so the switch corrects it.

### D6

The flow's check (`flow.py`) and the edit's (`edit.py`) name a manifest and a required set in messages of their own. Folding in `render.json` or `ui.json` would change a refusal, and `ui.json` has readers of one key each.

### D7

`docs/decisions.md` is not edited: nothing in force changes, so no task names it.

## Tests

The change adds unit tests and removes none; it adds no end-to-end run (`T1`). Counts are of `def test_` lines, taken with `git grep -c "^def test_" -- <file>`:

| file | at the base | after | added |
|---|---|---|---|
| `tests/test_caption.py` | 46 | 48 | the unknown and missing keys of the caption config, whole |
| `tests/test_ink.py` | 33 | 35 | the same for the ink config |
| `tests/test_tattoo_library.py` | 55 | 57 | the same for the tattoo config |
| `tests/test_config.py` | — | 1 | the document `read_keyed` returns |

Each loader's new cases extend its own test file (`T2`) and bind the marker that file uses: `caption:selection:an-unknown-key-is-refused` and `caption:selection:an-absent-or-empty-model-is-refused` for the caption's, `spec_exempt("structural: …")` for the ink's, the tattoo's and the helper's. No test is deleted or merged, so there is no `I16` table.

## Dependencies

None.

## Risks / Trade-offs

- `tools.mutate` mutates a node on one line and never a string, so its runs reach the comparisons of each block and the helper's `return`, and the whole-message cases, not the runs, hold the text. A survivor gets a case in that loader's file until the run exits 0 with no survivor.
- A loader's message drifts in the switch: the whole-message cases written first are green before it and must stay green after.
- `tools.mutate` finds only tracked files, so the helper's mutation run follows the phase that commits `config.py`.
- A loader's block is gone from its file once the switch lands, and the lines it held then hold the loader's value checks, which this change does not pin. The `Verify:` of tasks 1.5 and 1.6 therefore mutates `read_keyed` in `config.py` with that loader's tests; task 1.4 keeps its range, where `tests/stages.py` makes every mutant of `caption_config.py` invalid.
- The derived *Imported by* table moves at the refusal's row and the helper's own; both are derived, never typed.

## Verdict

Ready to build. The change is a move and an extract: no format version moves, no verb or flag changes and no product output changes.
