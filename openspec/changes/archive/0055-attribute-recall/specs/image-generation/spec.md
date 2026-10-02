## MODIFIED Requirements

### Requirement: A flow renders on another flow's seeds when the operator names it

When the operator names a source flow, the system SHALL render one image per seed of that flow's latest
render group for the same run, reading the seeds from filenames alone, and SHALL record the source flow on
each render. It SHALL refuse a run whose source flow has no render before any endpoint is acquired, SHALL
refuse a flow named as its own source, and SHALL accept neither a count nor an explicit seed beside a source.
Where the flow's approval is a copy of the source's, it SHALL refuse a run whose copy was not made from the
approval the source's latest renders came from, before any endpoint is acquired. Where the source renders first
in the same session, it SHALL refuse, before any endpoint is acquired, a copy not made from the source's latest
approval, and that check SHALL render nothing. It SHALL refuse, naming its file, an approval whose record of its
producer or origin is damaged.

```
render.sh <runs> S=1 T=S
   free pass: assemble S and T
   free pass: T in step with S's latest approval?  no ──▶ refused, no pod
   pod: render S into its latest approval's group, then T on those seeds
```

A render on the same seed starts from the same noise, so two flows differ only in what the operator changed
between them; a fresh seed would add a difference of its own as large as the one measured. The same holds for
the sheet: seeds from one approval under a sheet copied from another compare two prompts, silently.

#### Scenario: one render per source seed
- **Key:** `image-generation:seeds-from:one-render-per-source-seed`
- **Layers:** unit
- **WHEN** a flow is rendered with a source flow named and the source holds renders for the run
- **THEN** the flow renders exactly the source's latest group's seeds
- **AND** each render's record names the source flow

#### Scenario: a run without a source render is refused before the session
- **Key:** `image-generation:seeds-from:no-source-render-is-refused-first`
- **Layers:** unit
- **WHEN** a source flow is named and a run holds no render of it
- **THEN** the run is refused naming the source flow and the command that renders it
- **AND** no endpoint is contacted

#### Scenario: a copy out of step with the source's renders is refused first
- **Key:** `image-generation:seeds-from:a-copy-out-of-step-is-refused-first`
- **Layers:** unit
- **WHEN** the flow's approval is a copy of a source approval other than the one the source's latest renders
  came from
- **THEN** the run is refused naming both approvals and the command that brings them in step
- **AND** no endpoint is contacted

#### Scenario: a damaged approval record is refused by name
- **Key:** `image-generation:seeds-from:a-damaged-approval-record-is-refused`
- **Layers:** unit
- **WHEN** a source flow is named and the flow's approval records its producer or its origin in a damaged shape
- **THEN** the run is refused naming the approval's file
- **AND** no endpoint is contacted

#### Scenario: a copy behind a source that renders first is refused first
- **Key:** `image-generation:seeds-from:a-copy-behind-a-source-rendering-first-is-refused-first`
- **Layers:** unit
- **WHEN** the source renders first in the same session and the flow's approval is a copy of an older source
  approval
- **THEN** the run is refused naming both approvals and the command that copies the latest
- **AND** no endpoint is acquired

#### Scenario: the check before the source renders takes no endpoint
- **Key:** `image-generation:seeds-from:the-check-before-the-source-takes-no-endpoint`
- **Layers:** unit
- **WHEN** the check against a source that renders first is asked for beside an endpoint
- **THEN** the invocation is refused before any run is opened

#### Scenario: a flow is not its own source
- **Key:** `image-generation:seeds-from:a-flow-is-not-its-own-source`
- **Layers:** unit
- **WHEN** the source flow named is one of the flows being rendered
- **THEN** the invocation is refused naming the flow

#### Scenario: a source excludes a count and explicit seeds
- **Key:** `image-generation:seeds-from:excludes-count-and-seeds`
- **Layers:** unit
- **WHEN** a source flow is named beside a count or an explicit seed
- **THEN** the invocation is refused before any run is opened
