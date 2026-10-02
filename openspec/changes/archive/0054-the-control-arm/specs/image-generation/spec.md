## ADDED Requirements

### Requirement: A control flow equals its subject flow but for the dials it zeroes

The system SHALL hold a control flow equal to its subject flow: the graph, the schema and the briefing
byte for byte, and the manifest equal once the identifier and the face dials are set aside, with those
dials at zero. A difference anywhere else SHALL fail the suite naming the file.

```
flows/summon-anime-wai/                    flows/control-anime-wai/
  flow.json   ip_weight 0.9, cn 0.8   ──▶    flow.json   the identifier; ip_weight 0, cn 0
  graph.json                          ══▶    graph.json           byte-identical
  schema.json                         ══▶    schema.json          byte-identical
  caption.briefing.md                 ══▶    caption.briefing.md  byte-identical
```

A control is a floor only while it differs from its subject in exactly the thing under test. Each flow is
pinned by its own digest, so a drift in the subject is caught by its pin and by the control's equality,
and the two move together or not at all
([D38](../../../../docs/decisions.md#d38--a-control-flow-is-its-subject-with-the-face-chain-at-zero)).

#### Scenario: the control's files equal the subject's
- **Key:** `image-generation:control:files-equal-the-subject`
- **Layers:** unit
- **WHEN** the control flow's graph, schema and briefing are compared with the subject's
- **THEN** each is byte-identical

#### Scenario: the manifests differ only in the identifier and the face dials
- **Key:** `image-generation:control:manifest-differs-only-in-the-face-dials`
- **Layers:** unit
- **WHEN** the two manifests are compared with the identifier and the face dials set aside
- **THEN** they are equal
- **AND** the control's face dials are zero

### Requirement: A flow renders on another flow's seeds when the operator names it

When the operator names a source flow, the system SHALL render one image per seed of that flow's latest
render group for the same run, reading the seeds from filenames alone, and SHALL record the source flow on
each render. It SHALL refuse a run whose source flow has no render before any endpoint is acquired, SHALL
refuse a flow named as its own source, and SHALL accept neither a count nor an explicit seed beside a source.
Where the flow's approval is a copy of the source's, it SHALL refuse a run whose copy was not made from the
approval the source's latest renders came from, before any endpoint is acquired. Where the source renders first
in the same session, it SHALL refuse, before any endpoint is acquired, a copy not made from the source's latest
approval, and that check SHALL render nothing.

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
