# Design — 0030 the defects

How each defect is fixed, and the existing requirement that demands it. **Verdict: `feasible`.** Every file,
symbol and line below was re-checked at `main` `e6c4278`.

## Context

- **What survives from each family**, re-checked at `e6c4278` by reproduction or by tracing the code:

  | family | the defect today | where |
  |---|---|---|
  | tracebacks | a truncated file, a JSON list, a `schema` that is not an object: `read` raises `ValueError` or `AttributeError` | `isekai/foundation/artifacts.py:316-317` |
  | | a draft missing `fields` | `isekai/pipeline/review.py:309-311` |
  | | an approved sheet missing `sheet` | `review.py:147` |
  | | the approved producer read outside the assemble guard; a list `fields` raises `AttributeError` | `isekai/pipeline/generate.py:207`, `:185`; `isekai/foundation/flow.py:531` |
  | | a malformed answer from ComfyUI: `IncompleteRead`, a body that is not JSON, a missing key | `isekai/boundary/comfy/client.py:47-79`, `generate.py:485` |
  | | a WD14 tag that is not a string | `isekai/pipeline/sheet.py:116` |
  | | a corrupt frame, read with a bare `json.loads` | `isekai/foundation/run.py:233-236` |
  | remedies | printed stage commands name no run, so they parse, do nothing and exit 0 | `review.py:139`, `:207`, `:302`, `:343`; `generate.py:139-140`, `:237-238`; `sheet.py:109`; `run.py:555`; `isekai/interface/ui/app.py:317` |
  | | `refusal_for` says "run again" after a permanent record, or one that fills the budget | `run.py:523-557` |
  | | a budget refusal names only the directory: `in 001/`, `in wd14/` | `run.py:484`, `:492` |
  | | the render says "render again" after recording a record that refuses it | `generate.py:488-491`, `:443-454` |
  | | the assembly refusal forwards an inner remedy and names no action of its own | `generate.py:185-195` |
  | | *"the id `python -m isekai show` prints"* — `show` with no id prints nothing | `isekai/interface/cli.py:264-269`; `isekai/interface/ui/batch.py:175-179`, `:190-195` |
  | | the read's *"re-run the stage that wrote it"* — a rerun is a no-op while the file exists | `artifacts.py:320-323` |
  | records | the attempt number is a count, so a deletion makes the next record overwrite one | `run.py:459` |
  | | every HTTP status is `Unreachable`, recorded transient and told to bring a pod up | `client.py:94`; `generate.py:451` |
  | | a failed upload records nothing | `generate.py:431` |
  | | `record_failure` spreads its detail after its own keys | `run.py:461-467` |
  | approval | the definitions of a draft disagree: `review.draft_versions` (`review.py:80-85`), `Batch.draft_path` (`batch.py:114-123`), `review.state` (`review.py:88-110`). A listing `001.draft.json 002.approved.json` serves 001's fields read-only (`app.py:247-257`) and lets `approve` and its POST (`app.py:336`) approve 001 | |
  | | overlapping draft updates both pass the precondition and both write | `app.py:295-333`, `:438-463` |
  | reading | `Run.frame` and `show` parse a file whatever version it declares | `run.py:233-236`; `isekai/interface/run_view.py:62-82` |
  | provenance | the image is written before its sidecar | `generate.py:459`, `:475` |
  | dead code | `prompt_artifact`'s `new_version` rewrites a prompt in place; no caller passes it | `generate.py:163`, `:174` |

- **Tests that pin today's text**, which the fixes keep or reword: `tests/test_run_directory.py:452-453`,
  `:467-468` (the version refusal), `tests/test_resume.py:355-362` (`AVAILABLE`), `:411-437` (the printed
  command parses once `an-identifier` is appended), `tests/test_generate.py:646`, `:710` (the forwarded remedy),
  `tests/test_tagging.py:225-226`, `:510`, `:514`, `tests/test_caption.py:245`, `:263-264` (`refusal_for`),
  `tests/test_review.py:231`, `tests/test_ui.py:123` (command substrings).
- **Line numbers are `e6c4278`'s.** A builder re-resolves each by the text it names.

## Goals / Non-Goals

**Goals**

- No input's failure ends the batch with a traceback.
- Every command a refusal prints works in the state that refusal leaves.
- Every failure is recorded, as the kind it was.
- An approved input stays approved until a new version is asked for.

**Non-Goals**

- Any product change: a sheet's fields, the prompt, the image.
- A defect no requirement covers ([proposal](proposal.md#not-in-this-change)).
- A catch-all for exceptions.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | each traceback becomes a refusal where it happens | a traceback is a defect; a catch-all hides the next one | catching `Exception` in `across` |
| [D2](#d2) | every printed command carries its run id and works in the state its refusal leaves | the remedy requirement: *SHALL NOT name an action this build cannot perform* | editing only the phrasing |
| [D3](#d3) | the attempt number is the highest present plus one; HTTP statuses carry their kind | the budget requirement; *recorded as the kind it was* | a count; one class for every transport failure |
| [D4](#d4) | one definition of a draft, in `pipeline/review.py`; a lock around a draft update | the definitions disagree, and every approval defect comes from it | a point fix per defect |
| [D5](#d5) | stage reads refuse an unknown version; `show` marks it | *a reader handed an unknown version refuses*; inspection reads a run in any state | `show` refusing the whole run |
| [D6](#d6) | the sidecar is written before its image | an image then always has its provenance | a check at resume |
| [D7](#d7) | the docs drop the known breaks that close | a closed break still listed is a false claim | leaving them |
| [D8](#d8) | a scenario per fix, under its requirement | each fix gets a test bound to its own scenario | borrowed bindings |
| [D9](#d9) | a patch | every fix is demanded by an existing requirement | a minor |

### D1

**Each traceback becomes a named refusal where it happens.** Demanded by
`run-directory:budget:one-failure-does-not-halt-the-batch`, the SHALL of *An unknown schema version is refused*,
`review:validation:missing-field-refuses-approval`, `image-generation:assembly:a-bad-sheet-is-per-flow` and
`ui:startup:refusals-are-reported-together`.

| site | becomes |
|---|---|
| `read` (`artifacts.py:309-325`) | a file that is not valid JSON, not a JSON object, or whose `schema` is not an object is refused naming the file, with a remedy this build can perform: delete it, then run the stage that wrote it again |
| `approve` (`review.py:309-311`) | a draft whose `fields` is absent or not an object is read as holding no fields, so validation refuses it naming the missing fields |
| `review` (`review.py:147`) | an approved sheet without `sheet` is refused naming the file |
| `prompt_artifact` (`generate.py:178-207`) | the producer is read inside the guard, and the guard also catches `AttributeError` |
| the client (`client.py:84-100`) | [D3](#d3)'s statuses; `http.client.HTTPException` → a transient `TransportFailure`; `ValueError`, `KeyError` → a permanent one, *"the endpoint answered in a shape this build does not read"* |
| `_submit` (`generate.py:480-491`) | a history record without `outputs` or with no image is refused, permanent |
| `sheet` (`sheet.py:116`) | `DanbooruTag(str(one["tag"]))` — a non-string tag routes nowhere, as before v0.22.6 (`v0.22.6 review/R1`, `security/S1`) |
| `Run.frame` (`run.py:233-236`) | read through `read(self.frame_path, RUN_FILE)` ([D5](#d5)) |

### D2

**Every printed command works in the state its refusal leaves.** Demanded by `cli:refusals:refusal-names-the-remedy`
(*SHALL NOT name an action this build cannot perform*), `run-directory:budget:at-budget-the-stage-refuses` (*names
the photograph and the error record*) and `image-generation:assembly:a-bad-sheet-is-per-flow` (*naming the flow*).

- **A printed stage command carries the run id**, after its flags: every site in [Context](#context)'s remedies row.
- **`refusal_for`** (`run.py:523-557`): when the record is permanent, or fills the stage's budget, the message names
  `<flow>/<area>/<record>`, says to fix what it names and delete it, then the command with the run id. Below the
  budget it keeps *"run … again"*, with the run id.
- **`check_budget(stage, directory, version, run)`** takes the `Run`, and names the record by its path relative to
  the run — `summon-anime-wai/wd14/001.error.1.permanent.json`. Callers: `isekai/pipeline/caption.py`,
  `tagging.py`, `sheet.py`, `generate.py`; `tests/test_run_directory.py:575`, `:591`, `:607`, `:630`.
- **The render** (`generate.py:443-454`): after recording, the refusal names the run, the flow, the record by its
  path and *delete it before rendering again*; `_submit`'s own text (`:488-491`) loses *"render again"*.
- **The assembly** (`generate.py:185-195`): its refusal keeps the forwarded cause and ends with its own action —
  fix it, delete `<flow>/prompts/<record>`, run `python -m isekai generate --flow <flow> <run-id>`.
- **The `show` circle** (`cli.py:264-269`, `ui/batch.py:175-179`, `:190-195`) becomes *"the name of a run
  directory under `<runs root>`"*.
- **The read's remedy** is [D1](#d1)'s.
- **The guard:** `tests/test_resume.py`'s `test_every_command_a_refusal_prints_is_one_this_build_accepts` parses each
  printed command as printed — no appended identifier — and asserts a stage verb names at least one run.

### D3

**Records are right.** Demanded by the budget SHALL (`run-directory` `:246-248`),
`image-generation:failure:an-unreachable-endpoint-is-transient` and the remedy requirement.

- **The attempt number** (`run.py:459`) is the highest recorded plus one.
- **`record_failure`** writes `stage`, then `seed` when given, then `detail`, after its own keys — never a spread.
  Today's bytes are unchanged (`tests/golden/error.json`).
- **The transport's refusal carries its kind**, as `isekai/boundary/comfy/contract.py:11`'s docstring prescribes
  (*"that is the point to add the field rather than a second subclass"*): `Unreachable` becomes
  `TransportFailure(Refusal)` with a `kind`. `_reported` (`client.py:84-100`) classifies:

  | the endpoint | kind | the message names |
  |---|---|---|
  | answers 4xx | permanent | the status and ComfyUI's error body |
  | answers 5xx | transient | the status; *check the pod's ComfyUI log* |
  | cannot be reached (`URLError`, `OSError`) | transient | today's text |

  `render` records `failed.kind` for a `TransportFailure`, and `permanent` for any other refusal (`generate.py:451`).
  The front door exports `TransportFailure` in `Unreachable`'s place.
- **A failed upload is recorded** (`generate.py:431`): the upload runs inside the guard, with the same
  classification; its record carries no `seed`.

### D4

**One definition of a draft**, in `isekai/pipeline/review.py`: `current_draft(directory)` returns the highest
`NNN.draft.json` numbered above the highest approval, or `None`. Demanded by the SHALL of *An approved input is
read-only on the surface until it is re-opened* (`ui` `:128-130`), `run-directory:idempotence:rerun-is-a-no-op` and
`review:approval:approved-is-not-overwritten`.

- It replaces `draft_versions` in `save_draft` and `approve`; `Batch.draft_path` (`batch.py:114-123`) returns it.
- `read_input` (`app.py:239-290`) serves the approved artifact when the state is approved and the current draft
  otherwise; `draft` and `saved` come from the current draft.
- `approve` on an approved flow finds no current draft and returns as complete — for the CLI and the POST alike.
- A same-numbered draft left by a crash between approving and unlinking is not above the approval, so it no
  longer counts.
- **The lock:** one module-level `threading.Lock` in `app.py`, held across `_precondition` and `save_draft` in
  `put_draft`. The later of overlapping updates then fails the precondition and answers 409. Demanded by the
  SHALL of *A draft update states the version of the draft it replaces*.

### D5

**Stage reads refuse an unknown version; `show` marks it.** Demanded by
`run-directory:provenance:artifact-declares-its-schema` (*a reader handed an unknown version refuses rather than
parsing it*).

- `Run.frame` reads through `read(…, RUN_FILE)`.
- `run_view._producer_of` (`run_view.py:62-82`) compares a file's declared version with the version of the kind it
  names, from a mapping `isekai/foundation/artifacts.py` builds from its descriptors. A mismatch, an unknown kind
  and a body that is not an object are shown as *"declares version N; this build reads M"*, *"declares kind X,
  which this build does not read"* and *"unreadable"* — none parsed. A malformed `producer` or `from` is shown as
  unreadable, not raised.

### D6

**The sidecar is written before its image** (`generate.py:459`, `:475` swap). An image then always has its
provenance: a crash between the writes leaves a sidecar with no image, and the seed renders again. Demanded by
`image-generation:immutability:output-records-the-graph-digest`. `prompt_artifact`'s `new_version` parameter and its
branch (`generate.py:163`, `:174`) are deleted: no verb reaches them, and they overwrote a prompt in place.

### D7

**The docs drop the known breaks that close**: `docs/principles.md:28-29`, `:127-131`, `:227`. Paid on the way,
because this change edits their files:

- `v0.22.5 review/R1` — *Only a front end composes* gains a known-breaks line: `interface/wiring.py`'s
  `load_vocabulary` turns a missing vocabulary into a refusal.
- `v0.22.7 review/R1` — `isekai/boundary/README.md:34`'s importer list for `provision.py` is completed, in the
  README this change edits for `TransportFailure`.

### D8

**A scenario per fix**, each under the requirement whose SHALL states it ([specs/](specs/)):

| scenario | test |
|---|---|
| `ui:approval:a-stale-lower-draft-does-not-reopen` | `tests/test_ui_api.py::test_a_stale_lower_draft_does_not_reopen_an_approved_input` |
| `ui:draft-update:overlapping-updates-cannot-both-commit` | `tests/test_ui_api.py::test_overlapping_draft_updates_cannot_both_commit` |
| `run-directory:idempotence:approving-an-approved-flow-writes-nothing` | `tests/test_review.py::test_approving_an_approved_flow_writes_nothing` |
| `run-directory:schema:an-unreadable-artifact-is-refused-by-name` | `tests/test_run_directory.py::test_an_unreadable_artifact_is_refused_by_name` |
| `image-generation:failure:a-rejected-graph-is-permanent` | `tests/test_generate.py::test_a_rejected_graph_is_recorded_permanent` |
| `image-generation:failure:a-server-error-is-transient` | `tests/test_generate.py::test_a_server_error_is_recorded_transient` |
| `image-generation:failure:a-failed-upload-is-recorded` | `tests/test_generate.py::test_a_failed_upload_is_recorded` |

The other fixes bind to scenarios that already state them: the batch fixes to
`run-directory:budget:one-failure-does-not-halt-the-batch`, the remedies to `cli:refusals:refusal-names-the-remedy`,
the attempt number to `run-directory:budget:at-budget-the-stage-refuses`, `show` to
`run-directory:provenance:artifact-declares-its-schema`, the sidecar to
`image-generation:immutability:output-records-the-graph-digest`.

**`a-rejected-graph-is-permanent` sits under a SHALL that names only the unreachable case**; the requirement's
title (*recorded as the kind it was*) and rationale (*the kinds separate what will fail again from what might not*)
state it, and the SHALL is not changed.

### D9

**This is a patch.**

| condition | met because |
|---|---|
| no format version moves | no kind's version, and `MANIFEST_VERSION`, changes; an upload's record is an `error` v1 without `seed`, which the shape allows |
| a behaviour fix is required by an existing requirement | each fix names its requirement above; the scenarios are added under existing requirements |
| nothing deprecates a verb or a flag | none; `prompt_artifact`'s parameter was reachable from no verb |
| nothing changes the product | the sheet, the prompt and the image are unchanged for the same inputs |

## Dependencies

None.

## Risks / Trade-offs

- **A reordered render leaves a sidecar without an image after a crash**, and that seed renders again — one paid
  call. → Accepted at the grilling: lost provenance is worse.
- **The lock serialises every draft update in the process.** → One operator, one surface; an update is a
  millisecond write.
- **Renaming `Unreachable` touches the transport's front door.** → Its importers are `generate.py` and a test
  docstring; the name follows the contract's own instruction.
- **Refusal texts change across the stages.** → Each test that asserts a substring keeps it, and the guard test
  holds every printed command to the state it names.

## Verdict

**`feasible`.** Every fix is small, local, and demanded by a requirement the spec already holds; the scenarios give
each its own test.
