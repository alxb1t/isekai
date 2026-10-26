## ADDED Requirements

### Requirement: A sheet is filled from another flow's tag list when the operator names it

The system SHALL fill a flow's sheet from another flow's tag list when the operator names that flow as the source,
through the target flow's own schema, vocabulary and field map, and SHALL record the source flow in the sheet's
producer. Where the source holds no tag list, it SHALL write every field empty, as for a flow that declares no
tagger.

```
summon-anime-wai/wd14/001.json ──▶ conjure's schema · vocabulary · field map ──▶ conjure-anime-wai/sheets/001.json
                                                                                  producer.tags_from: summon-anime-wai
```

Two flows that tag with the same pinned model read the same photograph the same way, so the second needs no tagging
of its own. A flow reads another's artifacts only when the operator names it
([D17](../../../docs/decisions.md#d17--input-above-flow-below)), and the sheet says whose tags it holds.

#### Scenario: a sheet is filled from the source's tag list
- **Key:** `sheet:tags-from:filled-from-the-sources-tag-list`
- **Layers:** unit
- **WHEN** a sheet is asked for a flow with another flow named as the source of its tags
- **THEN** its fields are routed from the source's tag list through the target's schema and field map
- **AND** its producer names the source flow

#### Scenario: no source tag list gives an empty sheet
- **Key:** `sheet:tags-from:no-source-tag-list-gives-an-empty-sheet`
- **Layers:** unit
- **WHEN** a sheet is asked from a source flow that holds no tag list
- **THEN** a sheet is written with every field present and empty
- **AND** its producer names the source flow
