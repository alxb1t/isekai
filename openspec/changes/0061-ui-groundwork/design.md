# Design — 0061 ui groundwork

How `isekai ui` becomes the shell over a library — Home, the hub, Review inside it — with a browser test harness
that reaches no GPU and no Ollama. **Verdict: feasible** — the server already calls the stage functions in process,
and the library is a directory listing over run directories the pipeline already reads; the new parts are the routes,
the listing and the harness.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `45babd9` (`v0.36.0`):

- **The verb:** `ui` takes `photos`, `--runs`, `--flow` through `_OneFlow` and `--port`
  (`isekai/interface/cli.py:120-127`, `:162-182`, `:216-229`); `DEFAULT_PORT = 8517` (`:93`). `run()` sends `ui` to
  `_ui` before any flow is resolved (`:378-383`).
- **The server:** `serve(wired, flow, identifiers, *, port)` calls `establish(..., bundle=ensure_built)` before binding
  (`isekai/interface/ui/__init__.py:33-55`); `batch.py` holds `Input`, `Batch`, `establish` and `_prepare`
  (`isekai/interface/ui/batch.py:47`, `:68`, `:140`, `:185`). `app.py`'s routes are `/api/batch`, `/api/tags`,
  `/api/fields`, `/api/inputs/{identifier}` with `/photo`, `/draft` and `/approve` (`isekai/interface/ui/app.py:160-354`),
  the bundle mounted at `/` (`:373`).
- **The guard:** `_addressed_here` checks `Host`, and `Origin` only when sent (`app.py:129-153`, `:150-151`).
- **Commands a page prints:** `_remedy` adds `--runs` off the default root (`app.py:480-497`);
  `caption_command` does not (`app.py:280-282`).
- **The bundle:** `ensure_built` builds with `subprocess.run([BINARY, "run", "build"], ..., timeout=BUILD_TIMEOUT)`,
  no process group (`isekai/interface/ui/bundle.py:93-146`, `:121-135`).
- **The page:** `ui/src/ReviewApp.vue` with `useSheet`, `useBatch`, `useApproval`, `useVocabulary`; `ui/package.json`
  pins `vue 3.5.43`, no router and no test runner.
- **The wiring:** `wiring_from(*, runs, server=None)` runs `_check_run_root` and builds the real `Wiring`
  (`isekai/interface/wiring.py:259-283`); `trackable` and `_check_run_root` decide D18 (`:196-222`).
- **The doubles:** `tests/fakes.py` (`FakeComfyClient`, `stub_comfy`), `tests/stages.py` (`FakeSession`,
  `fake_tagger`, `fake_wd14`); no module under `isekai/` imports `tests/`.
- **The bindings:** `tests/test_spec_bindings.py` reads `@pytest.mark.spec` with `ast`; a key an open delta adds is
  known and not yet demanded. CI sets `ISEKAI_VOCABULARY: absent`, and the checks that read the vocabulary skip.
- **The skills:** `.claude/skills/run-flows/` and `.claude/skills/compare-renders/`; `tests/test_agent_skills.py`
  parses every command they name.
- **The defects**, each re-read at the cut:

  | card | where |
  |---|---|
  | 0018·R5 | `ui/src/composables/useSheet.ts:92-93` against `:133-135`; the watcher `ui/src/ReviewApp.vue:385-397` |
  | 0018·R8 | `ui/src/ReviewApp.vue:156`, `:161`; `ui/src/composables/useBatch.ts:42-45` |
  | 0018·R12 | `ui/src/api.ts:32-38`; `ui/src/ReviewApp.vue:367-373` |
  | 0023·R5 | `isekai/interface/ui/bundle.py:121-135` |
  | 0023·S1 | `isekai/interface/ui/app.py:150-151` |
  | 0032·R1 | `isekai/interface/ui/app.py:280-282` |

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_ui.py` | 19 | `grep -c "def test_" tests/test_ui.py` |
| tests in `tests/test_ui_api.py` | 39 | `grep -c "def test_" tests/test_ui_api.py` |
| tests in `tests/test_agent_skills.py` | 2 | `grep -c "def test_" tests/test_agent_skills.py` |
| lines in `ui/src` | 2067 | `cat ui/src/*.vue ui/src/components/*.vue ui/src/composables/*.ts \| wc -l` |

## Goals / Non-Goals

**Goals:** one server over the library; Home, the hub and Review as routes per the [design spec](design-spec.md);
every screen tested in a browser on doubles; the carried defects closed with a test each.

**Non-Goals:** writing anything a stage does not already write — no tick, no import, no prepare, no render; an
event stream; a change to a flow, a sheet, the prompt or the image; moving any `.data/` batch.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `isekai ui [--port N]`, nothing else, over `ISEKAI_LIBRARY` (default `~/isekai`), created on start; D18 holds for the library | the operator never types a path; a library holds photographs | `--library`; keeping `--flow` and run ids |
| [D2](#d2) | a library folder is a batch when it holds `sources/`; its runs root is `<batch>/runs`; one `Wiring` per batch through `wiring_from` | layout alone decides, so no marker file can lie; `wiring_from` keeps D19 | a `batch.json`; a flat `runs/` |
| [D3](#d3) | `vue-router` in history mode; the server answers `/api/…` and returns `index.html` for every other path; runs named by their digest | a reload lands where it was; a slug can repeat | a hash router; a hand-rolled router |
| [D4](#d4) | the hub is a listing: stage per source × tracked flow from the run directory's names; an unreadable file marks its cell; it writes nothing | every stage is already decided by a listing | storing stages |
| [D5](#d5) | Review moves inside the shell; its queue is the first flow's unapproved sheets in hub order; opening a sheet with no draft calls `review` | approving is the only step between sheets; `review` owns the draft | drafts at server start |
| [D6](#d6) | `ISEKAI_WIRING=<module>:<factory>` replaces `wiring_from` when set, imported then and only then; the doubles stay in `tests/` | production never names `tests/`; CI has no vocabulary and no models | `ISEKAI_WIRING=fake` with the fakes moved into `isekai/` |
| [D7](#d7) | Playwright from pytest (`pytest-playwright`), Chromium, under `tests/e2e/`, `Layers: e2e`; vitest under `ui/src/**/*.test.ts`, bound by `spec("<key>", …)`, run by `tools.test_ui` in the gate | one binding rule for every test; the gate stays `make gate` | `@playwright/test`; JS tests left unbound |
| [D8](#d8) | close 0018·R5, R8, R12, 0023·R5, 0023·S1, 0032·R1; retire 0024·R10 | each lives where this change rewrites | deferring them to the next UI change |
| [D9](#d9) | delete `run-flows`, `compare-renders` and the `agent-skills` capability; `compare` stays a verb | the UI is the tool; the review step cannot follow the library | rewriting `run-flows` onto the library |
| [D10](#d10) | the [design spec](design-spec.md) moves to `ui/design/spec.md`; the old `ui/design/` goes; D4, D18, D19, D24 edited, D40 and D41 added | a decision in force is edited where it lives | keeping the imported design beside the spec |

### D1

`ui`'s parser keeps `--port` and loses `photos`, `--runs` and `--flow`; `_OneFlow` goes. `serve(port=)` reads
`ISEKAI_LIBRARY` from the environment, expands `~`, creates the directory, and refuses through `trackable` a library
inside the working tree and outside `.data/`, naming `ISEKAI_LIBRARY`. `.env.example` declares the key, commented.

```
uv run --env-file .env python -m isekai ui     ──▶  http://127.0.0.1:8517/
  ISEKAI_LIBRARY unset ──▶ ~/isekai, created
  ISEKAI_LIBRARY=./lib (inside the repo) ──▶ refused before binding
```

### D2

`isekai/interface/ui/library.py` replaces `batch.py`. It lists the library, names each folder a batch or not
(`sources/` decides), skips dot-folders, and for a batch reads its sources, its runs and each row's figures per
[`ui:batch-folder`](specs/ui/spec.md). A request for one batch builds that batch's `Wiring` with
`wiring_from(runs=<batch>/runs)`, so `_check_run_root` runs on every batch. Last activity is the newest `st_mtime`
under the batch.

### D3

Routes per [design spec §4](design-spec.md#4--routes), less the renders and the session. The API, every path under one
batch:

```
GET  /api/library
GET  /api/b/{batch}/hub
GET  /api/b/{batch}/review/{digest}/{flow}          the input payload today's /api/inputs/{id} carries
GET  /api/b/{batch}/review/{digest}/{flow}/photo
PUT  /api/b/{batch}/review/{digest}/{flow}/draft
POST /api/b/{batch}/review/{digest}/{flow}/approve
GET  /api/tags   ·   GET /api/fields?flow=
```

Any other `GET` returns `ui/dist/index.html`, so a deep link loads the shell. A digest that matches no run, or a
batch the library does not hold, is a `Refusal` the page shows with the way back.

### D4

A cell's stage is the furthest of: `review/` holds an approval with outputs → `rendered ×n`; an approval →
`approved`; a draft → `draft`; `sheets/` → `sheet`; `wd14/` → `tagged`; the flow's directory alone → `assigned`; no
directory → no flow. A file that raises `Refusal` when read marks the cell `unreadable` with its message. Columns are
the tracked flows `wired.flows_dir` holds; any other directory under a run is skipped.

### D5

`ReviewApp.vue`'s surface becomes the `Review` route's view; the rail lists the queue. Opening a sheet calls
`review(run, flow)` when the flow has a sheet and no draft, as `_prepare` does today at startup. After Approve the
page reads the hub; a `Refusal` there shows in the approve bar (0018·R8); the next sheet in the queue opens, or the
hub after the last.

### D6

```
wiring_from(runs=…)
   ISEKAI_WIRING unset ──▶ the real Wiring, as today
   ISEKAI_WIRING=tests.e2e.wiring:fake ──▶ importlib → fake(runs=…) ──▶ a Wiring on doubles
```

`fake` builds the `Wiring` with `FakeComfyClient`, `fake_tagger`, a stub reader and a small fixed vocabulary, after
the same `_check_run_root`. The import sits inside the function, so `python -m isekai`'s import graph is unchanged
(D20, the `-S` guard).

### D7

- **Playwright:** a session fixture in `tests/e2e/conftest.py` builds a library in `tmp_path` from fixture runs,
  starts `python -m isekai ui --port <free>` with `ISEKAI_LIBRARY` and `ISEKAI_WIRING` set, waits for the address,
  and stops it. Tests carry `@pytest.mark.spec`. Chromium only (T4: the shell is one client).
- **vitest:** `ui/src/test/spec.ts` exports `spec(key, fn)`, a `test` named by its key. `tests/test_spec_bindings.py`
  reads `spec("…")` from `ui/src/**/*.test.ts` beside the pytest markers. `tools/test_ui.py` runs `npm run test` and
  refuses by name without `ui/node_modules/`, as `tools.typecheck_ui` does.
- **Browsers:** `make browsers` runs `uv run playwright install chromium`; CI runs it before `make gate`.

### D8

| card | fix | proved by |
|---|---|---|
| 0018·R5 | each save takes a token; `saving` clears when the last token answers, never on `open()` | `ui:save:a-stale-save-cannot-clear-saving` (vitest) |
| 0018·R12 | the draft `PUT` sets `keepalive: true`; the router's leave guard and `beforeunload` flush | `ui:save:a-pending-edit-is-sent-on-leaving` (vitest) |
| 0018·R8 | the post-approve read is caught and shown in the approve bar | `ui:queue:a-failure-after-approval-is-shown` (e2e) |
| 0023·R5 | `Popen(..., start_new_session=True)`; on timeout `os.killpg` the group, then refuse | `ui:bundle:an-unfinished-build-is-stopped-and-named`, its test made to see the group stopped |
| 0023·S1 | without `Origin`, refuse unless `Sec-Fetch-Site` is `same-origin`, `none` or absent | `ui:address:a-cross-site-request-without-origin-is-refused` |
| 0032·R1 | `caption_command` goes through `_remedy`, which always names `--runs` | `ui:source:a-missing-caption-names-its-command` |

0024·R10 retires with the closing manifest, which the queue's end on the hub replaces.

### D9

Delete `.claude/skills/run-flows/` and `.claude/skills/compare-renders/`; the REMOVED requirement takes
`agent-skills` out of the living spec at release. Comments naming the skill are reworded: `compare_view.py:38`,
`tests/test_render.py:570`.

### D10

Copy the change's `design-spec.md` to `ui/design/spec.md` and delete the rest of `ui/design/`; the change keeps its copy. Edited in
`docs/decisions.md`: D4 → *the UI runs no stage* (nothing in the browser writes beyond review); D18 → the library is
held to the runs-root rule; D19 → `ISEKAI_WIRING` is the one way past `wiring_from`; D24 → `Sec-Fetch-Site` closes
the no-`Origin` case. Added: **D40 · A batch is a library folder holding `sources/`**; **D41 · The test seam is a
factory named in the environment**. Also `README.md`, `CLAUDE.md` (the `e2e` sentence in *The quality gate*, the
intro's `ui` clause), `docs/data-flow.md` (the `ui` paragraph), `docs/modules.md`, `isekai/interface/ui/README.md`.

## Tests

| layer | added | removed | where |
|---|---|---|---|
| unit, pytest | a test per new `unit` scenario in [the ui delta](specs/ui/spec.md) and per new scenario under a modified requirement | the startup and batch tests in `tests/test_ui.py`; `tests/test_agent_skills.py` | `tests/test_ui.py`, `tests/test_ui_library.py`, `tests/test_ui_api.py` |
| unit, vitest | `ui:save:*` | — | `ui/src/composables/*.test.ts` |
| e2e, Playwright | `ui:routes:*`, `ui:queue:*` (less the draft), a characterisation of today's surface | — | `tests/e2e/` |

**End-to-end runs added:** the `e2e` scenarios of the ui delta, each once, on Chromium. Each is end-to-end because
only a browser shows it (T1): a reload, a route's refusal, the page moving after Approve. The characterisation tests
extend the same session fixture (T2).

| removed or merged | its assertions and scenario ids now carried by |
|---|---|
| `tests/test_ui.py` tests bound to `ui:startup:untracked-flow-is-refused`, `ui:startup:input-without-a-sheet-is-refused`, `ui:startup:refusals-are-reported-together` | none: the requirement is REMOVED; an untracked flow is ignored per `ui:hub:an-untracked-flow-is-ignored` |
| `tests/test_ui.py` test bound to `ui:startup:a-draft-is-opened-for-each-input` | `ui:queue:opening-a-sheet-writes-its-draft` |
| `tests/test_ui.py` tests bound to `ui:batch:no-batch-artifact-is-written`, `ui:batch:approved-count-comes-from-disk` | `ui:batch-folder:no-file-records-a-batch`, `ui:batch-folder:a-flows-counts-are-of-its-sources` |
| `tests/test_pipeline_cli.py` tests bound to `cli:flow-selection:a-serving-verb-takes-one-flow` | `ui:library:the-verb-takes-no-arguments` |
| `tests/test_agent_skills.py` — `test_every_command_a_skill_names_parses`, `test_a_skill_naming_a_flag_the_parser_refuses_is_reported` | none: the requirement is REMOVED with the skills |

## Dependencies

| package | where | constraint | why |
|---|---|---|---|
| `vue-router` | `ui/package.json` `dependencies` | `5.4.0` | the routes ([D3](#d3)) |
| `vitest` | `ui/package.json` `devDependencies` | `5.0.5` | the composables' timing defects ([D7](#d7)) |
| `pytest-playwright` | `pyproject.toml` `[dependency-groups] dev` | `==0.10.0` | browser tests in pytest ([D7](#d7)); it brings `playwright` `1.64.0` |

Chromium is fetched by `make browsers`, never by the gate.

## Risks / Trade-offs

- **[Risk]** the bundle needs node at runtime and the e2e fixture builds it → the gate already requires
  `ui/node_modules/`; `ensure_built` builds once per tree.
- **[Risk]** e2e tests are slower and can flake → one engine, one server per session, waits on the page's own state,
  never on time.
- **[Risk]** a library-wide server lists more photographs → D24's guard now covers the no-`Origin` case (0023·S1).
- **[Trade-off]** run-flows is gone before the UI can prepare or render → the verbs cover both until the UI does.
- **[Risk]** `agent-skills` leaves the living spec with no requirement → `mf-release` deletes
  `openspec/specs/agent-skills/` when it folds the delta.

## Migration Plan

- `isekai ui --flow …` and its run ids stop parsing; the README and `docs/data-flow.md` move to `isekai ui`.
- A `.data/<batch>` opens once moved into the library with `photos/` renamed `sources/`; this change moves none.
- Rollback: revert the branch; no run file's format moves.

## Verdict

**Feasible.** Every write the new screens make is a write the review surface already makes, through the same
functions; the library and the hub are listings; the harness runs on doubles the suite already has.
