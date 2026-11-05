## MODIFIED Requirements

### Requirement: The excluded list names what no criterion can hold, and nothing is in both

The system SHALL hold a list of tags that answer no criterion: `photorealistic`, and every tag in the pinned
vocabulary containing `tattoo`. It SHALL refuse a table in which any tag appears in both that list and a criterion's
group, and SHALL NOT serve the excluded list to any surface. The tag search SHALL NOT return an excluded tag, and
approval SHALL refuse a sheet holding one, naming the tag, its field and the remedy.

A tattoo is outside what `summon` preserves
([D29](../../../docs/decisions.md#d29--what-summon-preserves)), and `photorealistic` describes how a picture was
rendered, not the person in it. The list is derived against the vocabulary, so a tattoo tag it gains is excluded
with no edit.

A sheet routed by an earlier table may still hold an excluded tag, so approval is the guard, not the routing alone.
The list is an assertion about the table, not material the operator browses, so no surface shows it.

#### Scenario: no tag is in both a criterion's group and the excluded list
- **Key:** `field-map:excluded:no-tag-is-in-both`
- **Layers:** unit
- **WHEN** the table is loaded
- **THEN** the excluded list and the union of every criterion's group are disjoint
- **AND** a tag in both is refused naming the tag

#### Scenario: a tag in neither is dropped without a record
- **Key:** `field-map:excluded:a-tag-in-neither-is-dropped`
- **Layers:** unit
- **WHEN** a tag is in the vocabulary, in no criterion's group and not in the excluded list
- **THEN** the `tag → field` direction returns nothing for it
- **AND** loading the table is not refused for the omission

#### Scenario: every tattoo tag and photorealistic are excluded
- **Key:** `field-map:excluded:tattoos-and-photorealistic-are-excluded`
- **Layers:** unit
- **WHEN** the committed table is loaded against the pinned vocabulary
- **THEN** its excluded list is `photorealistic` and every vocabulary tag containing `tattoo`
- **AND** no criterion's group holds any of them

#### Scenario: the tag search offers no excluded tag
- **Key:** `field-map:excluded:the-tag-search-skips-an-excluded-tag`
- **Layers:** unit
- **WHEN** a fragment is searched that an excluded tag contains
- **THEN** the matches and their count leave the excluded tag out
- **AND** every other tag containing the fragment is still returned, ranked

#### Scenario: approval refuses an excluded tag
- **Key:** `field-map:excluded:approval-refuses-an-excluded-tag`
- **Layers:** unit
- **WHEN** a draft, or an approval being copied, holds a tag on the excluded list
- **THEN** approval is refused naming the tag, its field and the remedy
- **AND** the draft is left untouched, and saving it is not refused
