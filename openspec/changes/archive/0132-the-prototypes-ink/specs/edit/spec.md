## MODIFIED Requirements

### Requirement: The ink is cut by `isekai ink`

The system SHALL offer `isekai ink <image> <out>` with `--outline <mask.png>`, `--neutral` or `--no-neutral`, and
`--depth` between 1.0 and 2.0, free and local. It SHALL write a PNG layer to be multiplied over a render: bare
skin white, the ink its colour where there is ink. With an outline it SHALL keep the ink inside the outline only,
as the layer's alpha, neutral on and depth 1.6; with none it SHALL keep the whole image, neutral off and depth 1.0;
a flag SHALL override its default. **Neutral** SHALL set the three channels to the layer's luminance, and
**depth** SHALL raise the layer's Multiply factor to the power. It SHALL read the white point as the `white`
percentile, per channel, of the lit pixels inside the outline, and compare it with nothing outside the outline. An
outline with no lit pixel inside it SHALL be refused, and the refusal SHALL name its fix.

The tattoo photograph is read here and nowhere else, and the layer carries pixels only, so the photograph never
reaches a run or a pod. An outline fitted to a solid fill reads the fill as its own white point, and the ink view
shows the result: the operator widens the outline over the skin
([D57](../../../docs/decisions.md#d57--the-white-point-is-the-prototypes-percentile)).

#### Scenario: a photograph with an outline
- **Key:** `edit:ink:a-photograph-with-an-outline`
- **Layers:** unit
- **WHEN** the verb is given a photograph and an outline
- **THEN** the layer's alpha is the outline and its channels are equal
- **AND** its darkest ink is deeper than the same extraction at depth 1.0

#### Scenario: a tattoo image keeps its colour
- **Key:** `edit:ink:a-tattoo-image-keeps-its-colour`
- **Layers:** unit
- **WHEN** the verb is given a coloured tattoo image and no outline
- **THEN** the layer is opaque everywhere and keeps the ink's colour
- **AND** the depth is 1.0

#### Scenario: a flag overrides its default
- **Key:** `edit:ink:a-flag-overrides-the-default`
- **Layers:** unit
- **WHEN** a photograph with an outline is given `--no-neutral` and `--depth 1.2`
- **THEN** the layer keeps its colour and is raised to the power 1.2

#### Scenario: bare skin is white
- **Key:** `edit:ink:bare-skin-is-white`
- **Layers:** unit
- **WHEN** a photograph of an arm with a dark fill is extracted
- **THEN** the skin away from the fill is white in the layer
- **AND** the fill is darker than the skin

#### Scenario: an outline with no bare skin inside it is refused
- **Key:** `edit:ink:an-outline-with-no-bare-skin-is-refused`
- **Layers:** unit
- **WHEN** an image with no lit pixel inside the outline is extracted
- **THEN** the extraction is refused, naming the fix: widen the outline over the skin, or light the photograph

#### Scenario: a tight outline over a solid fill is cut by the percentile
- **Key:** `edit:ink:a-tight-outline-over-a-solid-fill-is-cut-by-the-percentile`
- **Layers:** unit
- **WHEN** an outline fitted to a solid fill is extracted
- **THEN** the extraction returns a layer, and the fill, read as its own white point, is white in it
- **AND** the same fill, under an outline that also covers bare skin, keeps visible ink

#### Scenario: a depth out of range is refused at parse time
- **Key:** `edit:ink:a-depth-out-of-range-is-refused`
- **Layers:** unit
- **WHEN** `--depth` is below 1.0 or above 2.0
- **THEN** the invocation is refused before any image is read
