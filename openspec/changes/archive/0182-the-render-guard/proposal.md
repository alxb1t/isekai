---
bump: patch
version: 0.87.38
debt: [0181·R1, 0181·S3]
---

# The render guard

The app refuses a delete and a cancel while any process renders the collection, as its requirements already say.

Reading map: [design](design.md) holds the rule, the guard and the documents, [tasks](tasks.md) its phases.

## Why

The page's delete requirement and its review requirement say the server refuses a delete and a cancel "while a render session runs for the collection". The guard is `Surface.rendering`, and it asks this server's render slot alone. A render started from a terminal holds the collection by a lock on its session record, and the app's delete, its cancel and the review payload's reason do not see it.

The foundation already reads that lock: `render_running` in `isekai/foundation/library.py` is the verb's guard. This version gives the rule for a collection's folder one function, and the app asks it.

Debt cards `0181·R1` and `0181·S3` ride along. Each names a clause of a `CHANGELOG.md` line that the amend of `0181` made false: the *Known breaks* bullet of the state principle stayed.

## What Changes

- `collection_held(folder)` joins `isekai/foundation/library.py`: it answers whether a render process holds a collection's folder, by liveness alone. `render_running` calls it.
- `Surface.rendering` answers for this server's render slot or for `collection_held`, with today's sentence. The delete, the cancel and the review payload's `cancel` read it, and none of their code changes.
- The `ui` spec gains scenarios under the delete requirement and under the review requirement. No requirement's text changes.
- D72's *Accepts* line says the app's guard asks the slot or the rule.
- `CHANGELOG.md` gains this version's entries, and the stale clause of the `0.87.37` notes goes (cards `0181·R1`, `0181·S3`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`: *The large view deletes its render after asking, and the Hub opens on its cell* gains a scenario for a session of another process. *Review opens a collection at its own address, lists every unrendered sheet, and Approve stays on the sheet* gains a scenario for the sheet's reason and one for the cancel. Each requirement's text is as it was.

## Impact

- Code: `isekai/foundation/library.py`, `isekai/interface/ui/surface.py`.
- Tests: `tests/test_ui_library.py`, `tests/test_ui_api.py`.
- Docs: `docs/decisions.md` (D72), `isekai/foundation/README.md`, `isekai/interface/ui/README.md`, `CHANGELOG.md`.
- No format version moves.

## Not in this change

- The verb's guard, `approve --cancel`'s missing guard and a run outside a collection: a minor of its own, `the-terminal-guards`, planned after this version ships.
- A lock an act holds, and the window before a session's record opens: they wait for a lock both a session and an act take, in *the session queue*'s plan.
- Card `0181·S1`: it wants the owner's order changed, when a change next opens `isekai/foundation/discard.py`.
- Any file under the page's `ui/`, `tools/` or `evaluation/`.
- The render route's `_held`, which holds the Render start back: it is no delete or cancel.
- `render_running`'s wrapper in `isekai/interface/ui/__init__.py`, and the stage record, which is the next version's.
