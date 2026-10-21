## ADDED Requirements

### Requirement: A draft carries how many images to render and which seeds, and approval checks them

The system SHALL carry in a draft, and into its approval, a count of images and a list of seeds, SHALL read a draft
or approval without them as a count of one and no seeds, and SHALL refuse approval of a count below the number of
seeds listed or a seed outside the range a render accepts, naming the field.

What the operator approves includes how many attempts the sheet gets and at which seeds. An old draft reads as it
always rendered.

#### Scenario: an old draft reads as one image
- **Key:** `review:renders:an-old-draft-reads-as-one`
- **Layers:** unit
- **WHEN** a draft without a count or seeds is read
- **THEN** it reads as a count of one and no seeds

#### Scenario: a count below its seeds is refused
- **Key:** `review:renders:a-count-below-its-seeds-is-refused`
- **Layers:** unit
- **WHEN** approval is asked for a draft with a count of one and two seeds
- **THEN** it is refused naming the count

#### Scenario: a seed out of range is refused
- **Key:** `review:renders:a-seed-out-of-range-is-refused`
- **Layers:** unit
- **WHEN** approval is asked for a draft with a negative seed
- **THEN** it is refused naming the seed
