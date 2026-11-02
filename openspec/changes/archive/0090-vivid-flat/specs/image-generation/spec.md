## MODIFIED Requirements

### Requirement: A flat flow is its subject with the face chain ending early and a flat style

The system SHALL hold a flat flow equal to its subject flow but for its style: the schema and the briefing byte for
byte; the graph equal but for the identity node's `end_at`, below one; and the manifest equal once the identifier,
`ip_weight` and the prompt's trailer and negative are set aside, the trailer gaining `flat color, cel shading, anime
coloring, colorful` and the negative `realistic, photorealistic, 3d, semi-realistic`. A difference anywhere else SHALL
fail the suite naming the file.

```
flows/summon-anime-wai/            flows/summon-flat-anime-wai/
  schema.json, briefing    ══▶       byte-identical
  graph.json  end_at 1     ──▶       end_at below 1
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

#### Scenario: the graph differs only in the face chain's end
- **Key:** `image-generation:flat:the-graph-differs-in-the-face-chains-end`
- **Layers:** unit
- **WHEN** a flat flow's graph is compared with its subject's
- **THEN** the identity node's `end_at` is below one, and nothing else differs

#### Scenario: the manifest differs only in the style
- **Key:** `image-generation:flat:the-manifest-differs-in-the-style`
- **Layers:** unit
- **WHEN** a flat flow's manifest is compared with its subject's, the identifier, `ip_weight` and the prompt's trailer
  and negative set aside
- **THEN** they are equal
- **AND** the trailer and the negative hold the flat terms

## ADDED Requirements

### Requirement: A semireal and a vivid flow are their subject's face chain ending early, in a style of their own

The system SHALL hold `summon-semireal-anime-wai` and `summon-vivid-anime-wai` each equal to `summon-anime-wai` but
for its style, as a flat flow is held: the schema and the briefing byte for byte; the graph equal but for the identity
node's `end_at`, below one; and the manifest equal once the identifier, `ip_weight` and the prompt's trailer and
negative are set aside. The semireal flow's trailer and negative SHALL be its subject's; the vivid flow's trailer SHALL
be its subject's, and its negative SHALL gain `realistic, photorealistic, 3d, semi-realistic, monochrome, greyscale,
muted color`. A difference anywhere else SHALL fail the suite naming the file.

```
summon-anime-wai ─▶ face chain ending early, lower ip_weight ─┬─▶ summon-semireal-anime-wai  summon's prompt
                                                              ├─▶ summon-flat-anime-wai      the flat terms
                                                              └─▶ summon-vivid-anime-wai     no muted colour
```

Ending the face chain early keeps the likeness and frees the look; the prompt then sets how far the look moves. Each
was chosen by eye on the operator's photographs, as the cohort count cannot read a drawn face
([D46](../../../docs/decisions.md#d46--a-semireal-and-a-vivid-flow-are-flats-face-chain-in-other-looks)).

#### Scenario: their files equal the subject's
- **Key:** `image-generation:styled:files-equal-the-subject`
- **Layers:** unit
- **WHEN** the semireal or the vivid flow's schema and briefing are compared with its subject's
- **THEN** each is byte-identical

#### Scenario: their graph differs only in the face chain's end
- **Key:** `image-generation:styled:the-graph-differs-in-the-face-chains-end`
- **Layers:** unit
- **WHEN** the semireal or the vivid flow's graph is compared with its subject's
- **THEN** the identity node's `end_at` is below one, and nothing else differs

#### Scenario: their manifest differs only in its style
- **Key:** `image-generation:styled:the-manifest-differs-in-the-style`
- **Layers:** unit
- **WHEN** the semireal or the vivid flow's manifest is compared with its subject's, the identifier, `ip_weight` and the
  prompt's trailer and negative set aside
- **THEN** they are equal
- **AND** the trailer and the negative hold that flow's terms
