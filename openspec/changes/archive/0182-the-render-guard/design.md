# The render guard — design

The app's guard asks this server's render slot alone. It gains the one rule the verb already reads, a session's lock on a collection's folder. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`Surface.rendering(collection)` in `isekai/interface/ui/surface.py` is the one guard of the page's delete, its cancel and the review payload's `cancel`. It asks the render slot of this server's `Jobs`, so a render started from a terminal does not stop them, though both requirements say "a render session runs for the collection".

The foundation lists what a render process holds. `record_running(path)` reads one session record's lock, `running(folder)` lists the held records, and `render_running(run)` is the verb's guard. `render_running` holds the rule for a collection's folder inline: any `*.json` of `<folder>/sessions/` whose lock is held.

```
today    delete / cancel / payload ─▶ Surface.rendering ─▶ the slot of this server
verb     discard ─▶ render_running(run) ─▶ any session record of the folder held
after    delete / cancel / payload ─▶ Surface.rendering ─▶ the slot, or collection_held(folder)
                                      render_running(run) ─▶ collection_held(folder)
```

## Goals / Non-Goals

- Goal: the app refuses a delete and a cancel, and says why in the review payload, while any process holds the collection. The sentence is today's.
- Goal: the rule for a collection's folder is one function.
- Non-Goals: see [proposal](proposal.md#not-in-this-change). In short, the verb's guard, `approve --cancel`, a run outside a collection, a lock an act holds and the window before a record opens are not here.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `collection_held(folder)` joins `isekai/foundation/library.py`; `render_running` calls it | the rule is one function, and the verb and the app ask the same one | a second glob in `surface.py`; a copy of `render_running`'s body |
| [D2](#d2) | `Surface.rendering` answers for the slot or for `collection_held`, with today's sentence | the slot covers the window before a record opens, for the app's own job; the lock covers every process | the lock alone, which leaves that window; the slot alone, as today |
| [D3](#d3) | the spec delta adds scenarios and changes no requirement's text | both requirements already say "while a render session runs for the collection" | a reworded requirement; a new requirement |
| [D4](#d4) | the cases come first, hold a lock from a second open file, and patch no module | a case that fails before the switch proves the switch; a patch would add a row to the patch ratchet | patching `Jobs.slot` alone, which is what hid the defect |
| [D5](#d5) | D72's *Accepts* line names the app's guard as the slot or the rule; no decision is added | D72 says the guards stay with the acts, and the app's guard has changed | a new decision; a note in the changelog alone |

### D1

The function sits after `running` and before `render_running`, so the session's read side stays together. It is exactly this, so a mutation range is known:

```python
def collection_held(folder: Path) -> bool:
    """Return whether a render process holds collection `folder`.

    Liveness alone is read, from each session's lock, so a record that does not
    read still counts; a folder with no sessions is held by none.
    e.g. `<lib>/b` with `<lib>/b/sessions/<t>.lock` locked -> True
    """
    return any(record_running(path) for path in (folder / SESSIONS).glob("*.json"))
```

`render_running` keeps its guard for a run outside a collection and ends on `return collection_held(runs.parent)`. Its first lines, its docstring and its answer for a run outside a collection do not change. `ui/library.py` re-binds nothing: the name is new, so it has no old home ([D68](../../../docs/decisions.md#d68--the-collections-names-and-the-sessions-read-side-are-foundationlibrarypy-re-bound-at-their-old-homes)).

### D2

`isekai/interface/ui/surface.py` imports `collection_held` from `isekai.foundation.library`, between the imports of `flow` and `refusal`. The method becomes:

```python
    def rendering(self, collection: str) -> str | None:
        """Return what a render running for `collection` says, or None.

        The render slot answers for this server's job: a session over several
        collections renders each, not only the first its slot names. A session any
        process holds in the collection answers by its lock, as the verb does.
        """
        slot = self.rendering_slot()
        ours = slot and collection in slot.get("collections", [slot["collection"]])
        if ours or collection_held(library.collection(self.root, collection)):
            return "A render session is running."
        return None
```

Every caller has read the collection through `held` or `rendered`, so `library.collection` refuses nothing new. The delete route, the cancel route and the review payload do not change. The refusal's sentence is the one the existing tests assert.

### D3

`specs/ui/spec.md` holds a `## MODIFIED Requirements` block for the delete requirement and one for the review requirement, each its living text as it stands plus its new scenarios. The delete requirement gains a scenario for a session of another process, whose last line also holds that a session in another collection refuses nothing. The review requirement gains a scenario for the payload's reason and one for the cancel.

| scenario key | case | layer |
|---|---|---|
| `ui:delete-render:refused-while-another-process-renders` | `test_deleting_a_render_is_refused_while_another_process_renders` | unit |
| `ui:review:the-sheet-names-a-session-another-process-holds` | `test_the_sheet_names_a_session_another_process_holds` | unit |
| `ui:review:the-cancel-is-refused-while-another-process-renders` | `test_a_cancel_is_refused_while_another_process_renders` | unit |

### D4

Each case in `tests/test_ui_api.py` empties the render slot (no patch of `Jobs`), writes `<collection>/sessions/<id>.json` and locks its `.lock` file with `fcntl.flock(held, fcntl.LOCK_EX)` on a second open file, as `tests/test_pipeline_cli.py` does for the verb. `record_running` then answers true to a lock held outside the server. The case writes the sheet's state with the same calls the neighbouring cases use, and asserts the refusal's sentence and that the files are unchanged.

The existing cases that fake the slot stand, unchanged: the slot still refuses, and they hold the window before a record opens for the app's own job.

### D5

`docs/decisions.md` D72's *Accepts* line becomes: `the guards stay with the acts: the app's, which refuses while its render slot runs or a session holds the collection (0182), the verb's disk check and `approve --cancel`'s lack of one. `_derived`, `review.discard` and `tattoos.remove` stay where they are. Reopen when a delete's guards move into the owner.` Its *Made by* gains `0182`; the heading stays. The `library.py` row of `isekai/foundation/README.md` names `collection_held`, its *Imported by* table is derived again, and the delete bullet of `isekai/interface/ui/README.md` says the refusal holds for a session of any process.

The stale clause of the `0.87.37` notes goes: `D72 records the delete's owner, D4 and D69 name it, and its *Known breaks* leave `docs/principles.md`; the module…` becomes `D72 records the delete's owner, D4 and D69 name it; the module…`. The bullet after it already says the *Known breaks* bullet is back. Cards `0181·R1` and `0181·S3` name this one clause; `mf-release` deletes them.

## Tests

Added tests are unit tests: a case of `collection_held` in `tests/test_ui_library.py`, and the cases of [D3](#d3) in `tests/test_ui_api.py`. No end-to-end test is added or removed, so no engine runs any. Each count is the command's output.

| layer | measure | command | before | after |
|---|---|---|---|---|
| unit | cases bound to a scenario of this change | `git grep -c -e "another-process" -- tests/test_ui_api.py` | `0` | `3` |
| unit | cases of the rule | `git grep -c -e "^def test_a_collection_is_held" -- tests/test_ui_library.py` | `0` | `1` |
| e2e | runs added | none: the page's code does not change | — | — |

No test is deleted or merged, so there is no `I16` table. The new cases patch no module, so the patch ratchet's rows do not move. The rule's case is `spec_exempt`, a structural test of a foundation function, like its neighbours for `file_digest`.

The mutation runs are in [tasks](tasks.md): over `collection_held` and over `Surface.rendering`, each on the tests that reach it, exit 0 on the new lines.

## Dependencies

None.

## Risks / Trade-offs

- `rendering` now reads each session record's lock of the collection on every review read, as the hub's read already does. A library with many old records opens that many lock files; the verb's guard has always paid this. A later version may cache it.
- A session that starts after the check, and the window before its record opens, still pass the guard. They need a lock both a session and an act take, which is *the session queue*'s.
- A record that does not read still counts as held, by liveness alone. The refusal says a session runs, which is true.

## Verdict

The change is the rule, the guard that asks it, their scenarios and cases, and the documents they make false. It is ready to build in the phases of [tasks](tasks.md).
