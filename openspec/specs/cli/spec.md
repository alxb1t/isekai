# Capability: `cli`

## Purpose

The command-line surface: one entry point, seven verbs — six that run a stage and one that serves the
review surface — and every refusal a batch produced reported together rather than one at a time.

**Source:** `isekai/__main__.py`, `isekai/interface/cli.py`, `isekai/interface/wiring.py`,
`isekai/interface/run_view.py`, `flows/` ·
**Tests:** `tests/test_pipeline_cli.py`, `tests/test_generate.py`, `tests/test_resume.py`,
`tests/test_run_view.py`

The CLI is where a bad value is cheapest to catch — `--seed` and `--count` are range-checked **at parse
time**, so a bad one fails before a pod is touched rather than after a paid render. **There are no dial
flags.** A flow's dials are declared in `flows/summon-v1/flow.json` and are not reachable from the
command line, because a tuned dial is not a variant of a flow — it is an untested flow.

`isekai/__main__.py` is the path `runpy` resolves and is a shim; the parser, the verb table and the
dispatch functions are `isekai/interface/cli.py`, the composition is `isekai/interface/wiring.py`, and
the `show` verb's reader is `isekai/interface/run_view.py`. The verb is `show`; the file is not.

## Requirements

### Requirement: The pipeline surface is the only entry point, and its verbs are subcommands

The system SHALL expose the staged pipeline as subcommands of a module entry point, and that entry
point SHALL be the only command-line surface the system offers.

A pipeline that stops for a human cannot have a one-command surface, so it needs verbs. They were added
beside the single-command render surface rather than into it, so that the path in use at the time was
not disturbed while the new one was unproven; that surface is deleted in this version, and what was a
second entry point is now the only one. Subcommands under one parser rather than several scripts keeps
argument handling in one place and the stdlib-only guard to a single target — which is the reason the
shape survives its original justification.

#### Scenario: the pipeline verbs are reachable as subcommands
- **Key:** `cli:pipeline-surface:verbs-are-subcommands`
- **Layers:** unit
- **WHEN** the pipeline entry point is invoked with a subcommand
- **THEN** that stage runs

#### Scenario: the pipeline entry point needs no third-party import
- **Key:** `cli:pipeline-surface:entry-point-is-stdlib-only`
- **Layers:** unit
- **WHEN** the pipeline entry point is imported with third-party packages unavailable
- **THEN** the import succeeds
- **AND** the guard proving that condition is genuinely unavailable still holds

#### Scenario: an unknown subcommand is refused at parse time
- **Key:** `cli:pipeline-surface:unknown-verb-is-refused`
- **Layers:** unit
- **WHEN** an unrecognised subcommand is given
- **THEN** the invocation is refused before any work begins
- **AND** the available subcommands are listed

### Requirement: The rendering verb takes many photographs and either a count or explicit seeds

The system SHALL accept several run identifiers in one rendering invocation, SHALL accept either a
count of renders per photograph or an explicit list of seeds but not both, and SHALL default to one
render per photograph.

Reading and sorting are cheap and per-photograph; rendering is where the money is, and a boot costs
roughly eight renders — so a single-photograph invocation is mostly overhead. Taking many identifiers
at once is what lets one boot serve a batch. The default is one because the cheap option should be what
happens when nothing is asked for.

#### Scenario: several photographs render in one invocation
- **Key:** `cli:generate-signature:accepts-many-identifiers`
- **Layers:** unit
- **WHEN** several run identifiers are given
- **THEN** all of them are prepared and rendered in one invocation
- **AND** the endpoint is acquired once

#### Scenario: the count defaults to one
- **Key:** `cli:generate-signature:count-defaults-to-one`
- **Layers:** unit
- **WHEN** no count and no seed is given
- **THEN** one render is produced per photograph per approved flow
- **AND** its seed is drawn rather than fixed

#### Scenario: a count and explicit seeds cannot be combined
- **Key:** `cli:generate-signature:count-and-seed-are-exclusive`
- **Layers:** unit
- **WHEN** both a count and one or more seeds are given
- **THEN** the invocation is refused at parse time
- **AND** the message states that the two are alternatives

### Requirement: A new artifact version is requested explicitly

The system SHALL do nothing when a stage's artifact already exists, and SHALL require an explicit flag
to produce a new version.

Deciding automatically — writing a new version when some recorded field differs — would make an
invocation that sometimes costs money and sometimes does not, decided by a field the operator did not
look at. An explicit flag makes the spend visible in the command line that caused it.

#### Scenario: a repeat invocation does nothing
- **Key:** `cli:explicit-versions:repeat-invocation-is-a-no-op`
- **Layers:** unit
- **WHEN** a stage's command is invoked and its artifact exists
- **THEN** nothing is written and nothing is called
- **AND** the command reports that the stage is already complete

#### Scenario: the flag produces the next version
- **Key:** `cli:explicit-versions:flag-writes-the-next-version`
- **Layers:** unit
- **WHEN** the explicit flag is given
- **THEN** the next numbered artifact is written
- **AND** the previous one is unchanged

### Requirement: Re-running every command is the whole of resume

The system SHALL make running the pipeline's commands a second time, with the same arguments, change
no byte of the run directory and make no external call.

There is no state machine, so there is nothing to corrupt and nothing to repair. A crashed process, a
closed laptop and a week-long pause are the same event, and the answer to all three is the same
invocation. This is also the only assertion that can prove the state model works, and it needs no GPU
and no network.

#### Scenario: a second full pass changes nothing and calls nothing
- **Key:** `cli:resume:second-pass-is-inert`
- **Layers:** unit
- **WHEN** every pipeline command is run against a complete run, and then run again
- **THEN** not one byte of the run directory differs
- **AND** not one external call is made

### Requirement: Inspection prints the run directory with its provenance

The system SHALL provide a command that prints a run's artifacts, which version is active for each
stage, and what produced each one.

A filename carries only what resume decides on, which leaves a directory that is precise and unreadable.
This command is what a person reads instead — and it is also the answer to "where is this run", which is
why no progress file is needed before something other than a human is watching.

#### Scenario: inspection names the active version for each stage
- **Key:** `cli:show:active-version-is-marked`
- **Layers:** unit
- **WHEN** a run is inspected
- **THEN** each stage's versions are listed and the active one is marked
- **AND** approval is shown where the concept applies

#### Scenario: inspection reports what produced each artifact
- **Key:** `cli:show:producers-are-reported`
- **Layers:** unit
- **WHEN** a run is inspected
- **THEN** each artifact's producer is shown
- **AND** artifacts produced by different implementations are distinguishable in the output

### Requirement: Every refusal names the action that would resolve it

The system SHALL end every refusal with the action the operator can take, and SHALL NOT name an action
this build cannot perform.

This generalises the posture the evaluator already takes for a missing optional dependency: the failure
states the command that fixes it. A refusal that names a remedy the build does not have is worse than
one that names none, because it sends the operator looking for something that is not there.

#### Scenario: a refusal states a remedy
- **Key:** `cli:refusals:refusal-names-the-remedy`
- **Layers:** unit
- **WHEN** any pipeline command refuses
- **THEN** the message names the action that would resolve it
- **AND** that action is available in this build

#### Scenario: a refusal exits with a failure status
- **Key:** `cli:refusals:refusal-exits-non-zero`
- **Layers:** unit
- **WHEN** any pipeline command refuses
- **THEN** the process exits with a failure status
- **AND** the reason is written to the error stream

### Requirement: Every stage verb requires the flows it acts on, and takes more than one

The system SHALL require a flow selection on every stage verb — reading, sorting, reviewing, approving
and rendering — SHALL accept the selection more than once in a single invocation, and SHALL refuse an
invocation that names none, naming the flows that are tracked. It SHALL NOT fall back to every tracked
flow. It SHALL refuse a flow that is not tracked, at the point of selection, naming the flows that are.

A stage cannot act without knowing which flow asked, because the flow is what supplies the thing the
stage reads: its briefing, its schema, its graph and its dials. Falling back to every tracked flow is an
unbounded default that spends money at the last verb and burns a paid model call at the first — at
catalogue scale "everything tracked" is not a selection, it is the absence of one. The selection repeats
because flows batch: every flow named in one rendering invocation renders on one endpoint, and a second
boot costs what eight more renders would, so a flow left off the line is a flow that pays for its own
boot.

#### Scenario: a stage verb without a flow is refused
- **Key:** `cli:flow-selection:a-stage-verb-requires-a-flow`
- **Layers:** unit
- **WHEN** a stage verb is invoked with no flow named
- **THEN** the invocation is refused
- **AND** the message lists the tracked flows

#### Scenario: the selection repeats
- **Key:** `cli:flow-selection:the-flag-is-repeatable`
- **Layers:** unit
- **WHEN** a stage verb is given more than one flow
- **THEN** every named flow is acted on in that one invocation
- **AND** no named flow is silently dropped

#### Scenario: every stage verb accepts it
- **Key:** `cli:flow-selection:every-stage-verb-accepts-it`
- **Layers:** unit
- **WHEN** each of the five stage verbs is invoked with a flow named
- **THEN** none of them rejects the flag as unrecognised
- **AND** the inspection verb is the only one that does not take it

#### Scenario: an untracked flow is refused at selection
- **Key:** `cli:flow-selection:an-untracked-flow-is-refused`
- **Layers:** unit
- **WHEN** a stage verb names a flow that is not tracked
- **THEN** the invocation is refused naming that flow
- **AND** the message lists the flows that are tracked
