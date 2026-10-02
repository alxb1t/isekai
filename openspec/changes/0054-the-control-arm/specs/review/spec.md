## ADDED Requirements

### Requirement: An approval is copied from another flow's approval, recording where it came from

When the operator names a source flow, the system SHALL write an approval under the target flow whose fields
are the source flow's latest approval's, validated against the target flow's schema and the vocabulary as any
approval is, and whose record names the source flow and the approval it was copied from. It SHALL refuse a
run whose source flow has no approval, naming the way out, and SHALL write nothing for a target flow already
approved.

```
runs/<id>/summon-anime-wai/review/001.approved.json
        │  approve --flow control-anime-wai --from summon-anime-wai <run>
        ▼
runs/<id>/control-anime-wai/review/001.approved.json   same fields; the record names the source
```

Two flows are compared only on one prompt. A copy by hand carries the source's identifier and lies about its
provenance; a second approval by hand lets the prompts drift and voids the comparison. The target's own
validation is what keeps the copy honest: a schema the fields do not fit refuses as it would any draft.

#### Scenario: the fields are copied and validated against the target
- **Key:** `review:copy-from:fields-are-copied-and-validated`
- **Layers:** unit
- **WHEN** a target flow is approved from a source flow's approval
- **THEN** the target's approval carries the source's fields
- **AND** a field the target's schema does not declare refuses the copy naming it

#### Scenario: the record names its origin
- **Key:** `review:copy-from:the-origin-is-recorded`
- **Layers:** unit
- **WHEN** a target flow is approved from a source flow's approval
- **THEN** the approval's identifier is the target flow's
- **AND** its record names the source flow and the source approval's version

#### Scenario: no source approval refuses the copy
- **Key:** `review:copy-from:no-source-approval-is-refused`
- **Layers:** unit
- **WHEN** the source flow holds no approval for the run
- **THEN** the copy is refused naming the source flow and the command that approves it

#### Scenario: an approved target writes nothing
- **Key:** `review:copy-from:an-approved-target-writes-nothing`
- **Layers:** unit
- **WHEN** the target flow already holds an approval
- **THEN** nothing is written
- **AND** the existing approval is unchanged
