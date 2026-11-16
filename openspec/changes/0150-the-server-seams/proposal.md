---
bump: patch
after: [0149-the-css-files]
---

# The server's seams

What a test replaces in the UI server becomes a keyword-only parameter of `create_app`, held by the `Surface`; no test patches a name of `app.py` that a route reads, and the draft lock is each app's own.

Reading map: [design](design.md) holds the seams, the lock and the tests, [tasks](tasks.md) the jobs, the file response, the draft's four and the documents.

## Why

Tests replace names of `isekai/interface/ui/app.py` with `monkeypatch.setattr`: `Jobs`, `FileResponse`, `_precondition`, `save_draft`, `approve` and `_DRAFT_UPDATE`. A patch of a module's own name is global state, and a patch is stranded the moment the code reading it moves to a module of `routes/` ([docs D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)). The review, images, library and staging routes read these names and move in the versions after this one, so the seams come first.

The draft lock is a module-level lock, shared by every app in the process. That is why the tests swap it for a lock of their own.

The change moves no route and edits no assertion. Each seam defaults to the object the product uses today, so `serve` passes none and the product behaves as before.

## What Changes

- `create_app` takes `make_jobs`, `file_response`, `save_draft`, `approve`, `precondition` and `draft_lock`, each keyword-only with the product's own object as its default ([D1](design.md#d1)).
- The `Surface` holds `file_response`, `save_draft`, `approve`, `precondition` and `draft_lock`; the routes that read them read them there ([D2](design.md#d2), [D3](design.md#d3)).
- The module's lock `_DRAFT_UPDATE` goes: each app builds its own `threading.Lock` when none is passed ([D4](design.md#d4)).
- `_photograph` takes the file response as its first parameter, and the image routes and the source thumbnail answer through it ([D3](design.md#d3)).
- The tests pass an argument where they patched; the shared client's builder passes them on ([D5](design.md#d5)).
- One test holds that an app given no lock holds a lock of its own across a write ([D6](design.md#d6)).
- The patch ratchet's row for `isekai.interface.ui.app` falls to the patch of `run`.
- A decision says what a test replaces in the server is a parameter of `create_app`; D59's *Accepts*, `app.py`'s docstring and the interface's README follow ([D7](design.md#d7)).

No requirement is added, changed or removed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- Code: `isekai/interface/ui/app.py`, `isekai/interface/ui/surface.py`.
- Tests: `tests/test_ui.py`, `tests/test_ui_jobs.py`, `tests/test_ui_api.py` (arguments where patches were, a test added), `tests/test_ratchets.py` (a row's number).
- Replayed, not edited: `tests/mutants.json`.
- Documents: `docs/decisions.md`, `isekai/interface/README.md`, and the docstrings of `app.py` and `surface.py`.
- No format version moves, no flow is re-pinned, no frozen image file is touched, and nothing under `tests/record/` changes.

## Not in this change

- Any route's move: the review, images, library, staging and sources routes stay closures of `create_app`.
- The patch of `run`, and the app's row in the patch ratchet that stays for it: `run` is read by `serve` alone, and goes with `serve`'s collaborators.
- `serve`'s collaborators, `ensure_built` and the library's root, and the patches of `ui/library.py`, `ui/events.py` and `ui/bundle.py`.
- A mutation pre-flight over the rewritten lines: the lines are single-name substitutions, and the replay of `tests/mutants.json` closes the change ([D8](design.md#d8)).
- A seam read from the request or the environment: a seam is a Python argument, and `serve` passes none.
