## MODIFIED Requirements

### Requirement: The list is stored as it came, and narrowing it is another stage's job

The system SHALL store a tagger's output without canonicalising it, without filtering it against any
vocabulary and without re-ordering it by anything other than a score the tagger itself returned.

**The reason changes with this version and gets stronger.** It used to be that the raw list was what a model
offered *before the sorter narrowed it*, and the sorter's narrowing was what the operator was trying to see
behind. There is no sorter now: the local tagger's list **is** the sheet's source, and the thing that
narrows it is a committed table that drops every tag no criterion can hold. So the raw artifact is the only
place the dropped tags survive — it is how the operator sees what the router refused, and it is what makes a
missing group in the table findable instead of invisible. A filtered artifact would leave the table's gaps
unobservable from disk, which is the one failure mode an authored artifact has.

The same rule still holds for a tagger whose output reaches no sheet: its list is advisory, it will contain
wrong tags, and nothing is dropped for being outside the vocabulary. Marking which tags a vocabulary
contains is a display concern and is not filtering — the surface may mark, and this stage may not drop.

#### Scenario: nothing is dropped for being outside the vocabulary
- **Key:** `tagging:output:the-list-is-stored-unnarrowed`
- **Layers:** unit
- **WHEN** a tagger returns tags that are not in the flow's pinned vocabulary
- **THEN** every one of them is stored
- **AND** the stored order is the tagger's own
