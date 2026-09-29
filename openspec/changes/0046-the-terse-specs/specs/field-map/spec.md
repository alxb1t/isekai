## MODIFIED Requirements

### Requirement: The table is one authored artifact and the reverse direction is derived

The system SHALL hold the tag-to-criterion assignment in exactly one committed artifact, and SHALL derive
the `field → tags` direction from it rather than storing a second copy. It SHALL NOT place the assignment
inside a flow's schema document.

Two stored copies of one mapping drift, and the cheatsheet and the router are one table read two ways. Kept out of
the schema, fixing one tag's criterion is one edit rather than an edit to every digest-pinned flow: `twintails`
answers *hair silhouette* in every flow that declares that field
([D2](../../../docs/decisions.md#d2--a-table-fills-the-sheet)).

#### Scenario: the reverse index is derived and never authored
- **Key:** `field-map:table:the-reverse-index-is-derived`
- **Layers:** unit
- **WHEN** the table is loaded
- **THEN** the `field → tags` grouping is computed from the `tag → field` entries
- **AND** no second stored mapping is read

#### Scenario: the table is not read from a flow directory
- **Key:** `field-map:table:it-is-not-read-from-a-flow`
- **Layers:** unit
- **WHEN** the table is loaded
- **THEN** it is read from outside every flow directory
- **AND** no flow's schema document declares which tags exist

#### Scenario: the table carries a name, a revision and a digest
- **Key:** `field-map:table:it-names-its-own-revision`
- **Layers:** unit
- **WHEN** the table is loaded
- **THEN** it reports a name, a revision and a digest of its own bytes
- **AND** a consumer can record which revision it was read at

### Requirement: A tag has exactly one primary criterion and may be browsed under several

The system SHALL give every tag in the table exactly one primary criterion, SHALL permit a tag to list
further criteria it may be browsed under, and SHALL route by the primary alone.

Criteria overlap in use: the operator's approved sheets file `navel` under clothes, pose and body shape, and `lips`
is a criterion of its own in one flow and part of *expression* in another. Routing needs one answer and browsing
needs all of them, so the table carries both, and exactly one primary is checked when the table loads.

#### Scenario: every tag declares exactly one primary criterion
- **Key:** `field-map:membership:every-tag-has-exactly-one-primary`
- **Layers:** unit
- **WHEN** the table is loaded
- **THEN** every tag has exactly one primary criterion
- **AND** a tag with none, or with two, is refused naming the tag

#### Scenario: a tag may be browsed under criteria that are not its primary
- **Key:** `field-map:membership:a-tag-may-be-browsed-under-several`
- **Layers:** unit
- **WHEN** a tag lists further criteria beside its primary
- **THEN** the `field → tags` direction returns it under each of them
- **AND** the `tag → field` direction returns only its primary

### Requirement: The excluded list names what no criterion can hold, and nothing is in both

The system SHALL hold a list of tags that answer no criterion, SHALL refuse a table in which any tag
appears in both that list and a criterion's group, and SHALL NOT serve the excluded list to any surface.

A tag that routes nowhere is dropped either way, so the list changes the record, not the behaviour: it tells a
deliberate absence, such as `realistic` or `photorealistic`, from an omission. It is an assertion about the table,
not material the operator browses, so no surface shows it.

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

### Requirement: Every criterion any flow declares has an entry, and an empty entry is legal

The system SHALL require an entry for every field name declared by any tracked flow's schema, and SHALL
accept an entry whose group is empty.

A criterion with no entry is indistinguishable from one nobody has authored yet, and the surface would silently
omit its row. An empty group is an honest answer: a criterion the vocabulary cannot express, such as an age band,
is a fact about the vocabulary, and the table is where to say it.

#### Scenario: a criterion with no entry is refused
- **Key:** `field-map:coverage:every-declared-field-has-an-entry`
- **Layers:** unit
- **WHEN** a tracked flow declares a field the table has no entry for
- **THEN** loading the table is refused, naming the field and the flow
- **AND** the refusal does not depend on which flow is being acted on

#### Scenario: an empty group is accepted and reported as empty
- **Key:** `field-map:coverage:an-empty-group-is-legal`
- **Layers:** unit
- **WHEN** a criterion's entry declares no tags
- **THEN** the table loads
- **AND** the `field → tags` direction returns an empty group for it rather than omitting the criterion

### Requirement: Routing places a tag by its primary and drops what the flow does not declare

The system SHALL place each tag from a tagger's list into its primary criterion, SHALL drop a tag whose
primary the acting flow does not declare, SHALL preserve the order the tagger returned within each
criterion, and SHALL NOT emit any tag the tagger did not return.

The router cannot invent, because its input is already the vocabulary
([D2](../../../docs/decisions.md#d2--a-table-fills-the-sheet)). Dropping by declared field lets one table serve
every flow: a tag whose criterion the flow does not declare has nowhere legal to go. Keeping the tagger's order
costs nothing and helps the operator delete: a hierarchy arrives general form first, and the general forms are what
go.

#### Scenario: a tag is placed in its primary criterion
- **Key:** `field-map:routing:a-tag-goes-to-its-primary`
- **Layers:** unit
- **WHEN** a tagger's list is routed for a flow that declares a tag's primary criterion
- **THEN** the tag appears in that criterion and in no other
- **AND** no language model is reached

#### Scenario: a tag whose criterion the flow does not declare is dropped
- **Key:** `field-map:routing:an-undeclared-criterion-drops-its-tags`
- **Layers:** unit
- **WHEN** a tag's primary criterion is not in the acting flow's schema
- **THEN** the tag appears nowhere in the result
- **AND** routing is not refused for it

#### Scenario: the tagger's order survives inside each criterion
- **Key:** `field-map:routing:the-tagger-s-order-is-kept`
- **Layers:** unit
- **WHEN** several tags route to one criterion
- **THEN** they appear in the order the tagger returned them
- **AND** no second ordering is applied

#### Scenario: nothing is emitted that the tagger did not return
- **Key:** `field-map:routing:no-tag-is-invented`
- **Layers:** unit
- **WHEN** a list is routed
- **THEN** every tag in the result was in the input list
- **AND** no tag is completed, corrected or substituted on the way
