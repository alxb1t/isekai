## MODIFIED Requirements

### Requirement: An approval is copied once from another flow's approval, its seeds with it

When the operator names a source flow, the system SHALL write an approval under the target flow whose fields are the
source flow's latest approval's, validated against the target flow's schema and the vocabulary as any approval is, and
whose renders list the source approval's seeds — its listed seeds, then each seed its outputs group holds an image of —
its count raised to their number where it is lower. The copy SHALL name the target's newest sheet, SHALL record whether
its fields differ from that sheet's, and SHALL record that it is a copy and SHALL NOT record the source flow or
approval. The approve verb SHALL first fill a target holding no sheet from the photograph's tag list, as the sheet verb
fills one; asked of a target holding no sheet without that fill, the copy SHALL be refused, naming the sheet verb and
writing nothing. It SHALL refuse a run whose source flow has no approval, naming the way out. It SHALL write nothing
where the target's newest approval is a copy holding the same fields and the same seeds, listed or rendered, and SHALL
otherwise copy under the target's next number. It SHALL refuse a source that is the target itself or no tracked flow,
before any run is opened.

```
runs/<id>/summon-anime-wai/review/001.approved.json      renders {count 2, seeds []} · outputs/001/ 11.png 12.png
        │  approve --flow control-anime-wai --from summon-anime-wai <run>
        │  control-anime-wai/sheets/ empty? fill 001.json from photo/wd14/ first
        ▼
runs/<id>/control-anime-wai/review/001.approved.json     same fields; renders {count 2, seeds [11, 12]}; a copy;
                                                         sheet 1, control's own
```

Two flows are compared only on one prompt and one noise. A copy by hand carries the source's identifier; a second
approval by hand lets the prompts drift. The target's own validation keeps the copy honest. The copy lists the source's
seeds, so control and subject render the same seeds until a render names the source (`T=S`): that render reads the
source's latest seeds when it runs, and the copy's fields follow the source's only when the approve verb copies again. A
target that has rendered the seeds the source lists is in step, so a copy made before the source rendered is not
copied again once both have. The source's approval can always be cancelled or deleted with its renders. The copy's
sheet is the target's own, so a revision of the copy compares against a sheet the target holds
([D49](../../../docs/decisions.md#d49--a-control-flow-is-its-subject-with-the-face-chain-at-zero-copied-once)).

#### Scenario: the fields are copied and validated against the target
- **Key:** `review:copy-from:fields-are-copied-and-validated`
- **Layers:** unit
- **WHEN** a target flow is approved from a source flow's approval
- **THEN** the target's approval carries the source's fields
- **AND** a field the target's schema does not declare refuses the copy naming it

#### Scenario: the copy carries the source's seeds and names no source
- **Key:** `review:copy-from:the-copy-carries-the-seeds`
- **Layers:** unit
- **WHEN** a target flow is approved from a source approval whose group holds images
- **THEN** the approval's identifier is the target flow's, and its renders list the source's listed seeds, then each
  seed rendered
- **AND** its record says it is a copy and names neither the source flow nor its approval

#### Scenario: the copy names the target's own sheet
- **Key:** `review:copy-from:the-copy-names-the-targets-own-sheet`
- **Layers:** unit
- **WHEN** a target holding a sheet is approved from a source approval
- **THEN** the copy names the target's newest sheet, and whether its fields differ from it
- **AND** a revision of one of the copy's images approves against that sheet
- **AND** a target holding no sheet refuses the copy, naming the sheet verb, and no file is written

#### Scenario: a target with no sheet is filled first
- **Key:** `review:copy-from:a-target-with-no-sheet-is-filled-first`
- **Layers:** unit
- **WHEN** the approve verb copies a source approval into a target holding no sheet
- **THEN** the target's first sheet is filled from the photograph's tag list, and the copy names it

#### Scenario: no source approval refuses the copy
- **Key:** `review:copy-from:no-source-approval-is-refused`
- **Layers:** unit
- **WHEN** the source flow holds no approval for the run
- **THEN** the copy is refused naming the source flow and the command that approves it

#### Scenario: an equal copy writes nothing
- **Key:** `review:copy-from:an-approved-target-writes-nothing`
- **Layers:** unit
- **WHEN** the target's newest approval is a copy holding the fields and renders the copy would hold
- **THEN** nothing is written
- **AND** the existing approval is unchanged

#### Scenario: a copy made before the source rendered is in step once both have
- **Key:** `review:copy-from:a-copy-is-in-step-once-both-have-rendered`
- **Layers:** unit
- **WHEN** a target copied before its source rendered is copied again after both rendered the same seeds
- **THEN** nothing is written
- **AND** a target that has not rendered them is copied again, its renders listing the seeds

#### Scenario: a changed source approval is copied again
- **Key:** `review:copy-from:a-newer-source-approval-is-copied-again`
- **Layers:** unit
- **WHEN** the source's latest approval differs from what the target's newest approval holds, or that is no copy
- **THEN** the source's latest is copied under the target's next number
- **AND** the target's earlier approval is unchanged

#### Scenario: the source is a tracked flow other than the target
- **Key:** `review:copy-from:the-source-is-another-tracked-flow`
- **Layers:** unit
- **WHEN** the source named is the target itself or no tracked flow
- **THEN** the invocation is refused naming it
- **AND** no run is opened
