# Design — 0047 the refusals

How each refusal names a remedy that works, how a batch keeps going past one flow's refusal, and how the host-key
check reads a log that answers. **Verdict: feasible** — each fix a few lines under an existing requirement, each held
by a test.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`b748c61`; the code is `9995b54`'s, unchanged since):

- **`isekai/interface/cli.py`:** `_require_tagged` (`:350-364`) tells each untagged flow "drop `--flow {name}`", before
  any identifier (`:332-333`). `refused = across(targets, work) + collected` (`:342-344`) is printed together
  (`:345-346`). The work function's `caption` (`:461-479`), `sheet` (`:504-520`), `review` (`:521-523`) and `approve`
  (`:524-529`) loop flows with no catch; `tag` collects per tagger (`:480-503`), with `tagger(flow)` and the hosted
  `_seam` (`:482-485`) outside that `across`.
- **`across`** (`isekai/foundation/run.py:561-574`) runs `work(item)` and collects each `Refusal` as a string.
- **`isekai/pipeline/generate.py:250`:** `ready = [flow for flow in approved_flows(run) if flow in flows]`; the refusal
  (`:251-260`) fires only when no named flow is approved.
- **`isekai/interface/run_view.py`:** `report` (`:181-190`) reads `run.frame` (`:182`) and `frame["photo"]` (`:183`)
  first; `_producer_of` (`:63-105`) marks an unreadable artifact.
- **`isekai/boundary/ollama.py`:** `PROVISION` (`:105`) and `BUILD` (`:108`); the unreadable-record (`:293-297`) and
  no-record (`:343-347`) refusals and the absent-model remedy name the build alone; the mismatch refusal (`:355-360`)
  names `PROVISION` first.
- **`isekai/boundary/provision.py`:** `class UnknownArtifact(Exception)` (`:289`); `entry_for` (`:301-311`) raises it
  naming `eval_models.json`; `resolve` calls it (`:336`). `config/vocabulary.json`'s callers are
  `isekai/interface/wiring.py:244-256` and `isekai/boundary/wd14.py:260-277`.
- **`infra/up.sh`:** `printed_fingerprint` (`:111-117`) reads `logs?since=$since`; `verify_host_key` (`:126-150`) reads
  it for 60 s, then scans and compares.
- **RunPod's v2 log read:** `tail` backfills up to 5000 lines (default 100) and is ignored under `since`;
  `source=container` drops the host's lines; the stream stays open, so `--max-time` ends it.
- **`tests/test_spec_bindings.py`:** `spec_keys` (`:25-31`) reads the effective spec — the living spec as active
  deltas leave it, through `tests/specs.py`'s `effective` — and `test_every_key_has_a_test` demands a test for every
  one. A cut writes a delta before the build writes its tests, so a cut adding a scenario turns the gate red.
- **Tests:** `tests/test_tagging.py:686-707` (the mixed untagged case), `tests/test_caption.py:595-610` (no record),
  `tests/test_eval_manifest.py:131-136` (`pytest.raises(UnknownArtifact)`), `tests/test_infra.py:1889-1923` (the
  host-key stubs, which ignore the URL).

## Goals / Non-Goals

**Goals:** every refusal's remedy runs; every named flow is tried and every refusal reported; no traceback on an
undeclared artifact; a host-key read that answers.

**Non-Goals:** `show` listing failure records; rendering an unnamed approved flow; a message for assembly-only
`generate`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | with only untagged flows named, `tag` says it has nothing to do and names `sheet --flow <flow>`; the mixed case keeps "drop `--flow`" | a remedy argparse refuses is no remedy | naming the run, which does not exist yet |
| [D2](#d2) | each verb's per-flow work runs through `across`, into `collected`, `tag`'s tagger setup included | no named flow is silently dropped | one catch around the whole input |
| [D3](#d3) | every named flow with no approved sheet is refused, beside approved ones or not | the scenario already demands it | dropping it, as today |
| [D4](#d4) | `show` prints the frame's refusal as the photograph line and lists the rest; a missing `photo` key is a refusal too | inspection reads a run in whatever state it is in | refusing the whole report |
| [D5](#d5) | the no-record, unreadable-record and absent-model refusals name `PROVISION`, then the build | the build fails without the files | the build alone |
| [D6](#d6) | the vocabulary's callers turn `UnknownArtifact` into a `Refusal` naming the manifest they loaded | a traceback is a defect; `provision.py` runs by path on the pod, where `isekai` does not import | `UnknownArtifact(Refusal)`, which imports `isekai` into `provision.py`; a new exception |
| [D7](#d7) | the fingerprint is read with `tail=5000&source=container`, the last key line kept | `since` stalled on a live boot; a restarted container prints a new key after the old | `since` with a fallback to `tail` |
| [D8](#d8) | a key is demanded a test once it is in the living spec; a key only an open delta adds may be named, not demanded; each new scenario enters the delta with its test | a cut stays green; the release's gate demands the folded keys | demanding every effective key, which reddens every cut that adds a scenario |

### D1

**`tag`'s untagged remedy.** `_require_tagged` gets the flows it was named. When every one is untagged:
"`tag` has nothing to do: `<flows>` declare `"tagger": false`; run `python -m isekai sheet --flow <flow> <photo>`
next". Otherwise, each untagged flow keeps "drop `--flow <flow>`".

### D2

**Per flow.** In the work function, each verb's loop body becomes a step per flow, and
`collected.extend(across(flows, step))` gathers its refusals, as `tag` does per tagger. `tag`'s `tagger(flow)` and
hosted `_seam` move inside its steps. The input's other flows run; every refusal prints at the end.

### D3

**The unapproved flow.** In `prepare`, a named flow outside `approved_flows(run)` is refused by name with the same
remedy the all-unapproved refusal gives, while the approved flows are assembled. The scenario
`every-approved-flow-renders` now reads "…and the invocation names them" (see `specs/image-generation/spec.md`).

### D4

**`show`'s frame.** `report` reads the frame inside a guard. A `Refusal` — unreadable, unknown version — or a frame
without `photo` prints `photo: <the refusal>` and the report lists flows and artifacts as usual. Stage verbs still
refuse such a frame. `show` exits 0, as it does for an unreadable artifact.

### D5

**The Ollama refusals.** Each names `fetch the pinned files (`{PROVISION}`), then build the model (`{remedy}`)`, the
mismatch refusal's shape. `tests/test_caption.py:595-610`'s assertion on the build command still holds.

### D6

**The undeclared artifact.** `provision.py` stays standard-library only: `Dockerfile` copies it alone into the image
and `tools/download_models.sh` runs it by path, so an `isekai` import fails there. `wiring.load_vocabulary` and
`wd14.verified_paths` catch `UnknownArtifact` and raise `shared/vocabulary.py`'s refusal: `<dest> is not declared in
<manifest path>`, naming `tools/derive_vocabulary.py` as the fix. Amended at the build, on the operator's choice.

### D7

**The host-key read.** `printed_fingerprint` reads `"$API/pods/$pod_id/logs?tail=5000&source=container"` with the
same `--max-time 10`, and keeps the last match (`tail -n 1`, not `head -n 1`). `since` is no longer taken for the
read. The stub test asserts the URL and that a later key line wins.

### D8

**Keys demanded, keys known.** In `tests/test_spec_bindings.py`, a `living_keys(root)` reads `openspec/specs/` alone;
`test_every_key_has_a_test` demands `spec_keys(root) & living_keys(root)` — the living keys less those a delta
removes. `test_every_marker_names_a_key` still checks against `spec_keys(root)`, so a marker may name a key an open
delta adds. A twin holds each: a delta-only key with no test passes; a living key with no test fails. This cut's
delta carries only the image-generation block; each build task writes its scenario, below, into the delta beside its
test.

## The new scenarios

Each goes into the change's delta as a MODIFIED block: the living requirement, unchanged, with the scenario added.

**`tagging`** — *Both taggers run for a flow that declares the tagger, and the hosted one runs on the model the flow
names* ([D1](#d1)):

```
#### Scenario: a command naming only untagged flows names the next verb
- **Key:** `tagging:declaration:only-untagged-flows-name-the-next-verb`
- **Layers:** unit
- **WHEN** the tag verb names only flows whose manifests declare no tagger
- **THEN** the invocation is refused, saying `tag` has nothing to do for them
- **AND** the message names the `sheet` command to run next
```

**`cli`** — *Every stage verb requires the flows it acts on, and takes more than one* ([D2](#d2)), and *Inspection
prints the run directory with its provenance* ([D4](#d4)):

```
#### Scenario: one flow's refusal leaves the input's other flows
- **Key:** `cli:flow-selection:one-flows-refusal-leaves-the-others`
- **Layers:** unit
- **WHEN** a stage verb names more than one flow, and one of them refuses for an input
- **THEN** the input's other named flows are still acted on
- **AND** every refusal is reported together at the end

#### Scenario: a frame it cannot read is marked
- **Key:** `cli:show:an-unreadable-frame-is-marked`
- **Layers:** unit
- **WHEN** a run's frame is unreadable, declares an unknown version, or lacks its photograph
- **THEN** the report marks the frame with its refusal in place of the photograph line
- **AND** it lists the run's flows and artifacts as it would otherwise
```

**`caption`** — *A hosted model that is not running or not installed is refused before any attempt is spent*
([D5](#d5)):

```
#### Scenario: a model with no readable record names the files first
- **Key:** `caption:reachability:no-record-names-the-files-first`
- **Layers:** unit
- **WHEN** the runtime holds no readable record of the declared model
- **THEN** the command refuses naming the command that fetches the pinned files, then the one that builds the model
```

**`model-provisioning`** — *The tag vocabulary and the model it indexes are provisioned from one manifest*
([D6](#d6)):

```
#### Scenario: an artifact the manifest does not declare is refused
- **Key:** `model-provisioning:vocabulary:an-undeclared-artifact-is-refused`
- **Layers:** unit
- **WHEN** a caller asks a manifest for an artifact it does not declare
- **THEN** the command refuses naming the artifact and the manifest it searched
```

## Dependencies

None.

## Risks / Trade-offs

- **The boot prints more than 5000 container lines before the read** → the key line falls out of the backfill and
  the check refuses, as today's fails closed; a cold volume's download is the only large source.
- **A refusal per flow prints more lines** → each names its flow; that is the point.
- **The tail read is unproven live** → proved at the next metered session; the stub test holds its shape.

## Verdict

**feasible** — small, tested fixes under existing requirements.
