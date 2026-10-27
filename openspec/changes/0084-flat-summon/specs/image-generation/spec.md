## ADDED Requirements

### Requirement: A flat flow is its subject with the face chain ending early and a flat style

The system SHALL hold a flat flow equal to its subject flow but for its style: the schema and the briefing byte for
byte; the graph equal but for the identity node's `end_at`, below one, and, where the flat flow restyles its hires
pass, that pass reading the plain checkpoint and the sheet's own conditioning; and the manifest equal once the
identifier, `ip_weight` and the prompt's trailer and negative are set aside, the trailer gaining `flat color, cel
shading, lineart` and the negative `realistic, photorealistic, 3d, semi-realistic`. A difference anywhere else SHALL
fail the suite naming the file.

```
flows/summon-anime-wai/            flows/summon-flat-anime-wai/
  schema.json, briefing    ══▶       byte-identical
  graph.json  end_at 1     ──▶       end_at below 1; the hires pass, where restyled, on the plain checkpoint
  flow.json   ip_weight    ──▶       a lower ip_weight; the flat trailer and negative
```

The face is set in the early steps, and the rendering style in the late ones, so ending the face chain early keeps
the likeness and frees the style. A flat flow is a variant, compared with summon on the same sheet and seed, never a
migration of it ([D15](../../../docs/decisions.md#d15--a-flow-is-named-for-what-it-is)).

#### Scenario: the flat flow's files equal the subject's
- **Key:** `image-generation:flat:files-equal-the-subject`
- **Layers:** unit
- **WHEN** a flat flow's schema and briefing are compared with its subject's
- **THEN** each is byte-identical

#### Scenario: the graph differs only in the face chain's end and the hires pass
- **Key:** `image-generation:flat:the-graph-differs-in-the-face-chains-end`
- **Layers:** unit
- **WHEN** a flat flow's graph is compared with its subject's
- **THEN** the identity node's `end_at` is below one, and nothing else differs but a restyled hires pass's inputs

#### Scenario: the manifest differs only in the style
- **Key:** `image-generation:flat:the-manifest-differs-in-the-style`
- **Layers:** unit
- **WHEN** a flat flow's manifest is compared with its subject's, the identifier, `ip_weight` and the prompt's trailer
  and negative set aside
- **THEN** they are equal
- **AND** the trailer and the negative hold the flat terms
