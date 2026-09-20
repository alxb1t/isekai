## ADDED Requirements

### Requirement: The source pane shows the caption one sentence to a block

The system SHALL render a caption's prose as one block per sentence rather than as paragraphs, and SHALL
derive that division in the browser from the prose it already holds, without a request and without a
second copy of the rule.

The complaint this answers is specific: *"I read the paragraph, go to the sheet, add a tag, come back —
and I have lost where I was reading."* A block boundary at every sentence gives the eye something to
return to, and it costs nothing, because the prose is already in the browser and the surface already
owns one rule for how a caption is divided. Putting the second rule beside the first is what stops the
two drifting; putting it on the server would send prose across a socket to be split and sent back.

Splitting on sentence-ending punctuation is naive against abbreviations and decimals. That is accepted
as a known edge rather than an unknown one: the prose is constrained by briefing to plain description of
a person, and the acceptance looks for it specifically.

#### Scenario: a caption is shown as sentences, not paragraphs
- **Key:** `ui:source:the-caption-is-shown-one-sentence-to-a-block`
- **Layers:** unit
- **WHEN** an input whose caption is a multi-sentence paragraph is opened
- **THEN** each sentence is rendered as its own block
- **AND** the prose's own text is unchanged, with nothing added, dropped or re-ordered

### Requirement: Both tag lists are shown beside the prose, raw and read-only

The system SHALL show every tag each tagger produced, in the order the artifact records, without
filtering any of them against the vocabulary, and SHALL make none of them committable.

The lists exist so the operator can see what was offered **before** the sorter narrowed it, and the
sorter's narrowing is exactly what he is trying to see behind — so a surface that filtered them would
answer a question he can already ask. Showing a score where the tagger returned one lets the list be
read in confidence order, which is what makes a long list cheap to scan and a wrong entry cheap to
dismiss: a low-scored tag sitting beneath a high-scored contradiction is refuted by the row above it.

They are read-only because the picker in the sheet is the only path into a field, and it is the only
path that validates. A chip that could commit would be a second writer into an artifact whose whole
correctness argument is that one function validates every value entering it.

#### Scenario: every tag is shown, and none of them can be committed
- **Key:** `ui:source:both-tag-lists-are-shown-raw-and-read-only`
- **Layers:** unit
- **WHEN** an input whose tag artifacts contain tags outside the flow's vocabulary is opened
- **THEN** every tag in both artifacts is present in the response the surface renders
- **AND** no interaction on either list writes to a draft

### Requirement: Vocabulary membership is decided by the server, not by the browser

The system SHALL resolve, for each tag it shows, whether the flow's pinned vocabulary contains it and
what its post count is, and SHALL deliver that with the input's own payload rather than through a
per-tag query.

Marking is what makes an unfiltered list usable: it shows at a glance which suggestions can actually be
committed, and a tag shown with no post count reads as the model's word rather than as Danbooru's, which
is the scepticism that defuses a measured hazard — a reader pushed toward a field list invented nineteen
identity marks across seven of ten subjects and its score fell from 0.518 to 0.307.

The tag search endpoint answers a **fragment query** and has no membership form, so marking a list of
forty tags through it would be forty round trips on the busiest pane in the surface. The vocabulary is
already resolved at startup and already held by the process that assembles this payload; deciding
membership there costs one dictionary lookup per tag and no request at all.

#### Scenario: the payload carries membership and count for every tag
- **Key:** `ui:source:vocabulary-membership-is-marked-by-the-server`
- **Layers:** unit
- **WHEN** an input with a tag artifact is requested
- **THEN** each tag in the payload carries whether the vocabulary contains it, and its post count where
  it does
- **AND** the surface makes no additional request to resolve any of them

### Requirement: A tag artifact that is absent is silent

The system SHALL render the source pane without a tag list when its artifact does not exist, SHALL NOT
refuse to open the surface for the absence, and SHALL NOT display a message explaining it.

There are three legitimate ways for one to be missing — a run captioned before the stage existed, a flow
that declares no hosted model, and a tagger call that failed — and none of them is a reason a sheet
cannot be reviewed. The tag lists are an aid; a surface that refuses to open because an aid is missing
has confused an aid for an input, and the startup refusals exist for what review genuinely cannot proceed
without: the flow, the run, the draft, the photograph's dimensions, the vocabulary and the bundle.

No message either. A line explaining an absence the operator caused by not running something is chrome
on the pane he spends the most time reading, and it would appear for every input of every flow that can
never have one.

#### Scenario: an input with no tag artifacts still opens
- **Key:** `ui:source:an-absent-tag-artifact-is-silent`
- **Layers:** unit
- **WHEN** an input whose run holds no tag artifacts is opened
- **THEN** the surface serves it and the payload reports the lists as absent
- **AND** no refusal is raised and no explanatory message is rendered
