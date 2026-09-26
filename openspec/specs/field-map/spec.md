# Capability: `field-map`

## Purpose

One authored artifact assigning each tag in the pinned vocabulary to the identity criterion it answers.
It is read in two directions and in neither is it a model's output: `tag → field` fills a sheet from a
tagger's list with no language model in the path, and `field → tags` shows the operator every candidate for
a criterion he cannot name. A third part of the same artifact names the tags no criterion can hold, so an
absence is a decision on the record rather than a gap nobody noticed.

It is keyed by the **vocabulary** and not by any flow: `twintails` answers *hair silhouette* in every flow
that declares that field, so the assignment is a property of the tag list rather than of a schema. A flow
keeps saying which criteria *it* declares and in what order, and says nothing about which tags exist.

**Source:** `isekai/shared/field_map.py`, `config/field_map.json`, `tools/derive_field_map.py` ·
**Tests:** `tests/test_field_map.py`

## Requirements

### Requirement: The table is one authored artifact and the reverse direction is derived

The system SHALL hold the tag-to-criterion assignment in exactly one committed artifact, and SHALL derive
the `field → tags` direction from it rather than storing a second copy. It SHALL NOT place the assignment
inside a flow's schema document.

Two copies of one mapping is a drift defect this repository already has a genre for: the cheatsheet is the
table read one way and the router is the same table read the other, so a second stored index is a second
thing to keep true. Keeping it out of the schema is what makes fixing one tag's criterion one edit rather
than three frozen directories — a schema lives inside a flow whose whole directory is digest-pinned, and
`twintails` does not become a different kind of thing because a second flow was written.

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

### Requirement: Every tag in the table resolves in the pinned vocabulary

The system SHALL refuse a table containing a tag that is not in the vocabulary the flows pin, and SHALL
make that check part of the suite rather than of a review.

An authored artifact held against nothing rots silently, and this one rots in the worst direction: a tag
that no longer exists routes nothing and shows nothing, and both failures are invisible. Holding it against
the pin is this repository's own pattern — the artifact-name grep, the registry-keys-equal-artifact-strings
test — and it is free, because the vocabulary is already provisioned by digest.

#### Scenario: a tag outside the vocabulary is refused
- **Key:** `field-map:integrity:a-tag-outside-the-vocabulary-is-refused`
- **Layers:** unit
- **WHEN** a table entry names a tag the pinned vocabulary does not contain
- **THEN** loading it is refused, naming the tag
- **AND** no partial table is returned

#### Scenario: the check runs against the provisioned vocabulary
- **Key:** `field-map:integrity:the-check-runs-against-the-pin`
- **Layers:** unit
- **WHEN** the suite runs with the vocabulary provisioned
- **THEN** every tag in the committed table resolves in it
- **AND** the assertion names the vocabulary's revision

### Requirement: A tag has exactly one primary criterion and may be browsed under several

The system SHALL give every tag in the table exactly one primary criterion, SHALL permit a tag to list
further criteria it may be browsed under, and SHALL route by the primary alone.

One assignment per tag cannot describe how the criteria are actually used, and the operator's own approved
sheets are the evidence: he files `navel` under clothes, pose **and** body shape, `collarbone` under pose
and body shape, and `standing` under framing and pose. A structural case is worse — `lips` is a declared
criterion of its own in one flow and part of *expression* in another, so a single vocabulary-keyed
assignment is wrong in one of the two flows whichever way it is written. Routing needs one answer and
browsing needs all of them, so the table carries both and the ambiguity that remains is decidable: exactly
one primary, checked the moment the table exists.

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

A tag that routes nowhere is dropped either way, so the list changes no behaviour — it changes the record.
Without it there is no way to tell a deliberate absence from an omission, and `realistic` and
`photorealistic` reaching a sheet once would be indistinguishable from the twenty other meta tags nobody
had looked at yet. It is not served to a surface because it is an assertion about the table and not
material the operator browses; showing him the tags that are never an answer is the opposite of the
cheatsheet's purpose.

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

Completeness is checkable and absence is not: a criterion with no entry is indistinguishable from a
criterion nobody has authored yet, and the surface would silently omit the row. An empty group, by
contrast, is an honest answer — the vocabulary holds four tags for eyelashes in total and none at all for
an age band, so a criterion the tag list cannot express is a fact about the vocabulary and the table is the
right place to say so.

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

The router cannot invent because its input is already the vocabulary — a tagger whose output layer is the
tag list can only name tags that exist, which is the entire reason the sheet is allowed to change author.
Dropping by declared field is what keeps one table serving every flow: a criterion five of twenty-one tags
answer exists whether the acting flow asked for it or not, and a tag routed to a criterion the flow does
not declare has nowhere legal to go. Preserving the tagger's order costs nothing and is the operator's
deletion aid, because a hierarchy arrives general-form-first and the general forms are what he deletes.

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
