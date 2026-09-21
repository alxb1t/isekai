## ADDED Requirements

### Requirement: The surface can show every candidate tag for every criterion the flow declares

The system SHALL answer, in one response, the tags each field the acting flow declares can be filled with,
SHALL include a field the table holds no tags for as an empty group rather than omitting it, SHALL order the
tags within each group by post count, and SHALL NOT serve the list of tags no criterion can hold.

The measured gap this closes is not ranking and not speed: the operator looks at a photograph, goes to type
a tag, and does not know what Danbooru calls the thing he is looking at. The autocomplete cannot help because
it needs a fragment he already has, and a fragment that matches nothing commits nothing — so the failure is a
dead end rather than a bad tag. Answering in one response is what makes browsing free: the whole table is
tens of kilobytes, a surface that has it can filter without a round trip per keystroke, and a surface that
never opens the reference pays nothing because the response is not on the page's own payload.

Ordering by post count is deliberate and is the design's standing rule rather than a default. A group is a
**filter** and the ordering inside it is the same global count every other tag surface uses, so no second
ranking enters the system — which is the decision a per-field ranking would have forced, and it is deferred
rather than taken quietly. A post-count **cutoff** was measured against the operator's own approved sheets
and refused: any cutoff aggressive enough to shorten the largest group hides tags he actually uses, and the
tags he reaches for are in the tail.

An empty group is present because the alternative is silent. A criterion the vocabulary cannot express — four
tags in total for one of them, none at all for another — is a fact worth showing, and a missing row is
indistinguishable from a criterion nobody has authored yet. The excluded list is withheld for the mirror
reason: it is an assertion about the table, and showing the operator the tags that are never an answer is
the opposite of what he opened the reference for.

#### Scenario: every declared criterion is answered with its candidates
- **Key:** `ui:cheatsheet:every-declared-criterion-is-answered`
- **Layers:** unit
- **WHEN** the candidates are requested for a flow
- **THEN** the response carries one group per field that flow's schema declares
- **AND** it carries no group for a field the flow does not declare

#### Scenario: a criterion with no candidates is present and empty
- **Key:** `ui:cheatsheet:an-empty-group-is-present`
- **Layers:** unit
- **WHEN** the table holds no tags for a declared field
- **THEN** that field is present in the response with an empty group
- **AND** the request is not refused for it

#### Scenario: candidates are ordered by post count
- **Key:** `ui:cheatsheet:candidates-are-ordered-by-post-count`
- **Layers:** unit
- **WHEN** a group carries more than one tag
- **THEN** the tags are ordered by descending post count
- **AND** each tag carries the count the pinned vocabulary records for it

#### Scenario: the excluded list is never served
- **Key:** `ui:cheatsheet:the-excluded-list-is-not-served`
- **Layers:** unit
- **WHEN** the candidates are requested
- **THEN** no tag from the excluded list appears in any group
- **AND** the excluded list is not carried in the response
