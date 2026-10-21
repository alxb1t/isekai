## ADDED Requirements

### Requirement: An approval states how many images it renders, its listed seeds first

The system SHALL render, for an approval that states a count and seeds, its listed seeds first and then seeds drawn
at full width up to its count, distinct from each other and from those already rendered under it; an approval that
states neither SHALL render one drawn seed. A listed seed SHALL be rendered as it is, whatever its size.

The approval is what the operator agreed to, so how many images it makes is part of it. A seed typed as `1` renders
seed 1, as ComfyUI does; only a drawn seed needs the full width that keeps draws apart.

#### Scenario: listed seeds render first, the rest are drawn
- **Key:** `image-generation:approved-count:listed-seeds-first`
- **Layers:** unit
- **WHEN** an approval states a count of three and the seed `1`
- **THEN** seed 1 is rendered and two more are drawn
- **AND** the drawn seeds differ from each other and from 1

#### Scenario: an approval with no count renders one
- **Key:** `image-generation:approved-count:no-count-renders-one`
- **Layers:** unit
- **WHEN** an approval states no count and no seed
- **THEN** one seed is drawn and rendered

#### Scenario: a short approval renders only what it lacks
- **Key:** `image-generation:approved-count:only-the-shortfall-renders`
- **Layers:** unit
- **WHEN** an approval of count three already holds one image
- **THEN** two more are rendered

### Requirement: A render records how long it took

The system SHALL record in every render the seconds the endpoint took to produce it, from submission to the image's
arrival.

A session's limit is estimated from what renders actually took; a record without the time can only be guessed from.

#### Scenario: a render carries its duration
- **Key:** `image-generation:duration:a-render-carries-its-duration`
- **Layers:** unit
- **WHEN** a render is written
- **THEN** its record carries the seconds it took
