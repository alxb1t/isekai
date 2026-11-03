# Design — 0093 the tests revisited

The binding rule, the rule of extending, the socketless and clockless rewrites, and the browser merges.
**Verdict: feasible.**

## Context

`tests/test_spec_bindings.py` reads markers statically and fails a test whose markers are not exactly one
(`unmarked`, `len(markers) != 1`). `tests/e2e/` holds 29 tests, one `served` server for the session and a fresh browser
context per test; CI runs them as `make e2e`, out of the gate. The `Makefile`'s `LOOPBACK` keeps two unit tests that
serve on `127.0.0.1` out of the gate too.

## Goals / Non-Goals

**Goals:** a step carries its key; fewer browser contexts; nothing in the gate binds a socket or reads the wall clock
for its verdict.

**Non-Goals:** any change to the app; the browser tests in the gate.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| <a id="d1"></a>**D1** | A test carries one or more `spec` markers, or exactly one `spec_exempt`, never both: `unmarked` fails no marker, a marker not read, or `spec_exempt` beside another; `test_every_test_carries_one_marker` becomes `test_every_test_carries_its_keys_or_its_exemption`, its twin adding a test with two `spec` markers, which passes. `spec()` in `ui/src/test/spec.ts` takes a key or an array of keys, named by them joined; `_VITEST_SPEC` reads both forms. `CONTRIBUTING.md` and `CODING_STANDARDS.md` say each behaviour a test holds carries its key, and that pytest warns on an unregistered marker | a step that adds a behaviour must carry its key | one marker a test |
| <a id="d2"></a>**D2** | `CODING_STANDARDS.md`'s *Project rules* gain *Extend before adding*: a new case goes into an existing test that reaches the same state; a new browser test names, in its commit, why none fits | a browser test's setup is most of its cost | |
| <a id="d3"></a>**D3** | `test_the_report_reaches_the_loopback_with_a_proxy_exported` dials through a connection like `RefusingConnection` (`tests/transports.py`) that answers `/system_stats` and records its host, so no server binds. `test_sigint_ends_streams_without_cancellation_output` calls the server's `handle_exit` on a running loop with streams open and asserts each ends and the job is interrupted, in-process; the `Server` subclass in `isekai/interface/ui/app.py` lifts to module scope for it. `LOOPBACK` leaves the `Makefile`, and `make gate` runs both | the privacy guard and the quiet stop stay held, and nothing in the suite serves | dropping either test |
| <a id="d4"></a>**D4** | The watchdog tests patch `render.threading.Timer` with a recording subclass and assert its `cancel()` ran and `kill` never did; the bundle-timeout test's stand-in holds a FIFO in `tmp_path` that `_stops` reads to EOF, in place of `ps`; `_overlap` in `tests/test_ui_api.py` waits on events, not `checked.wait(0.5)` | a unit test's verdict reads no wall clock | longer waits |
| <a id="d5"></a>**D5** | The browser tests reaching one state merge, per [Tests](#tests); each merged test carries both keys. The drawer's step narrows the viewport with `page.set_viewport_size`, so one photograph's grid sets the width; `ui:compare:the-pick-holds-its-width` and `ui:sessions:the-drawer-fits-its-widest-grid` return. The import test gains `0091·R4`'s step (no file removed while a commit is in flight) and `0091·R9`'s (Import disabled while a removal is in flight). `tests/e2e/conftest.py` names its order couplings: `test_prepare.py` relies on RENDER's Render, and `test_routes.py` reads the draft `test_review.py` writes | about ten fewer contexts | a bigger fixture collection |

## Tests

| layer | adds | removes |
|---|---|---|
| unit | the binding twin's two-marker case | none; the loopback tests return to the gate |
| end-to-end | none: steps in existing tests | the ten below, merged |

`tests/e2e/` holds 29 tests (`grep -c '^def test_' tests/e2e/*.py` at `5cc0174`), on Chromium alone; this change leaves 19.

| removed test | its key | carried by |
|---|---|---|
| `test_confirming_the_dialog_opens_the_session` | `ui:render:the-confirmation-starts-the-render` | `test_the_render_dialog_opens_on_its_checkbox` |
| `test_a_source_opens_in_the_viewer` | `ui:renders:a-source-opens-in-the-viewer` | `test_an_image_opened_from_the_grid_shows_the_approval_it_came_from` |
| `test_the_source_cell_opens_its_photograph` | `ui:hub:the-source-cell-opens-its-photograph` | `test_a_rendered_cell_opens_its_newest_image` |
| `test_side_by_side_shows_the_pair` | `ui:revise:side-by-side-shows-the-pair` | `test_discard_asks_before_it_deletes` |
| `test_side_by_side_sets_the_image_beside_its_photograph` | `ui:compare:side-by-side-sets-the-image-beside-its-photograph` | `test_compare_shows_both_versions_of_a_seed_each_under_its_head` |
| `test_a_command_waits_until_the_field_is_left` | `ui:keys:a-command-waits-until-the-field-is-left` | `test_the_photograph_opens_in_the_viewer` |
| `test_an_unknown_collection_is_refused_with_the_way_back` | `ui:routes:an-unknown-batch-is-refused` | `test_a_reload_lands_on_the_same_hub_and_the_same_review` |
| `test_cancel_approve_opens_the_sheet_again` | `ui:review:cancel-approve-opens-the-sheet-again` | `test_approve_stays_on_the_sheet` |
| `test_import_is_disabled_naming_how_many_are_read_until_all_are` | `ui:sheet:import-waits-for-reading` | `test_each_chosen_file_shows_its_upload_then_its_result` |
| `test_a_commit_in_flight_holds_the_sheet` | `ui:sheet:a-commit-in-flight-holds-the-sheet` | `test_importing_a_new_collection_opens_its_hub_with_every_source_unassigned`, holding the commit before it lands |

## Dependencies

None.

## Risks / Trade-offs

- **The merges are run by CI, not the build** → the build collects `tests/e2e`; a red CI is a patch.
- **A merged test fails for either behaviour** → each step names what it asserts, and the keys say which scenario broke.
- **`handle_exit` in-process no longer sees uvicorn print** → its quiet exit is uvicorn's; the streams ending and the
  job's interrupt are isekai's, and those stay held.

## Verdict

**feasible.** Every file and test named exists at `5cc0174`, and no behaviour moves.
