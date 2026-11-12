## ADDED Requirements

### Requirement: An edit is one flat directory, pinned by its digest

The system SHALL keep each edit as one flat directory under `edits/`, named for what it does and its base, holding
`edit.json` and `graph.json`. It SHALL read the manifest at load, refusing a key it does not read and a key it
requires and lacks, naming each. Every tracked edit SHALL be held by equality to a committed digest over every
regular file of its directory, and each committed digest SHALL appear in the changelog.

An edit changes a finished image, so an identifier that silently meant another configuration would make two
records of one name disagree. The directory is flat because the digest covers regular files only
([D14](../../../docs/decisions.md#d14--a-flow-is-one-flat-directory) holds the same for a flow).

#### Scenario: a tracked edit loads with every dial declared
- **Key:** `edit:directory:a-tracked-edit-loads`
- **Layers:** unit
- **WHEN** `tattoo-wai` is loaded
- **THEN** its prompt, dials, nodes, checkpoint, ControlNet and union type are those its manifest states
- **AND** no value is computed

#### Scenario: a wrong key is refused
- **Key:** `edit:directory:a-wrong-key-is-refused`
- **Layers:** unit
- **WHEN** a manifest carries a key the build does not read, or lacks one it requires
- **THEN** the load is refused, naming the key and the keys it reads

#### Scenario: a changed file fails the pin
- **Key:** `edit:directory:a-changed-file-fails-the-pin`
- **Layers:** unit
- **WHEN** a byte of `edit.json` or `graph.json` of a tracked edit changes
- **THEN** the pin test fails, naming the edit

#### Scenario: a pinned digest is recorded in the changelog
- **Key:** `edit:directory:the-digest-is-recorded`
- **Layers:** unit
- **WHEN** a tracked edit's committed digest is looked up in the changelog
- **THEN** an entry carries it

#### Scenario: the graph names the models the manifest declares
- **Key:** `edit:directory:the-graph-names-the-declared-models`
- **Layers:** unit
- **WHEN** `graph.json` of a tracked edit is read
- **THEN** its checkpoint, ControlNet and union type are those `edit.json` declares

### Requirement: The ink is cut by `isekai ink`

The system SHALL offer `isekai ink <image> <out>` with `--outline <mask.png>`, `--neutral` or `--no-neutral`, and
`--depth` between 1.0 and 2.0, free and local. It SHALL write a PNG layer to be multiplied over a render: bare
skin white, the ink its colour where there is ink. With an outline it SHALL keep the ink inside the outline only,
as the layer's alpha, neutral on and depth 1.6; with none it SHALL keep the whole image, neutral off and depth 1.0;
a flag SHALL override its default. **Neutral** SHALL set the three channels to the layer's luminance, and
**depth** SHALL raise the layer's Multiply factor to the power. An outline whose inside reads darker than the bare
skin beside it, in any one channel, by more than the skin's own variation SHALL be refused, and the refusal SHALL
name its fix. Such ink would otherwise be read as skin and wiped out.

The tattoo photograph is read here and nowhere else, and the layer carries pixels only, so the photograph never
reaches a run or a pod.

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
- **WHEN** an outline fitted to a solid fill is extracted, and the fill is darker than the skin around it in one
  channel alone
- **THEN** the extraction is refused, naming the fix: widen the outline over the skin
- **AND** the same fill, under an outline that also covers bare skin, keeps visible ink

#### Scenario: a depth out of range is refused at parse time
- **Key:** `edit:ink:a-depth-out-of-range-is-refused`
- **Layers:** unit
- **WHEN** `--depth` is below 1.0 or above 2.0
- **THEN** the invocation is refused before any image is read

### Requirement: An edit request is made from a render and its composite

The system SHALL offer `isekai edit <edit> <render> --composite <png>`, free and local, taking `--denoise`,
`--strength`, `--lines` and `--seed`. It SHALL derive the ink as the composite divided by the render, and from it
the mask, the crop box and the control, and SHALL write into the render's outputs group
`<seed>.edit-<k>.composite.png` and then `<seed>.edit-<k>.json`, `k` the next free number of that seed. The
composite SHALL be kept as pixels only. The record SHALL name the edit and its digest, the source and the digests
of the source and the composite, the sampling seed, every dial as it ran, the dials overridden, and the crop. The
seed SHALL be drawn as a render's is, and `--seed` SHALL repeat it. A request with no image beside it is pending.
A source that is an edit's image SHALL chain: the next edit is made from it.

An edit lives beside its source because a run's one channel is its directory, and every artifact records what
shaped it. The tattoo photograph is never a part of the request.

#### Scenario: a request writes the composite and a pending record
- **Key:** `edit:request:a-request-writes-a-pending-record`
- **Layers:** unit
- **WHEN** the verb is given a render and a Multiply composite of it
- **THEN** the group holds `<seed>.edit-1.composite.png` and `<seed>.edit-1.json`, and no edit image
- **AND** the record names the digests, the seed, the dials and the crop

#### Scenario: a repeated seed repeats the request's draw
- **Key:** `edit:request:a-repeated-seed-repeats-the-draw`
- **Layers:** unit
- **WHEN** two requests are made with the same `--seed`
- **THEN** both records hold that seed

#### Scenario: an override is recorded and marked
- **Key:** `edit:request:an-override-is-recorded-and-marked`
- **Layers:** unit
- **WHEN** a request is given `--denoise 0.3`
- **THEN** the record's dials hold 0.3 and its overridden list names `denoise`
- **AND** `edit.json` is as it was

#### Scenario: an edit's image chains
- **Key:** `edit:request:an-edits-image-chains`
- **Layers:** unit
- **WHEN** a second request names `<seed>.edit-1.png` as its render
- **THEN** it writes `<seed>.edit-2.*`, its record naming `<seed>.edit-1.png` as its source

#### Scenario: the composite is kept as pixels only
- **Key:** `edit:request:the-composite-is-kept-as-pixels-only`
- **Layers:** unit
- **WHEN** a composite carrying a colour profile and a text chunk is given
- **THEN** the kept composite carries neither
- **AND** its pixels are the composite's

#### Scenario: a request rents nothing
- **Key:** `edit:request:a-request-rents-nothing`
- **Layers:** unit
- **WHEN** the verb runs on a wiring with no endpoint
- **THEN** it succeeds and opens no session

### Requirement: A request the composite cannot support is refused

The system SHALL refuse a composite that does not decode or carries transparency; one that is not the render's
size; one darker nowhere past the ink threshold; and one lighter than the render anywhere past 8-bit rounding.
Each refusal SHALL name its fix. Where the render is near black no ink SHALL be read. A refused request SHALL
write nothing.

The division is defined only on a Multiply composite over a lit pixel, so anything else would bake the wrong ink.

#### Scenario: a composite of another size is refused
- **Key:** `edit:refusals:a-composite-of-another-size-is-refused`
- **Layers:** unit
- **WHEN** the composite's size is not the render's
- **THEN** the request is refused, naming both sizes
- **AND** nothing is written

#### Scenario: a composite with no ink is refused
- **Key:** `edit:refusals:a-composite-with-no-ink-is-refused`
- **Layers:** unit
- **WHEN** the composite is the render
- **THEN** the request is refused as carrying no ink

#### Scenario: a lighter composite is refused
- **Key:** `edit:refusals:a-lighter-composite-is-refused`
- **Layers:** unit
- **WHEN** the composite is lighter than the render past rounding at one pixel
- **THEN** the request is refused as no Multiply composite

#### Scenario: a composite with transparency is refused
- **Key:** `edit:refusals:a-composite-with-transparency-is-refused`
- **Layers:** unit
- **WHEN** the composite carries a transparent pixel
- **THEN** the request is refused, naming the flattening

#### Scenario: a near black render reads no ink
- **Key:** `edit:refusals:a-near-black-render-reads-no-ink`
- **Layers:** unit
- **WHEN** the composite differs from the render only where the render is near black
- **THEN** the request is refused as carrying no ink

### Requirement: The crop is the tattoo's own, widened and grown by two guards

The system SHALL take the crop box as the mask's box plus the margin, clipped to the image; SHALL widen it to an
aspect no thinner than the declared minimum; and SHALL grow it until the upscale to the sampling size is at most
the declared maximum, refusing a box the image cannot grow to that. The sampling size SHALL be the box scaled to
the declared long side, each side a multiple of 8. The record SHALL say whether either guard moved the box.

A thin strip and a tiny tattoo sample badly, and the pod sees only the crop.

#### Scenario: the box is the mask's plus the margin
- **Key:** `edit:crop:the-box-is-the-masks-plus-the-margin`
- **Layers:** unit
- **WHEN** a tattoo's mask spans a box inside the image
- **THEN** the crop box is that box grown by the margin on each side

#### Scenario: a thin strip is widened
- **Key:** `edit:crop:a-thin-strip-is-widened`
- **Layers:** unit
- **WHEN** the box is thinner than one to two
- **THEN** the box is widened to one to two and the record says widened

#### Scenario: a tiny tattoo is grown
- **Key:** `edit:crop:a-tiny-tattoo-is-grown`
- **Layers:** unit
- **WHEN** the upscale to the sampling size would pass the maximum
- **THEN** the box is grown until it does not and the record says grown

### Requirement: A render session runs every pending edit

The system SHALL, when `isekai render` names collections and no request, run every pending edit of each in the
same pod, after its renders, in each run's flow less each `--without` flow. It SHALL derive and check each pending
edit before anything is rented, refusing one whose source no longer has the recorded digest. A session SHALL be
allowed to hold edits alone. A request SHALL run no edit. The pod SHALL receive only the crop, its mask and its
control; the sampled crop SHALL be scaled, stitched through the mask and multiplied by the ink's lines here, and
`<seed>.edit-<k>.png` SHALL be written last, beside its source, after the record is completed with the graph's
digest, the runtime and the duration. A failed sampling SHALL leave its request pending.

One verb creates a pod ([D36](../../../docs/decisions.md#d36--a-render-session-is-isekai-render)), so an edit is
run by it.

#### Scenario: a pending edit runs beside the renders
- **Key:** `edit:session:a-pending-edit-runs-beside-the-renders`
- **Layers:** unit
- **WHEN** a session names a collection with an approval short of one image and a pending edit
- **THEN** the render is made first, then the edit's image appears beside its source
- **AND** the edit's record holds the graph's digest, the runtime and the duration

#### Scenario: a changed source refuses before the pod
- **Key:** `edit:session:a-changed-source-refuses-before-the-pod`
- **Layers:** unit
- **WHEN** a pending edit's source no longer has the recorded digest
- **THEN** the session is refused, naming the edit
- **AND** nothing is rented

#### Scenario: a session may hold edits alone
- **Key:** `edit:session:a-session-may-hold-edits-alone`
- **Layers:** unit
- **WHEN** nothing is short of its count and an edit is pending
- **THEN** the session runs the edit

#### Scenario: a flow taken out takes its edits out
- **Key:** `edit:session:a-flow-taken-out-takes-its-edits-out`
- **Layers:** unit
- **WHEN** `--without` names a run's flow that holds a pending edit
- **THEN** that edit stays pending

#### Scenario: a request runs no edit
- **Key:** `edit:session:a-request-runs-no-edit`
- **Layers:** unit
- **WHEN** the verb names a request
- **THEN** no pending edit runs

#### Scenario: a failed sampling leaves the request pending
- **Key:** `edit:session:a-failed-sampling-leaves-the-request-pending`
- **Layers:** unit
- **WHEN** the endpoint rejects the edit's graph
- **THEN** no edit image is written and the request is still pending
- **AND** the refusal names the discard that removes it

#### Scenario: the pod receives only crops
- **Key:** `edit:session:the-pod-receives-only-crops`
- **Layers:** unit
- **WHEN** an edit is sampled
- **THEN** the endpoint receives the crop, its mask and its control, each at the sampling size, and no other image

### Requirement: An edit's time is estimated from its work

The system SHALL add to a session's estimate, for each collection's pending edits, each at the higher of the
median of the newest recorded edit durations and the configured time per edit, and SHALL give the quote and the
session the same estimate.

An edit's median says nothing of a slower card, so the configured figure is the floor, as an image's is
([D26](../../../docs/decisions.md#d26--renders-run-on-a-rented-gpu)).

#### Scenario: with nothing recorded the configured figure is used
- **Key:** `edit:edit-limit:the-configured-figure-without-records`
- **Layers:** unit
- **WHEN** a pending edit has no recorded edit to take a median of
- **THEN** its time is the configured time per edit

#### Scenario: a median above the figure is used
- **Key:** `edit:edit-limit:a-median-above-the-figure-is-used`
- **Layers:** unit
- **WHEN** the newest recorded edits took a median above the configured figure
- **THEN** each pending edit is estimated at the median

#### Scenario: the quote and the session agree
- **Key:** `edit:edit-limit:the-quote-and-the-session-agree`
- **Layers:** unit
- **WHEN** a collection holds a short approval and a pending edit
- **THEN** the quote's estimate and the session's limit are taken from one function

### Requirement: An edit image is no render

The system SHALL leave an edit's image, its record and its composite out of every render listing: the seeds a
flow has rendered, a cell's newest image, the evaluator's runs. `isekai show` SHALL read an edit's files in a
group.

An edit is not a render: it carries no sheet, and counting it would make an approval look complete.

#### Scenario: the listings skip an edit
- **Key:** `edit:listing:the-listings-skip-an-edit`
- **Layers:** unit
- **WHEN** a group holds a render and its edit's image, record and composite
- **THEN** the seeds, the hub's images and the evaluator's runs list the render alone

#### Scenario: show reads an edit's files
- **Key:** `edit:listing:show-reads-an-edits-files`
- **Layers:** unit
- **WHEN** `show` runs over a run whose group holds an edit
- **THEN** none of its files is listed as unread

### Requirement: A discard takes edits

The system SHALL delete, with a discarded render, every edit of its seed: images, records and composites, before
it decides whether the group and its approval go. Given an edit image's path it SHALL delete that edit and every
edit whose source chain reaches it. Both SHALL be refused while a render session holds the collection.

An edit left in the group would keep the group and its approval alive, unseen on the hub
([D50](../../../docs/decisions.md#d50--the-last-render-takes-its-approval-and-a-flow-holds-only-its-own-files)).

#### Scenario: a render takes its edits
- **Key:** `edit:discard:a-render-takes-its-edits`
- **Layers:** unit
- **WHEN** a render with two chained edits is discarded
- **THEN** the render and both edits' images, records and composites are deleted

#### Scenario: the last render with an edit takes its approval
- **Key:** `edit:discard:the-last-render-with-an-edit-takes-its-approval`
- **Layers:** unit
- **WHEN** the only render of an approval, which has an edit, is discarded
- **THEN** the group and the approval go as they do without an edit

#### Scenario: an edit takes its chain
- **Key:** `edit:discard:an-edit-takes-its-chain`
- **Layers:** unit
- **WHEN** the first of two chained edits is discarded
- **THEN** both edits are deleted and the render stays

#### Scenario: a running session refuses it
- **Key:** `edit:discard:a-running-session-refuses-it`
- **Layers:** unit
- **WHEN** an edit's path is discarded while a render session holds the collection
- **THEN** nothing is deleted

### Requirement: Every file an edit's graph names has a manifest entry

The manifest SHALL declare every model file the graph of a tracked edit names, promax included, and every node
class of that graph SHALL be classified by name. A graph naming an undeclared file, or a class no list holds, MUST
fail the suite offline.

The checkpoint and the ControlNet an edit loads are found missing on a metered pod otherwise.

#### Scenario: the edit's files are declared
- **Key:** `edit:models:the-edits-files-are-declared`
- **Layers:** unit
- **WHEN** the graph of `tattoo-wai` is read
- **THEN** each model filename it names has a manifest entry

#### Scenario: a class absent from the mapping fails
- **Key:** `edit:models:a-class-absent-from-the-mapping-fails`
- **Layers:** unit
- **WHEN** the edit's graph holds a node class the mapping does not name
- **THEN** the check fails, naming the class
