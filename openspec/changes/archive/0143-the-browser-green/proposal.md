---
bump: patch
version: 0.86.16
---

# The browser green

The browser tests the guard of the page-in-a-browser version failed go green: the guard sees old behaviours in the import and render tests, and one stale tile in the product.

Reading map: [design](design.md) holds the decisions, the test cost and the risks, [tasks](tasks.md) holds the phases — the fake and the refusals, then the Hub after a delete.

## Why

CI run `43448367157` on `v0.86.15` passed lint, vitest and pytest, and the browser suite raised errors at teardown. The guard of `tests/e2e/guard.py` raises them: it fails a test on an undeclared 4xx and on a page error. Each error is an old behaviour the guard now reports.

```
import test      fake snapshot has `files` only ──▶ the page reads jobs.prepare of undefined ──▶ page error
two render tests drawer reads the session before the child opens its record ──▶ 409 undeclared
conjure test     Yes ──▶ Hub draws the hub read before the delete ──▶ thumbnail of the deleted render ──▶ 409
```

The import and render tests' faults are faults of the tests. The conjure test's is a product fault: the Hub draws a render the delete just removed, and only then reloads. A patch fixes them together, before the refactor's first version leans on the suite ([D1](design.md#d1)).

## What Changes

- `tests/e2e/test_import.py`: the faked snapshot carries `jobs` and `billing` beside `files`, as every server snapshot does.
- `tests/e2e/test_render.py`: the render dialog test and the drawer test declare the session record's refusal, one `sessions/` prefix per rendered collection.
- `ui/src/views/RenderLarge.vue`: after *Yes*, the view reads the hub again, then opens it. A reload that fails opens it all the same.
- `tests/e2e/test_render.py`: the conjure test binds the new scenario and asserts that no thumbnail of the deleted render is asked for.
- `ui/` spec, requirement *The large view deletes its render after asking, and the Hub opens on its cell*: one scenario, *the Hub opens without the deleted render*.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`: *The large view deletes its render after asking, and the Hub opens on its cell* gains one scenario. Its SHALL paragraph is unchanged.

## Impact

- `ui/src/views/RenderLarge.vue` is the one product file; the browser suite under `tests/e2e/` is the rest. `ui/src/App.vue` is read, not edited: it opens the collection store the view takes.
- No format version moves, no verb or flag changes, and the product for the same inputs is the same.
- CI proves the change after the merge, as the version before it was proven ([D5](design.md#d5)).

## Not in this change

- The tattoo screens' browser tests — *e2e tattoo*, once the place fixes are in.
- A MinionsFactory step that runs the browser tests before a merge — out of scope for now; CI holds them.
- A default for `jobs` or `billing` in the page: the server's scenario says every snapshot carries both, so the fake was the fault ([D2](design.md#d2)).
- A change to the session drawer's read: no requirement demands that it skip the read before the record exists ([D3](design.md#d3)).
- The mis-bound scenarios — the *spec audit*.
- The sweep's findings after the refactor's last version.
