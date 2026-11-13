# The CLI and the session — design

The front ends' first half is held by tests that read the wrong evidence, and some of its refusals are wrong as printed. This change reads them right, fixes those, and pins what it fixed with mutants. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The audit ran each test against mutants of the product. The ones below survived. The facts were read at the cut, at `d6e88dc3`; `0135-the-paydown`, the version this one builds after, adds the replay mode `--edits`, `tests/mutants.json` and `make mutants`, which phase 5 uses.

| gap | where it lives at the cut |
|---|---|
| a verb with no `--flow` is refused by argparse, which lists no flow | `isekai/interface/cli.py` `build_parser`, `tests/test_pipeline_cli.py` |
| *no verb is refused* reads an exit code; no test reaches the range checks | `tests/test_pipeline_cli.py`, `isekai/interface/cli.py` `_seed`, `_positive` |
| the empty runs root's remedy names `tag --flow`, which the build refuses | `isekai/interface/render.py` `_asked`, `isekai/interface/cli.py` `dispatch` |
| the remedy sweep accepts bare verbs and reaches no refusal of the session or of `dispatch` | `tests/test_resume.py` `AVAILABLE`, `_every_refusal` |
| a failing free check with no request, the limit's floor, a given limit, a lone source request and `render` through the parser run in no test | `isekai/interface/render.py` `_session`, `_limit`, `_asked`, `tests/test_render.py` |
| the busy-port probe runs in no test; its session test is exempt as fitting no scenario | `isekai/boundary/gpu.py` `answers`, `tests/test_spec_bindings.py` `BEHAVIOUR_EXEMPT` |
| tests rebuild the CLI's batch by hand | `tests/test_generate.py`, `isekai/interface/cli.py` `assemble_one` |
| a failed sampling is tested with one edit; a chain of pending edits and a replaced draft's content are unread | `tests/test_edit.py`, `tests/test_review.py`, `isekai/interface/cli.py` `_pending` |

```
 cli.py parser ──▶ render.py remedy ──▶ the sweep          (phases 1, 2)
 render.py session · gpu.py probe                          (phase 3)
 cli.py batch · cli.py pending edits · review.py           (phase 4)
 tests/mutants.json ◀── mutants.json                       (phase 5)
```

## Goals / Non-Goals

**Goals**
- A refusal of the CLI is read by its message, in process, never by an exit code alone.
- A refusal prints a remedy this build performs: the product fixes, and a sweep that would have caught the second.
- Nothing is rented before every free check has passed, on every path that rents.
- Each finding's mutant dies, and stays dead: `tests/mutants.json` holds it.

**Non-Goals**
- The server's half: the jobs, the routes, the wire. They are the next version.
- A requirement, a format version, a flag, a verb, or a decision in force. `docs/decisions.md` is not edited.
- The differences between the front ends. The refactor's *acts* fixes them with their tests.
- Merging the tests of the remedy sweep into one. Their names and keys stay.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | No verb, a count, a seed and a limit out of range are read in process, by the message | an exit code passes a traceback; a subprocess costs seconds a test | the exit code alone |
| [D2](#d2) | A stage verb with no `--flow` is refused listing the tracked flows, exit 2 as now | its requirement already says so, and a patch may not reword a scenario | dropping `required` and refusing in `_flows_for`; rewording the scenario |
| [D3](#d3) | The empty runs root's remedy names `assign --flow` | the build refuses `tag --flow`, and a refusal may name no action the build cannot perform | leaving it to the refactor |
| [D4](#d4) | The sweep drops its bare verbs, prints the unquoted command it finds, and refuses a photograph verb naming a flow | a sweep that accepts `delete` proves nothing; `tag --flow` parsed as printed | merging the sweep's tests |
| [D5](#d5) | The session's free checks are tested on every path that rents | the failing free check with no request runs in no test | one test over the quote alone |
| [D6](#d6) | The busy-port probe runs on a real socket, and gets a scenario under the tunnel requirement | the probe runs in no test; its session test fits no scenario | an exemption that stays |
| [D7](#d7) | One CLI batch test replaces the tests that rebuild the batch, and carries their keys | a test of a copy proves the copy | keeping them beside it |
| [D8](#d8) | The pending edits are tested as the verb runs them: a failure beside a good edit, a chain | each arranges one edit today | a patched client |
| [D9](#d9) | Scenarios are added under the requirements that demand them | a patch adds a scenario under a requirement, never a requirement | `skip_specs`; a MODIFIED SHALL |
| [D10](#d10) | Phase 5 adds the change's mutants to `tests/mutants.json` | a mutant that must stay dead is a file | the change directory alone |

### D1

The tests call `build_parser().parse_args(...)` under `pytest.raises(SystemExit)`, assert code `2` and read the message from `capsys`. The messages are the parser's own: `the following arguments are required: verb`, `a render count below 1 renders nothing`, `a session limit below 1s ends at once`, `is not an integer` and `is outside the sampler's unsigned 64-bit range`. No product edit.

### D2

A new class `_Verb` of `isekai/interface/cli.py` subclasses `argparse.ArgumentParser`. Its `error` appends `; the flows this build tracks are <names>` when the message names `--flow`, and exits as the parent does. `build_parser` passes `parser_class=_Verb` to `add_subparsers`. The exit code, `required=True` and every action stay as they are, so `tests/record/verbs.json` does not move.

```
review ada.jpg
  before: error: the following arguments are required: --flow
  after:  error: the following arguments are required: --flow; the flows this build tracks are <each flow>
```

### D3

`_asked` in `isekai/interface/render.py` prints `uv run python -m isekai assign <--flow F …> --runs <runs> <photos>/*` where it printed `tag`. `assign` opens the run with its flow ([cli: *Assigning a flow writes its run*](../../specs/cli/spec.md)); `tag` refuses `--flow` in `dispatch`.

### D4

The sweep's `AVAILABLE` loses `"delete"` and `"rename"`: any message holding the word passed. A message the sweep then names gets the phrase of that message from the word to the next `;`, `,` or `.`, as printed. `_printed` also finds the command a refusal prints without backticks, after `uv run python -m isekai `, to the end of the message. `_names_its_run` returns false for a printed photograph verb that names a flow. `_every_refusal` gains the refusal `dispatch` prints for `tag --flow` and the session's for an empty runs root: both are printed to `err`, not raised.

### D5

Each test goes to the lowest layer that fails: the session's own `run_session` through the file's `session` helper, `Calls` as `generate`, `FakeOpen` as the pod. No patch is added.

| finding | case | binds |
|---|---|---|
| `CL-1` | no request, the free `generate` answers 1: status 1, nothing opened, no `sessions/` folder | `pod-image:session:every-exit-tears-down` |
| `CL-3` | a limit one second below the floor is refused naming it; a limit within the bounds is the session's | the new scenarios of [D9](#d9) |
| `CL-4` | a source request over a run whose source holds renders: the free line carries `--seeds-from` and the record plans them; its free check failing opens nothing; an empty runs root is refused naming `assign` | `cli:render-session:the-record-plans-each-photograph`, `image-generation:seeds-from:no-source-render-is-refused-first`, `cli:refusals:refusal-names-the-remedy` |
| `CL-12` | `render` through the parser and `dispatch` over a short run with a fake session writes its record; a request with no collection is refused at parse time | `cli:render-session:a-session-writes-its-record`, `cli:render-session:a-refusal-before-renting-writes-none` |
| `RE-1` | more recorded edits than the window: the oldest, an outlier, is not taken | `edit:edit-limit:a-median-above-the-figure-is-used` |

### D6

`answers(port)` is true while a socket listens on `port` on loopback and false once it is closed. The test binds port `0`, so no fixed port is held. Its session twin, `test_a_port_that_already_answers_is_refused_before_the_session`, carries the scenario's key in place of its exemption, and its row leaves `BEHAVIOUR_EXEMPT`; `BEHAVIOUR_CEILING` falls by one, as the table may only shrink.

### D7

`test_one_batch_survives_a_bad_sheet_an_unreadable_header_and_a_photograph_past_the_bound` runs `dispatch` over `generate --flow` and these targets: an identifier naming no run, a good run, one with a damaged approved sheet, one whose photograph is a truncated header and one whose photograph is past the aspect bound. It asserts the exit, a refusal in `err` for each bad target, and the good run's prompt written.

The first target is the one on which `assemble_one` raises, the only case in which the mutant `PA-4` differs from `across`: the other bad targets reach `broken` through `prepare`. The tests it replaces are named in [Tests](#tests). `docs/principles.md` names one of them as a proof of a principle, so it names the new test.

### D8

A test-local client, a subclass of `RecordingComfyClient`, rejects the first graph it is sent and answers the rest, so no patch is needed. The chain test follows `test_edit_request_an_edits_image_chains_to_the_next_number`: a stand-in for the first edit's image, a request from it, then the stand-in is removed.

```
 42.edit-1  pending   source 42.png          sampled first
 42.edit-2  pending   source 42.edit-1.png   checked before the pod without its source,
                                              checked against the new image once written
```

The new image is the pod's, so it is not the stand-in's bytes: the second edit is refused at its sampling, `its source 42.edit-1.png has changed since the request`, and the first stays sampled. With `waiting` empty the check before the pod would refuse the second for a source that cannot be read, and nothing would be sampled: the test is red for that.

### D9

| requirement | scenario added | key |
|---|---|---|
| `cli` · *The rendering verb takes many photographs and either a count or explicit seeds* | a count or a seed out of range is refused at parse time | `cli:generate-signature:a-count-or-seed-out-of-range-is-refused` |
| `cli` · *A render session's limit is estimated from its work, at most the configured ceiling* | a limit below the floor is refused | `cli:render-limit:below-the-floor-is-refused` |
| the same | a limit below one second is refused at parse time | `cli:render-limit:below-one-second-is-refused-at-parse-time` |
| the same | a given limit is the session's limit | `cli:render-limit:a-given-limit-is-the-sessions` |
| `edit` · *A render session runs every pending edit* | a failed sampling costs the next edit nothing | `edit:session:a-failed-sampling-costs-the-next-edit-nothing` |
| the same | a chain of pending edits runs in order | `edit:session:a-chain-of-pending-edits-runs-in-order` |
| `pod-image` · *A render session reaches its tunnel without a proxy* | a port that already answers is refused before the session | `pod-image:session:a-busy-port-is-refused-before-the-session` |

Each requirement's text is the living one, unchanged. A scenario's test may carry the key before the release folds the delta: an active delta's keys are nameable.

### D10

The change's mutants are in [mutants.json](mutants.json), each `tests` a list of files. Phase 5 appends them to `tests/mutants.json` and replays the file. `CL-7` names the line of [D2](#d2) as phase 1 leaves it. No audit mutant exists for the parser's listing of flows: the test of phase 1 asserts each tracked flow, so it is red with the listing removed.

## Tests

Every case is a unit test: no browser, no end-to-end test is added, and none runs on an engine. The one socket is loopback, bound to port `0`. The tests each file holds at the cut, by `git grep -c -E '^def test_' -- <file>`, and what it gains:

| file | tests at the cut | gains | phase |
|---|---|---|---|
| `tests/test_pipeline_cli.py` | 50 | the range checks of a count and a seed, of a limit | 1 |
| `tests/test_resume.py` | 23 | none: the sweep and its twin are widened in place | 2 |
| `tests/test_render.py` | 59 | the empty runs root, a failing free check, the floor, a given limit, a lone source request's plan and its failing check, `render` through the parser and its refusal at parse time, the recorded edit durations | 2, 3 |
| `tests/test_gpu.py` | 2 | the busy-port probe | 3 |
| `tests/test_generate.py` | 88 | the CLI batch; loses three | 4 |
| `tests/test_edit.py` | 76 | a failed sampling beside a good one, a chain of pending edits | 4 |
| `tests/test_review.py` | 96 | none: a read of the draft's content is added to one | 4 |
| `tests/test_spec_bindings.py` | 53 | none: a row and one of the ceiling go | 3 |

`tests/mutants.json` is not a test and is not in the gate; `make mutants` replays it. The mutants, where each lies at the cut and the test file that must kill it:

| mutant | where at the cut | killed by |
|---|---|---|
| `CL-1` | `isekai/interface/render.py:1064` | `tests/test_render.py` |
| `CL-3a` | `isekai/interface/render.py:801` | `tests/test_render.py` |
| `CL-3b` | `isekai/interface/render.py:1084` | `tests/test_render.py` |
| `CL-4a` | `isekai/interface/render.py:1137` | `tests/test_render.py` |
| `CL-4b` | `isekai/interface/render.py:1148` | `tests/test_render.py` |
| `CL-5` | `isekai/boundary/gpu.py:97` | `tests/test_gpu.py` |
| `CL-7` | `isekai/interface/cli.py:261` | `tests/test_pipeline_cli.py` |
| `CL-10` | `isekai/interface/cli.py:188` | `tests/test_pipeline_cli.py` |
| `PA-4` | `isekai/interface/cli.py:1477` | `tests/test_generate.py` |
| `PB-5` | `isekai/pipeline/review.py:272` | `tests/test_review.py` |
| `PB-6` | `isekai/interface/cli.py:971` | `tests/test_edit.py` |
| `PB-16` | `isekai/interface/cli.py:943` | `tests/test_edit.py` |
| `RE-1` | `isekai/interface/render.py:679` | `tests/test_render.py` |

The tests deleted, each mapped to the test that carries its assertions and its scenario key:

| deleted test | carried by | key it carries |
|---|---|---|
| `tests/test_generate.py::test_one_bad_sheet_does_not_stop_the_other_photographs` | `tests/test_generate.py::test_one_batch_survives_a_bad_sheet_an_unreadable_header_and_a_photograph_past_the_bound` | `image-generation:assembly:bad-sheet-fails-before-the-session` |
| `tests/test_generate.py::test_one_unreadable_header_does_not_cost_the_batch_its_turn` | the same | `run-directory:budget:one-failure-does-not-halt-the-batch` |
| `tests/test_generate.py::test_one_photograph_past_the_bound_does_not_cost_the_batch_its_session` | the same | `image-generation:working-resolution:a-refusal-is-per-photograph` |

## Dependencies

None.

## Risks / Trade-offs

- **The sweep may name a message after its bare verbs go.** [D4](#d4) says what each gets, so the sweep is never loosened to pass.
- **The batch test may find a refusal that names no run.** The test then asserts the message's own words, as those it replaces did.
- **Phase 5 builds on `0135-the-paydown`.** Its replay mode and file must be merged: phase 5's first task is a **HALT CHECK** for them.
- **A `find` that moves makes the replay refuse.** Phases 1 to 4 edit `isekai/interface/cli.py` and `isekai/interface/render.py` away from the lines the mutants name; each phase leaves them as [D10](#d10) says.
- **The sweep's twin is widened, not replaced.** A guard that cannot fail is the failure the sweep exists to avoid.

## Verdict

Ready to build. Each phase ends on a green `make gate`, and phase 5 on a replay with no survivor. Nothing is irreversible: no format version, requirement or decision moves, and the product edits change a refusal's words and the parser's message alone.
