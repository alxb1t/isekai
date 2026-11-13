# The server — design

The server's half of the front ends is held by tests that read the wrong evidence. This change reads it right and pins it with mutants, and no product file changes. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The audit ran each test against mutants of the product; the gaps below survived or never ran, read at the cut, at `d6e88dc3`. `0135-the-paydown` adds the replay mode `--edits`, `tests/mutants.json` and `make mutants`, and `0136-the-cli-and-the-session` fills the file with its own entries. Phase 6 uses both.

| gap | where it lives at the cut |
|---|---|
| a failed window close raises no alert that a test sees; a second job after one ended is never asked; the render slot's steps and images read from the verb's lines are unread | `isekai/interface/ui/jobs.py` `_run_render`, `_render_child`, `_refuse_running`; `tests/test_ui_jobs.py` |
| the guard is shown to refuse, never to refuse before the handler; no request is sent with `localhost` or `[::1]` as its `Host` | `isekai/interface/ui/app.py` `_addressed_here`, `authorities`; `tests/test_ui_api.py` |
| the refusals of a malformed body, and an upload refused by its declared length, are driven by no test | `isekai/interface/ui/app.py` `post_assign`, `post_commit`, `post_quote`, `post_render`, `post_draft`, `put_file`, `_images`, `_taken_out`, `_renders` |
| no pytest posts Prepare or Stop; `unprepared` is held by one browser test | `isekai/interface/ui/app.py` `post_prepare`, `post_stop`; `isekai/interface/ui/library.py` `unprepared`; `tests/e2e/wiring.py` |
| the billing poll and its alert run in no test; the stream's collection filter and heartbeat are unheld | `isekai/interface/ui/billing.py` `alerting`, `watch`; `isekai/interface/ui/events.py` `stream`; `tests/test_ui.py` |
| no test imports `api.ts`; the bodies it builds are never compared with the server's key tuples | `ui/src/api.ts`; `isekai/interface/ui/app.py` `OUTLINE_KEYS`, `INK_KEYS`, `STAGE1_KEYS`, `PREVIEW_KEYS`, `PROPOSE_KEYS`, `BAKE_KEYS` |

```
 jobs.py ─ slot · close · lines                          (phase 1)
 app.py guard · bodies · upload                          (phase 2)
 app.py Prepare · Stop · library.unprepared              (phase 3)
 billing.py poll · events.py stream                      (phase 4)
 api.ts ──▶ ui/src/test/wire.json ◀── app.py key tuples  (phase 5)
 tests/mutants.json ◀── mutants.json                     (phase 6)
```

## Goals / Non-Goals

**Goals**
- A request the guard refuses changes nothing on disk, and every loopback spelling of the bound port is answered by the middleware.
- The alert a failed close must raise, the second job after an ended one and the render slot's record are read in process.
- Prepare and Stop are posted over HTTP, against a child that is real and held on a file.
- The poll and the stream's filter are run, and the page's bodies and the server's key tuples are compared.
- Each finding's mutant dies, and stays dead: `tests/mutants.json` holds it.

**Non-Goals**
- A product edit. The poll that dies silently when a check raises needs one, so the refactor's *the server* makes it.
- A requirement, a format version, a flag, a verb, or a decision in force. `docs/decisions.md` is not edited.
- The render route over HTTP with a running child.
- Moving a test to a faster seam. The existing jobs tests keep their real children.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | Each finding is held at the lowest layer that fails for its mutant: `Jobs`, `stream` and `Billing` in process, a route over `TestClient` | a layer above costs seconds and hides the line | an end-to-end test for each |
| [D2](#d2) | The guard's "before the handler" is read from the disk: a foreign `Host` or `Origin` on a write leaves the run unchanged | a middleware that runs the handler and then answers 403 keeps a status test green | asserting the status again |
| [D3](#d3) | The refusals of a malformed body are one parametrized test over the routes, and the render confirmation's are one beside the quote tests | each is a line of its route; a test each repeats the setup | a test per route |
| [D4](#d4) | Prepare and Stop run over HTTP against the real `prepare` verb under `ISEKAI_WIRING`, its reader held on a file | the browser tests' own seam; a child waiting on a file is not load-bound | a fake `Jobs` command |
| [D5](#d5) | The poll is run on a short interval over the gpunit double, its consults of the session counted | a wall-clock wait for "no more asks" is the flake the series removes | `time.sleep` |
| [D6](#d6) | The page's bodies are held by `ui/src/test/wire.json`, read by a vitest over `api.ts` and a pytest over the key tuples | the first file both suites share; nothing compares them today | a TypeScript type, which no runtime reads |
| [D7](#d7) | Scenarios are added under the requirements that demand them | a patch adds a scenario under a requirement, never a requirement | `skip_specs`; a MODIFIED SHALL |
| [D8](#d8) | Phase 6 adds the change's mutants to `tests/mutants.json`; those in `api.ts` are held by their vitest alone | the replay runs Python's tests | the change directory alone |

### D1

The tests extend the files that hold each subject. A mutant's test file is named in [mutants.json](mutants.json), and the replay runs that whole file. No test is deleted, so [Tests](#tests) holds no table of removals.

### D2

`test_a_request_carrying_someone_elses_host_is_refused` and `test_a_write_carrying_another_pages_origin_is_refused` each send a draft update a handler would accept: the body `test_a_draft_update_lands_on_disk_and_returns_a_receipt` sends. Each takes `snapshot(made.path)` before and asserts it equal after, with the status and the reason it asserts now. `test_every_loopback_alias_of_the_bound_port_is_answered` keeps its assertions on `authorities` and sends `Host` as `localhost:<port>` and `[::1]:<port>` to a read, and a draft update with `Origin: http://localhost:<port>`.

```
 PUT …/draft  Host: evil.example     ─▶ 403 {"refusal": "not addressed here"}   run unchanged
 PUT …/draft  Origin: evil.example   ─▶ 403 {"refusal": "not from this page"}    run unchanged
 GET /api/library  Host: localhost   ─▶ 200
 PUT …/draft  Host+Origin: localhost ─▶ 200
```

### D3

The routes and what each refuses, by the message the product prints:

| route | body | refusal holds |
|---|---|---|
| `POST /api/c/<c>/assign` | `{"flow": "nope", "sources": []}` | `not a flow this surface offers` |
| the same | `{"flow": <offered>, "sources": "ada.jpg"}` | `` `sources` is not a list of source names `` |
| `POST /api/staging/<id>/commit` | `{"as_is": "x"}` | `` `as_is` is not a list of file names `` |
| `POST /api/render/quote` | `{"collections": "b"}` | `the quote names no list of collections` |
| the same | `{"collections": ["b"], "without": "x"}` | `the quote names no list of photographs taken out` |
| `POST /api/c/<c>/draft` | `{"flow": "nope"}` | `not a flow this surface drafts` |
| the same | `{"flow": <offered>, "images": []}` | `the draft names no images` |
| `PUT …/draft` | `{"fields": <read>, "renders": "x"}` | `` the update's `renders` is not a count and its seeds `` |
| the same | `{"fields": <read>, "renders": {"seeds": ["x"]}}` | `the update's renders seeds are not decimal numbers` |

Each is read as a status `409`, its text, and the run or the staging folder unchanged. The render confirmation's own — no collections, no `limit_s`, no `images`, no `bakes` — need an approval and a key, so they sit beside `test_a_confirmation_shorter_than_the_quote_now_gives_is_refused` in `tests/test_ui_jobs.py` and use its `_quoting` and `_approved`. An upload past its declared length is bound to `import:refuse:a-file-over-the-limit-is-refused`: the reader's `put` is replaced by a function that fails, so the status `409` shows the body was never handed on.

### D4

`ISEKAI_WIRING=tests.e2e.wiring:fake` names the factory the browser tests serve on, and the child inherits the environment, as `jobs.py` starts it with no `env`. `fake` holds the reader on `.prepare-release` beside a collection named `hub-prepare`. The test makes that collection, posts Prepare, and waits for the cell to reach `tagged`, so the child is held.

Stop is posted, the slot is read from the stream's first frame until it reads `stopped`, and the cell still reads `tagged`. The reader is held, so the test proves the routes and the interrupt; that no later stage starts is held by the existing unit test of Stop.

```
 POST …/prepare ─▶ child: tag ─▶ caption (held on .prepare-release)
 POST …/prepare ─▶ 409 a job is running: Prepare on hub-prepare
 POST /api/jobs/prepare/stop ─▶ child interrupted ─▶ slot "stopped", cell not "sheet"
```

Stop with no job running is refused `no Prepare is running, so there is nothing to stop`; Stop of `nope` is refused `there is no nope job`. Both tests carry the key of Stop, `ui:prepare:stop-interrupts-the-job`, as refusals of it. `unprepared` is tested on a hub with a cell in each of the stages `assigned`, `tagged`, `sheet` and `unreadable`.

### D5

`Billing(volume, log, broadcast, running, now=…)` over the file's `_volume` double, its `status --json` asks recorded. The `running` callable the test passes counts its own calls and answers from a mutable flag. `watch(interval=0.01)` runs: it asks once on start; the flag set, it asks again; the flag cleared and a `pod` record written, it asks again; the record deleted, the counter shows the loop woke while nothing more was asked; `close()` ends the thread. Each wait is on the recorded asks or the counter, with a deadline, never on a sleep.

### D6

The fixture `ui/src/test/wire.json` is one object, `bodies`, each entry:

```json
{"builder": "bakeTattoo", "method": "POST",
 "path": "/api/c/{collection}/tattoos/{name}/bake",
 "keys": ["digest", "flow", "version", "seed", "edit", "pairs", "limb", "exclusions"],
 "server": "BAKE_KEYS", "optional": ["edit"]}
```

The entries, each builder of `ui/src/api.ts` with the tuple that checks its body:

| builder | method · path | `keys` as the builder sends them | `server` | `optional` |
|---|---|---|---|---|
| `saveStageOne` | `PUT` `/api/tattoos/{name}/stage1/{digest}` | `pairs`, `not_on_photo` | `STAGE1_KEYS` | none |
| `saveOutline` | `PUT` `/api/tattoos/{name}/outline` | `points`, `closed`, `white`, `neutral`, `depth` | `OUTLINE_KEYS` | none |
| `inkView` | `POST` `/api/c/{collection}/tattoos/{name}/ink` | `points`, `white`, `neutral`, `depth`, `digest`, `flow` | `INK_KEYS` | none |
| `placementPreview` | `POST` `/api/c/{collection}/tattoos/{name}/preview` | `target`, `digest`, `flow`, `version`, `seed`, `edit`, `pairs`, `limb`, `exclusions` | `PREVIEW_KEYS` | `edit` |
| `proposePairs` | `POST` `/api/c/{collection}/place/propose` | `digest`, `flow`, `version`, `seed`, `points` | `PROPOSE_KEYS` | none |
| `bakeTattoo` | `POST` `/api/c/{collection}/tattoos/{name}/bake` | `digest`, `flow`, `version`, `seed`, `edit`, `pairs`, `limb`, `exclusions` | `BAKE_KEYS` | `edit` |

`keys` is what the builder sends. `server` names the tuple `isekai/interface/ui/app.py` holds. `optional` is each key the server reads with `.get`, so the tuple has none of them. The vitest `ui/src/api.test.ts` calls each builder against a stubbed `fetch` and asserts the method, the path and the body's keys. `tests/test_ui_wire.py` asserts that `keys` less `optional` is the tuple, that every `*_KEYS` tuple of the server is named by an entry, and that the server has a route of each method and path.

The tattoo routes the page keeps and cuts, `POST /api/tattoos` and `POST /api/c/<c>/tattoos`, hold no tuple: the server reads their keys by `.get`. They are not in the fixture.

### D7

| requirement | scenario added | key |
|---|---|---|
| `ui` · *A damaged run file or a malformed draft update is refused, never failed* | a body of the wrong shape is refused naming what it lacks | `ui:damage:a-body-of-the-wrong-shape-is-refused-naming-what-it-lacks` |
| `ui` · *Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer* | a job of a kind is accepted once the one before it has ended | `ui:prepare:a-job-follows-an-ended-one` |
| the same | Prepare takes the cells with no sheet and no other | `ui:prepare:prepare-takes-the-cells-with-no-sheet` |
| `ui` · *The page is told of a job as it runs* | a stream sends only its collection's cells | `ui:events:a-stream-sends-only-its-collections-cells` |
| `ui` · *The render job opens the volume, renders, and closes the volume unless kept* | a failed close raises the volume alert | `ui:render-job:a-failed-close-raises-the-volume-alert` |
| the same | the verb's lines are the session's steps and images | `ui:render-job:the-verbs-lines-are-the-sessions-steps` |
| `ui` · *Billing state is read from gpunit's own records* | gpunit is asked while a session runs or an alert is open | `ui:billing:gpunit-is-asked-while-a-session-or-an-alert-is-open` |

Each requirement's text is the living one, unchanged. The test of a key may carry it before the release folds the delta. The tests with no scenario of their own carry an existing key:

| test | key it carries | because |
|---|---|---|
| the upload past its declared length | `import:refuse:a-file-over-the-limit-is-refused` | the route refuses it before the body is read |
| Stop idle and of an unknown kind | `ui:prepare:stop-interrupts-the-job` | refusals of Stop |
| the heartbeat | `ui:events:stopping-ends-open-streams-quietly` | a quiet stream ends when the surface stops |
| the wire fixture's tests | `structural:` exemptions | no requirement fits: [Tests](#tests) names them |

### D8

The change's mutants are in [mutants.json](mutants.json), each `tests` a list of files. Phase 6 appends them to `tests/mutants.json` and replays the file.

The audit's mutants in `ui/src/api.ts`, `VT-18`, name a vitest runner, and the replay runs Python's tests: `ui/src/api.test.ts` holds them by the cases [Tests](#tests) names. No audit mutant exists for the poll, the Prepare route or the bodies.

## Tests

Every case is a unit test: no browser, no end-to-end test is added, and none runs on an engine. The tests each file holds at the cut, by `git grep -c -E '^def test_' -- <file>`, and what it gains:

| file | tests at the cut | gains | phase |
|---|---|---|---|
| `tests/test_ui_jobs.py` | 33 | the alert on a failed close, a job after an ended one, the verb's lines, the render confirmation's refusals, Prepare and Stop over HTTP, `unprepared` | 1, 2, 3 |
| `tests/test_ui_api.py` | 97 | the refusals of a malformed body, an upload past its length; the guard's and the loopback's tests extended in place | 2 |
| `tests/test_ui.py` | 16 | the stream's filter and heartbeat | 4 |
| `tests/test_ui_billing.py` | 3 | the poll | 4 |
| `tests/test_ui_wire.py` | new | the fixture against the server and its twin | 5 |
| `ui/src/api.test.ts` | new | each builder's body, and a refusal unwrapped as the cases below say | 5 |

The cases that start a real child interpreter are Prepare over HTTP and the render whose script prints lines. A new test that runs over five seconds carries the `slow` marker, which `make check` skips; the build measures it.

`tests/mutants.json` is not a test and is not in the gate; `make mutants` replays it. The mutants, where each lies at the cut and the test file that must kill it:

| mutant | where at the cut | killed by |
|---|---|---|
| `UA-1a` | `isekai/interface/ui/app.py:348` | `tests/test_ui_api.py` |
| `UA-1b` | `isekai/interface/ui/app.py:352` | `tests/test_ui_api.py` |
| `UA-2` | `isekai/interface/ui/app.py:321` | `tests/test_ui_api.py` |
| `UA-9` | `isekai/interface/ui/events.py:102` | `tests/test_ui.py` |
| `UB-1` | `isekai/interface/ui/jobs.py:577` | `tests/test_ui_jobs.py` |
| `UB-4` | `isekai/interface/ui/jobs.py:413` | `tests/test_ui_jobs.py` |

The vitest cases that hold the mutants of `ui/src/api.ts`, `VT-18`:

| mutant's line | case |
|---|---|
| `.json().catch(() => ({}))` in `request` | a `502` with an HTML body rejects `<url> answered 502` |
| `if (answers?.(body)) return body as T` | `draft` answered `409` with `images` resolves to the body |
| the `NaN` check of `readBox` | an ink answer without `X-Ink-Box` rejects `answered no ink box or white point` |

No test is deleted or merged, so no row maps one test to another.

## Dependencies

None.

## Risks / Trade-offs

- **A real child is slow.** Prepare over HTTP starts the real verb. It waits on a file, not on the clock, but it costs the import of the program; the build marks it `slow` if it passes five seconds.
- **The held reader gives up at thirty seconds.** `tests/e2e/wiring.py` raises when no one releases it; a stopped child never reaches that.
- **Phase 6 builds on `0135-the-paydown` and `0136-the-cli-and-the-session`.** The replay mode and the file must be merged: its first task is a **HALT CHECK** for them.
- **A `find` that moves makes the replay refuse.** Phases 1 to 5 edit no product file, so each line stands as [Tests](#tests) says.
- **The scenario for a body of the wrong shape names routes by example.** It sits under the requirement whose title says *refused, never failed*; the reviewer may move it.

## Verdict

Ready to build. Each phase ends on a green `make gate`, and phase 6 on a replay with no survivor. Nothing is irreversible: no product file, format version, requirement text or decision moves.
