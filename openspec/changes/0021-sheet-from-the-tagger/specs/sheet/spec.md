## ADDED Requirements

### Requirement: The stage takes a tag list, a schema, a vocabulary and a field map, and returns fields

The system SHALL fill a sheet from exactly four inputs — a tag list, a schema, a vocabulary and a field map
— and SHALL store fields only. It SHALL NOT store an assembled prompt in a sheet, SHALL NOT be told which
flow requested the work, SHALL NOT read prose, and SHALL refuse naming the verb that produces the tag list
when that list is absent.

Storing the assembled prompt in the sheet creates a footgun where a human edits the prompt block and a
rebuild silently overwrites it. Keeping the stage ignorant of flows is what lets the same code serve every
flow without learning that flows exist: the composition root resolves a flow to its schema and hands the
stage a primitive.

**The input changes from prose to a tag list because of what the two producers can be wrong about.** A
reader asked for a field structure can invent a tag that merely looks canonical, and it did: `light` and
`dark` reached an assembled prompt as bare tags meaning *lighting* and *darkness*, past every guard, and one
sheet lost its subject count entirely. A tagger whose output layer **is** the vocabulary cannot make that
class of error, because naming a tag outside the list is not something it can express. It can be wrong about
the photograph, and that is the operator's to correct on the surface — which he does to every sheet
regardless, so sheet fidelity was never the metric. Prose remains a reading aid for the operator and stops
being a machine input, so a failed reader no longer blocks a sheet it does not feed.

**The tag list is a prerequisite rather than an aid, and the refusal is what says so.** A sheet with every
field empty is legal and therefore silent, so producing one when the tagger never ran would hide the one
thing the operator needs told. The rule that an absent tag artifact is an absent aid holds for a tagger that
contributes nothing to a sheet; it cannot hold for the one the sheet is filled from.

#### Scenario: a sheet stores fields and no prompt
- **Key:** `sheet:output:sheet-stores-fields-only`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** it carries one entry per schema field
- **AND** it carries no assembled prompt

#### Scenario: an empty field is a legal answer
- **Key:** `sheet:output:empty-field-is-legal`
- **Layers:** unit
- **WHEN** the tag list carries nothing a field can be filled from
- **THEN** that field is present and empty
- **AND** the sheet is not rejected for it

#### Scenario: the sheet records the vocabulary it was filled from
- **Key:** `sheet:output:sheet-names-its-vocabulary`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** it records the vocabulary's name, revision and digest
- **AND** that record is what a later reader checks the fill against

#### Scenario: the sheet records the field map it was routed by
- **Key:** `sheet:output:sheet-names-its-field-map`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** it records the field map's name, revision and digest beside the vocabulary's
- **AND** two sheets routed by different revisions of the table are distinguishable from the record alone

#### Scenario: the stage reads the tag list and not the prose
- **Key:** `sheet:output:the-stage-reads-the-tag-list`
- **Layers:** unit
- **WHEN** a sheet is filled for an input that has both a caption and a local tagger's list
- **THEN** the fields are filled from the tag list
- **AND** the caption is not read

#### Scenario: an absent tag list is a refusal naming the verb that fills it
- **Key:** `sheet:output:an-absent-tag-list-is-refused`
- **Layers:** unit
- **WHEN** a sheet is asked for an input whose local tagger's artifact is absent
- **THEN** the stage refuses, naming the verb that would produce it
- **AND** no sheet is written

### Requirement: Every tag in a sheet is in the vocabulary

The system SHALL emit no tag that is not in the vocabulary.

An invented tag that merely looks canonical is worse than an obviously invalid one, because it passes every
later check on its way into the prompt. **After this change the property holds by construction rather than
by filtering**: the tagger's output layer is the vocabulary, and the router emits only tags it was given.
The requirement stays because it is what a later reader checks a fill against, and because it is the
invariant any future producer would have to satisfy to be allowed near a sheet.

#### Scenario: every emitted tag is in the vocabulary
- **Key:** `sheet:purity:no-tag-outside-the-vocabulary`
- **Layers:** unit
- **WHEN** a sheet is written
- **THEN** every tag in every field is present in the vocabulary
- **AND** a tag the field map does not place contributes nothing at all

## REMOVED Requirements

### Requirement: The stage takes prose, a schema and a vocabulary, and returns fields

**Reason**: Replaced whole by *The stage takes a tag list, a schema, a vocabulary and a field map, and
returns fields*. The input changes and the stage gains a refusal, and `openspec` cannot add a scenario to a
requirement whose SHALL is being rewritten in the same breath.

**Migration**: None for a caller. `sheet`'s three output scenarios move across **under their existing keys**
— `sheet:output:sheet-stores-fields-only`, `sheet:output:empty-field-is-legal`,
`sheet:output:sheet-names-its-vocabulary` — and three are added. The verb, its flags and the artifact's
schema version are unchanged.

### Requirement: No absence clause and no out-of-vocabulary tag survives this stage

**Reason**: Split, because only half of it survives and `openspec` cannot retire one scenario in place. The
out-of-vocabulary half is added back whole as *Every tag in a sheet is in the vocabulary*, carrying
`sheet:purity:no-tag-outside-the-vocabulary` under its existing key. The absence-clause half goes: the
stage's input is a list of canonical tags, so there is no free text for a clause to arrive in and
`sheet:purity:absence-clause-is-dropped` would be unreachable rather than merely unneeded.

**Migration**: None for a caller, and deleting the guard is a **repair** rather than only a retirement.
`asserts_absence` in `isekai/shared/vocabulary.py` fires before any mapping runs, and swept over the whole
provisioned vocabulary it drops **37 of 8,106 canonical tags** — including `no bra` (93,761 posts) and
`no panties` (87,258), **both of which appear in the operator's own approved sheets**. A prompt still
carries no negation; what enforced it was a text rule on prose, and prose is no longer an input.

### Requirement: The mapping from phrase to canonical tag is deterministic and ordered

**Reason**: There is no phrase to map. The four-pass cascade — exact match, suffix completion, curated
spans, containment — existed to turn a language model's free text into canonical tags, and its only
production caller was the sorter's fill. A tagger's output is canonical on arrival, so 8,069 of the
vocabulary's 8,106 tags would terminate at the first pass and the other three would never run.

**Migration**: None. `map_phrase`, `CURATED`, `CURATED_SPANS`, `_curated_pass`, `_index_of`,
`contained_in`, `Vocabulary.words`, `Vocabulary.by_word`, `_spans` and `_in_order` are deleted with it.
**`normalise()` is not**: it is called by `Vocabulary.__contains__`, `count`, `search` and `read_tags`, and
by `isekai/shared/fields.py`'s `validate()` on the approval path, so a sheet's spelling refusal is
unchanged. The non-obvious insight the cascade held is preserved in this change's `design.md` D24 — a tag
list's canonicality is a property of the **producer's output layer**, not of a mapping applied afterwards.

### Requirement: The model is an injectable seam and its structure is constrained, not its content

**Reason**: There is no model. The stage reaches no network and no local inference; it reads one artifact
and one committed table and performs a dictionary lookup, so there is no seam to inject, no offline double
to satisfy an interface, and no response whose structure could fail to match the field list. Its three
scenarios — `sheet:seam:offline-double-satisfies-the-interface`,
`sheet:seam:structure-constrained-content-free` and `sheet:failure:structural-mismatch-is-permanent` —
describe a failure mode a deterministic router cannot have.

**Migration**: None for a caller. `Sorter`, `Sorting`, `FakeSorter`, `output_shape`, `sorter_prompt`,
`answers_from`, `SORTER_OPTIONS` and `SORTER_REMEDY` are deleted. The suite fills a sheet with no network as
before, and now without a double at all — a stronger form of the property the removed scenario asserted.
`BUDGETS["sheet"]` drops from 3 to 1, because a deterministic stage has no transient failure to retry.

### Requirement: The flow selects the sorter implementation, and the shape constraint travels with it

**Reason**: The stage has one implementation and it is selected by nothing. `CLAUDE.md` states that a
selectable implementation *"is removed only by the version that retires it"*, and this is that version:
`ClaudeSorter` and `OllamaSorter` both go, so `implementation` for this stage becomes a key that could hold
one value, which `CLAUDE.md`'s own rule calls not a declaration. All five `sheet:selection:*` scenarios
describe choosing between implementations, refusing an unknown one, constraining each one's output shape,
reading an answer from a response body, and naming a truncated response — none of which a dictionary lookup
can do.

**Migration**: **The manifest key stays.** `hosted.sorter` is a *required* key of the `hosted` block
(`isekai/foundation/flow.py:234`, read unguarded at `:429`), and removing `"sorter": "qwen3:8b"` from
`flows/summon-open-v1/flow.json` would move that flow's `manifest_digest` — which `CLAUDE.md` makes a new
flow identifier rather than an edit. It is carried **dead**, unread, exactly as `sheet.briefing.md` is, and
both have the same trigger: the version that deletes the flows they belong to. `Wiring.sorter`, `SORTERS`,
`sorter_for`, `_claude_sorter`, `_ollama_sorter` and the CLI's sorter seam check are deleted;
`DEFAULT_IMPLEMENTATION` survives, because the readers and the hosted taggers still resolve through it.
