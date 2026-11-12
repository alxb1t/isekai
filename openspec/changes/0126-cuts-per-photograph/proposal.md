---
bump: minor
beside: [0125-the-outline-gestures]
---

# Cuts per photograph

A cut belongs to its photograph: kept under that photograph, listed and named only on its renders, and a tattoo can be removed.

Reading map: [design](design.md) holds the decisions, the tests and the risks, [tasks](tasks.md) its phases: the library and its routes, then the picker.

## Why

The person's first session on *Place a tattoo* showed faults in the library. A cut was listed on every render, greyed out on the ones it is not cut from, and its name was taken library-wide. Nothing could be removed, so the test cuts `test` and `test1` stay forever.

The picker did not say which form a tattoo needs. A cut carries its own photograph's light and angle, so it is no input for another photograph. It should not be there to see, nor hold a name another photograph may want.

## What Changes

- A cut is kept at `.tattoos/.cuts/<digest>/<name>/`, `<digest>` the photograph's run digest. An upload stays at `.tattoos/<name>/`.
- A name is one tattoo among what one render lists: an upload refuses a name any cut holds, a cut refuses an upload's name and a cut of its own photograph's.
- Every library function and route that reads a tattoo by name takes the render's digest.
- The list for a digest holds the uploads and that photograph's cuts. The picker shows no cut of another photograph.
- A cut kept at `.tattoos/<name>/` moves to `.cuts/<cut_from>/<name>/` the first time the library reads it.
- A tattoo is removed by `DELETE /api/tattoos/{name}`, from a *Remove* on its card that asks a second click.
- Each picker form says what it takes, in a line under its heading.
- D52 reads *kept until removed*, and the threat model names the removal.

Requirements, one line each:

- `tattoo` · *A tattoo is kept in the library, whole and never deleted*: REMOVED, and ADDED as *A tattoo is kept in the library, whole until it is removed*. It holds the folders, the names, the digest and the removal.
- `tattoo` · *A tattoo is cut from a photograph*: MODIFIED. A cut lives under its photograph's folder and is found there alone.
- `ui` · *The picker lists the kept tattoos and takes an upload or a cut*: MODIFIED. It lists no cut of another photograph, offers *Remove*, and says what each form takes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `tattoo`: where a cut is kept, how a name resolves, what the list holds, and removal.
- `ui`: the picker's list, its *Remove* and its form lines.

## Impact

- `isekai/pipeline/tattoos.py` and the tattoo routes of `isekai/interface/ui/app.py`.
- `tests/test_tattoo_library.py`, `tests/test_tattoo_placement.py`, `tests/test_ui_tattoo.py` and `tests/test_ui_placement.py`.
- `ui/src/api.ts`, `ui/src/tattoos.ts`, `ui/src/tattoos.test.ts`, `ui/src/composables/usePlacing.ts`, `ui/src/components/TattooPicker.vue`, `ui/src/views/Place.vue`, `ui/src/app.css` and the components that call a tattoo by name.
- `docs/decisions.md` (D52), `THREAT_MODEL.md`, `docs/edit-tattoo.md`, `docs/modules.md`, `ui/design/spec.md` and `isekai/pipeline/README.md`.
- The library on the operator's disk: a cut kept today moves once, with no step to run.
- No package is added. Neither manifest changes.

## Not in this change

- Renaming a tattoo.
- A cut of another photograph being listed, greyed out or chosen: its card goes, so its wording goes too.
- Mounting components in the UI tests: the node tests cover the pure rules.
- The outline and pair gestures, the keys and the hint lines: the outline-gestures change owns them.
