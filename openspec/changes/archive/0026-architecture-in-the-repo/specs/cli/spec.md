## MODIFIED Requirements

### Requirement: The pipeline surface is the only entry point, and its verbs are subcommands

The system SHALL expose the staged pipeline as subcommands of a module entry point, and that entry
point SHALL be the only command-line surface the system offers.

A pipeline that stops for a human cannot have a one-command surface, so it needs verbs. They were added
beside the single-command render surface rather than into it, so that the path in use at the time was
not disturbed while the new one was unproven; that surface is deleted in this version, and what was a
second entry point is now the only one. Subcommands under one parser rather than several scripts keeps
argument handling in one place and the entry point's import guard to a single target — which is the
reason the shape survives its original justification.

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

Reading and filling a sheet are cheap and per-photograph; rendering is where the money is, and a boot
costs roughly eight renders — so a single-photograph invocation is mostly overhead. Taking many
identifiers at once is what lets one boot serve a batch. The default is one because the cheap option
should be what happens when nothing is asked for.

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

