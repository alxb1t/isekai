# The server's seams — design

What a test replaces in the UI server becomes a keyword-only parameter of `create_app`, held by the `Surface`, and the draft lock becomes each app's own; no route moves. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Tests replace these names of `isekai/interface/ui/app.py` with `monkeypatch.setattr`: `Jobs`, `run`, `FileResponse`, `_precondition`, `save_draft`, `approve` and `_DRAFT_UPDATE`. The patch ratchet lists the module ([docs D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets)), refuses a patch of a new module, and cannot see a patch a move has stranded. The review, images, library and staging routes read these names and move in the versions after this one, so a patch must be an argument before they do ([docs D59](../../../docs/decisions.md#d59--a-resource-is-a-class-registered-from-a-table-over-one-surface) accepts that they stay closures until then).

Evidence, at the cut's base `bc16b803`:

| fact | command | prints |
|---|---|---|
| the patches of `app.py`, per test file | `git grep -c -F "setattr(app_module" -- tests` | `tests/test_ui.py:2`, `tests/test_ui_api.py:10`, `tests/test_ui_jobs.py:1` |
| the measure the ratchet takes of them | `uv run python -c "from tests.test_ratchets import patched_modules, REPO_ROOT; print(patched_modules(REPO_ROOT)['isekai.interface.ui.app'])"` | `13`, where the row lists `12` |
| the routes that take the draft lock, which the change deletes | `git grep -c -F "with _DRAFT_UPDATE:" -- isekai/interface/ui/app.py` | `isekai/interface/ui/app.py:6` |
| the places that build a file response | `git grep -c -F "FileResponse(" -- isekai/interface/ui/app.py` | `isekai/interface/ui/app.py:7` |
| the only place `Surface` is built | `git grep -n -F "Surface(" -- isekai` | `isekai/interface/ui/app.py:276` |
| `run` is read by `serve` alone | `git grep -n -F "run(app, " -- isekai` | `isekai/interface/ui/__init__.py:93` |

The patches are `Jobs` in `tests/test_ui.py` and `tests/test_ui_jobs.py`; `FileResponse` twice and the draft's four — `_precondition`, `save_draft`, `approve` and `_DRAFT_UPDATE`, the lock the change deletes — in `tests/test_ui_api.py`; and `run` in `tests/test_ui.py`. The ratchet's `ratchet_faults` compares the keys of a table and its row count, never a row's number, so lowering a number is a convention that [D56](../../../docs/decisions.md#d56--size-and-patches-are-held-by-ratchets) states and no test holds.

## Goals / Non-Goals

**Goals**
- Each name a route reads and a test replaces is a parameter of `create_app`, and a test passes an argument where it patched.
- The draft lock is an app's own.
- The surface holds each seam a route reads, so a route that moves reads it there.

**Non-Goals**
- Any route's move, any assertion's change, anything under `tests/record/`.
- The patch of `run`, which no route reads, and `serve`'s collaborators.
- A mutation pre-flight over the rewritten lines ([D8](design.md#d8)).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `create_app` takes `make_jobs`, `file_response`, `save_draft`, `approve`, `precondition` and `draft_lock`, keyword-only, each defaulting to the object the product uses | a test's arrangement is an argument, not a patch of global state (Q103, Q127); `serve` passes none, so the product is unchanged | a parameter without a default, which changes `serve` and every other caller |
| [D2](#d2) | the `Surface` holds `file_response`, `save_draft`, `approve`, `precondition` and `draft_lock`; `make_jobs` is a parameter of `create_app` alone | a route that moves reads the surface, and the surface already holds the `Jobs` the factory built; the one reader of the factory is `create_app` (C4) | the factory as a field of the surface, which nothing reads |
| [D3](#d3) | `_photograph` takes the file response as its first parameter; the image routes and the source thumbnail call `surface.file_response`; the bundle's `page` keeps `FileResponse` | the photograph's bytes and every image leave through one seam; the page serves the built bundle, which no test replaces | the page through the seam too, which no test holds |
| [D4](#d4) | `draft_lock` defaults to a `threading.Lock` each call of `create_app` builds; `_DRAFT_UPDATE` is deleted; `_precondition` moves above `create_app` to be a default | a lock for the whole process was shared by every app in it (Q127); a default is evaluated when the `def` runs, so `_precondition` must precede it | a `None` default for the check, resolved in the body, which makes the default invisible in the signature |
| [D5](#d5) | `_client` in `tests/test_ui_api.py` takes `seams`, a mapping of parameter names to arguments, and passes them to `create_app`; the draft's tests build their app with their seams | the shared client's builder is the one place the file builds an app (Q127); a test's arrangement is not its assertion (Q6) | `**seams: Any`, which `ruff` refuses (`ANN401`) |
| [D6](#d6) | one test holds that an app given no lock holds a lock of its own across a write, with its twin as a second case | every other draft test passes its own lock, so nothing else shows the default is a real lock | none: a default of `contextlib.nullcontext()` would pass every other test |
| [D7](#d7) | a decision, D61, says what a test replaces in the server is a parameter of `create_app`; D59's *Accepts*, `app.py`'s docstring and the interface's README are amended | the documents a version makes false are amended in its diff, and a rule gets a decision (Q6) | amending the documents in the version that moves the last route |
| [D8](#d8) | the proof is the server's test files after each phase, the ratchet, the record and the layer guards, and the replay of `tests/mutants.json` in the last phase; no pre-flight runs | the brief names these (Q127, Q128); no line moves, and the rewrites substitute one name for another | a `tools.mutate` pre-flight per phase over lines the later phases rewrite, which the plan check cannot run twice |

### D1

The signature of `create_app` after the change; the parameters before `make_jobs` are as they are today:

```python
def create_app(
    root: Path,
    wired: Wiring,
    *,
    flows: Sequence[str],
    bundle: Path,
    wire: Callable[[Path], Wiring],
    host: str,
    port: int,
    make_jobs: Callable[..., Jobs] = Jobs,
    file_response: Callable[..., Response] = FileResponse,
    save_draft: Callable[..., Path] = save_draft,
    approve: Callable[..., tuple[Path | None, list[str]]] = approve,
    precondition: Callable[..., None] = _precondition,
    draft_lock: AbstractContextManager[Any] | None = None,
) -> FastAPI:
```

| parameter | default | read by |
|---|---|---|
| `make_jobs` | `Jobs` | `create_app`, where it builds `jobs` |
| `file_response` | `FileResponse` | `_photograph`, `read_render_image`, `read_render_thumb`, `read_bake_image`, `read_bake_thumb`, `read_source_thumb` |
| `save_draft` | `save_draft` of `isekai.pipeline.review` | `put_draft` |
| `approve` | `approve` of `isekai.pipeline.review` | `post_approve` |
| `precondition` | `_precondition` of `app.py` | `put_draft`, `post_approve`, `post_discard` |
| `draft_lock` | a new `threading.Lock` | `put_draft`, `post_approve`, `post_cancel`, `post_discard`, `post_draft`, `delete_render` |

`create_app`'s docstring gains one line per seam. A seam is a Python argument: no request and no environment variable names one, and `serve` passes none ([D41](../../../docs/decisions.md#d41--the-test-seam-is-a-factory-named-in-the-environment) stays the one environment seam).

### D2

`Surface.__init__` gains `file_response`, `save_draft`, `approve`, `precondition` and `draft_lock`, keyword-only and required, and stores each under its own name. `surface.py` imports no web framework, so `file_response` is typed `Callable[..., Any]`; the others are typed as in D1, with `Callable[..., None]` for `precondition`. `create_app` passes the arguments it took, and builds `Jobs` by `make_jobs(...)` with the arguments it passes today.

The brief's Q127 holds the jobs' factory as a field of the surface. The surface already holds the `Jobs` the factory built, and the factory has one reader, so C4 keeps it a parameter alone.

### D3

`_photograph(file_response, path, *, other=None)`: the body is as it is but for `FileResponse(path, media_type=kind, headers=headers)` becoming `file_response(path, media_type=kind, headers=headers)`. Its callers `read_staged`, `read_photo`, `read_source_copy` and `read_source` pass `surface.file_response`.

The image routes and the source thumbnail answer `surface.file_response(...)` with the arguments they pass today, and their return annotation `-> FileResponse` becomes `-> Response`: the seam returns a `Response`, as `read_photo`'s annotation already says. `page` and the assets' mount are the built bundle's, not the library's files, and keep `FileResponse`.

### D4

After the change the module holds neither the lock nor its comment. In `create_app`, `draft_lock if draft_lock is not None else threading.Lock()` is passed to the surface, and each route [D1](design.md#d1) lists writes `with surface.draft_lock:` where it wrote the deleted `with _DRAFT_UPDATE:`. Each call of `_precondition` becomes `surface.precondition(...)`, `save_draft(` in `put_draft` becomes `surface.save_draft(`, and `approve(` in `post_approve` becomes `surface.approve(`.

`_precondition`, with its docstring unchanged, moves to sit between `authorities` and `create_app`. Moving it shifts no mutant: the entries of `tests/mutants.json` are addressed by path and exact text.

### D5

A patch becomes an argument, and no assertion changes:

```
before  monkeypatch.setattr(app_module, "Jobs", make_jobs)
after   create_app(..., make_jobs=make_jobs)

before  monkeypatch.setattr(app_module, "FileResponse", record)
after   _client(wired, made, tmp_path, seams={"file_response": record})
```

In `tests/test_ui_api.py`:

- `_client(wired, made, tmp_path, *, drafted=True, offered=OFFERED, seams=None)` calls `create_app(..., **(seams or {}))`.
- The address tests build their client with the recorder each patched `FileResponse` with, as above.
- `_overlap` and `_update_during_approval` take `wired`, `made` and `tmp_path` where they took `client`, and build their client with `seams` holding the wrappers they patched. `_overlap` passes `precondition`, `save_draft` and `draft_lock`; `_update_during_approval` passes `precondition`, `approve` and `draft_lock`.
- In each the order is the wrappers, then the client, then `body = client.get(...)`: the wrappers are closures that read `body` only when a request calls them.
- Each wrapped the real object it read from `app_module`: now `app_module._precondition` still, and the `save_draft` and `approve` the file already imports from `isekai.pipeline.review`. The lock they wrapped was the module's; each now builds a `threading.Lock()` of its own to wrap.
- `unlocked` passes `contextlib.nullcontext()` as `draft_lock`, and the twins drop their own patch of it. `review_module.write` is a patch of another module and stays.

In `tests/test_ui.py` and `tests/test_ui_jobs.py` the test passes `make_jobs=make_jobs` to `create_app`, as above.

### D6

`test_an_app_given_no_lock_holds_one_of_its_own` in `tests/test_ui_api.py`, bound to `ui:draft-update:overlapping-updates-cannot-both-commit`, with a case each for `draft_lock` absent and `draft_lock=contextlib.nullcontext()`.

- It builds the app with a `save_draft` seam. On its first call only, as `_overlap`'s `write` does, the seam starts a second update on its own thread, waits for it, records whether it is still running, then writes through the real `save_draft`.
- Neither update carries a `saved`, so `_precondition` returns at once and both answer `200`.
- With no lock argument the wait is a quarter of a second and the second update is still waiting at the lock while the first writes. With `nullcontext()` the wait is `WAIT`, the file's own bound, and the second update has finished.
- A missing lock fails the first case. The quarter of a second only ever lets a broken lock pass, never a sound one fail, and the twin's wait is long enough to ignore load.

### D7

The decision, added to `docs/decisions.md` after D60 under *Code and environment* (`0149` adds D60), numbered the next free (D61 at the cut):

```
### D61 · What a test replaces in the server is a parameter of create_app

**`create_app` takes, as keyword-only parameters each defaulting to the object the product uses, what a test replaces: the jobs' factory, the file response, `save_draft`, `approve`, the precondition check and the draft lock. The `Surface` holds each but the factory, a route reads it there, and the draft lock is the app's own.**

- **Why:** a patch of a module's own name is global state that a route moving to another module leaves stranded ([D56](#d56--size-and-patches-are-held-by-ratchets)), and one lock for the process was shared by every app in it.
- **Accepts:** `run` stays a name a test patches in `app.py`, because `serve` reads it and no route does. Reopen when `serve`'s collaborators are parameters.
- **Made by:** `0150`.
```

D59's *Accepts* line and *Made by* line are amended as [tasks](tasks.md) 4.3 gives them. `app.py`'s docstring says `create_app` takes what a test replaces and declares the routes that read it, and the rest. The `ui/surface.py` and `ui/app.py` rows of `isekai/interface/README.md` name the seams, as 4.6 gives them.

### D8

`CONTRIBUTING.md` asks a change that rewrites lines of `isekai/` for `tools.mutate` over them, before and after.

- The brief settles this version's proof as the server's test files at every phase and the replay of `tests/mutants.json` at the last.
- The rewrites are one name for another in routes the server's test files hold.
- No entry of `tests/mutants.json` sits in them: UA-7 is anchored at the artifacts import block, UA-1a, UA-1b and UA-2 at the middleware and `allowed`, and PB-2c at `definition=one.flow,`, none of which a phase edits.
- The person may ask for a pre-flight; the cut plans none.

## Tests

The change adds a test and removes none. No assertion of an existing test changes: a test's arrangement moves from a patch to an argument, as [D5](design.md#d5) says.

| layer | tests added | tests removed | command |
|---|---|---|---|
| unit (pytest) | `test_an_app_given_no_lock_holds_one_of_its_own`, two cases | none | `git grep -c "^def test_an_app_given_no_lock_holds_one_of_its_own" -- tests/test_ui_api.py` prints `tests/test_ui_api.py:1` |
| browser (vitest) | none | none | `git diff --name-only bc16b803 -- 'ui/src/*.test.ts'` prints nothing |
| end-to-end | none, so no run on any engine | none | `git diff --name-only bc16b803 -- tests/e2e` prints nothing |

- **Why a unit test, and why this one:** the test sits with the draft's other tests, at the lowest layer that can fail for a missing lock (T1). Every other draft test passes a lock of its own after the change, so only this one would fail if the default were no lock.
- **The twin:** the second case, with `contextlib.nullcontext()`, is the guard's own twin, a step in the guard's test and no new test (T6).
- **Edited, no assertion changed:** `tests/test_ui.py` and `tests/test_ui_jobs.py` (the jobs' factory), `tests/test_ui_api.py` (the file response and the draft's four) and `tests/test_ratchets.py` (the app row's number). Each stays green only through the argument it now passes, and each phase's task names the test it re-arranges.
- **Replayed or held, not edited:** `tests/mutants.json` is replayed and `tests/record/` is held unchanged, in the last phase.
- **Deleted or merged:** no test, so there is no table of what carries its assertions.

## Dependencies

None.

## Risks / Trade-offs

| risk | held by |
|---|---|
| a route still reads a name the change deleted | `ruff check` and `ty check` name an undefined name, and the server's tests reach each route |
| a seam's default differs from today's object | each default is the imported name itself, and the whole server suite runs on the defaults |
| the default lock is no lock and no test notices | D6's test |
| an app built with no lock argument shares a lock with another | `threading.Lock()` is called in the body of `create_app`, never in a default |
| a seam is reachable from outside the process | a seam is a Python argument; `serve` passes none, and no request or environment variable names one |
| the patch ratchet's row falls and no test checks the number | task 3.9 sets the row to the patch left, and task 3.10 prints the measure |
| the rewritten lines get no mutation pre-flight | [D8](design.md#d8): the replay and the server's test files hold them, and the person may ask for more |
| `0149` has not released when this builds | `after:` holds the build behind it, and D61 follows D60 |

## Verdict

Ready to build. The phases are the jobs, the file response, the draft's four and the documents; each phase but the last ends with no patch of the names it took.
