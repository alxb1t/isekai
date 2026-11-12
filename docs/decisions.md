# Decisions

The choices in force today, each with its reason and the change that made it. A decision states a
choice and why; it never repeats a value a file already declares — it names the file instead. When a
change overturns a decision, it edits this page; the change's own `design.md` keeps the history.

## The product

### D0 · Self-hosted, open-source, open models

**The product is self-hosted, open-source, and runs on open models only.** No SaaS and no closed
provider API: every model it runs is open-weight, on hardware the operator controls — a local model
server, a rented GPU. The repository is public, under Apache-2.0.

- **Why:** learning to run the whole stack is the point, and a closed API would hide exactly the part
  worth learning.
- **Made by:** the project's founding decision.

### D29 · What `summon` preserves

**Identity is face, hair, clothes and pose, held together. A tattoo is outside it.**

- **Why:** these are what a viewer checks first. The graph carries the face and the pose, and the
  approved sheet's tags carry hair and clothes
  ([D10](#d10--the-face-and-the-pose-are-carried-by-the-graph)). A tattoo is local and arbitrary;
  neither holds it, and bundling it would make every version a research version. A tattoo is added by an edit
after the flow ([D51](#d51--an-edit-is-one-flat-directory-pinned-by-its-digest)); the flows carry no ink.
- **Made by:** the project's founding decision; `0119`.

### D30 · A public repository, for learning

**The deliverable is a public repository, not a hosted service. Its payoff is learning and a
portfolio piece, not product polish.**

- **Why:** a portfolio piece is read, not signed up for, and tuning comes after the stack runs
  end to end.
- **Made by:** the project's founding decision.

### D33 · The operator decides what is rendered

**isekai places no restriction on content: no filter, no rating tag, no safety terms in the negative.** The operator
writes the positive prompt by approving the sheet, and answers for what renders — as JoyCaption reads without
restriction.

- **Why:** self-hosted, private by default, open models on the operator's own machine and pod
  ([D0](#d0--self-hosted-open-source-open-models)).
- **Made by:** `0036`.

## Stages and verbs

### D1 · Stage ① is two independent verbs

**`tag` writes the WD14 tags, then the JoyCaption tags; `caption` writes the prose. Each writes only its
own artifacts, and each tagger's refusal is collected on its own. Both write the photograph's, under
`photo/`, once for every flow.**

- **Why:** the sheet reads WD14's tags, so its input must not wait on Ollama. `tag` is the sheet's input
  and `caption` is the reviewer's aid, and neither needs the other.
- **`--new-version`** re-produces only what its own verb writes.
- **`prepare`** runs `tag`, then `caption`, per photograph, then its sheets; each refusal costs only its own
  step, so a caption's never holds back a sheet.
- **Made by:** `0020`, `0032`, `0103`, `0116`.

### D2 · A table fills the sheet

**The sheet is filled from WD14's tags by one authored table, `config/field_map.json`, read from tag to
field. No model decides a sheet.** No tag on its excluded list — `photorealistic` and every tag containing
`tattoo` — reaches a field: no group holds one, the tag search skips one, and approval and sheet preparation
refuse one.

- **Why:** WD14's tags are all in the vocabulary, because its label file *is* the vocabulary, and a table
  cannot invent a tag. The router placed 73% of the tags offered, and 90% of those survived review.
- **Why those excluded:** neither describes the person: `photorealistic` is how a picture was rendered, and a
  tattoo is outside what `summon` preserves ([D29](#d29--what-summon-preserves)). A sheet routed by an earlier
  table may still hold one, so approval refuses it rather than routing alone.
- **Made by:** `0021`, `0101`.

### D3 · The hand path stays

**`review` and `approve` stay working verbs.** The review UI is the guided path; the hand path stays. The Render
dialog's removal is `render --without`, so a session the page starts is one the terminal can run.

- **Why:** deleting it would make stage ③ a single point of failure for the whole pipeline.
- **Made by:** `0018`, `0108`.

### D4 · The UI runs stages only as the CLI's children

**The browser runs a stage only as the CLI's own verb, a child of the server, save the sheet a draft from
another flow fills; the one act in it that spends is Render's confirmation, after its quote of image total, bake total and limit.**
Prepare is `prepare` run as one child, each photograph through `tag`, `caption` and its sheets in turn,
and Render is `render` between gpunit's `volume up` and `volume down`. Every other write goes through the function that owns it: a draft, its edits and an
approval through `review`'s, a tick through the run's `assign`, a source through import, a deleted render's
thumbnails through the library's `drop_thumbnails`, the render through the render stage's `discard_render`, and
the approvals, drafts, sheets, source copies and own copies of the photograph's description its last render leaves
through review's `withdraw`, and a target's first sheet, when it is drafted from another flow, through `sheet()`,
which `interface/drafting.py`'s `draft_across` runs in the server's process before the draft, and an edit request through the edit stage's own function.

- **Why:** the CLI is the one path, so a stage the page starts is exactly the stage the terminal runs,
  and a write no stage owns would give a run file a second author. `draft_across` is the sequence
  `draft --flow` runs too, so the in-process fill is still the terminal's path; it is free, and it
  refuses before it writes. Spend behind a web page is bounded by what the operator read: the
  confirmation carries the quote it showed and the photographs taken out of it, and a quote grown since is
  refused. The quote compares
  image total, bake total and limit, not source or approval identity.
- **Made by:** `0018`, `0061`, `0062`, `0063`, `0080`, `0106`, `0108`, `0111`, `0112`, `0114`, `0116`, `0120`, `0122`.

### D42 · A new draft starts from the last approval

**Where a flow has an approved sheet, a new draft is copied from that approval, never from the sheet the
machine wrote.** The approval is left as it was. A revision of an image is copied from the approval the
image was rendered under, newest or not.

- **Why:** a correction starts from the last thing a person agreed with. Starting again from the machine's
  sheet would throw away every edit the operator made before.
- **Made by:** `0013`, `0065`.

## Models

### D5 · One arm

**JoyCaption reads the photograph and WD14 tags it, both on this machine. No hosted provider.**

- **Why:** [D0](#d0--self-hosted-open-source-open-models) — and the sheet needs nothing a closed
  model offered: the router places 73–77% of the tags with the local tagger and the table alone.
- **Made by:** `0022`.

### D6 · Ollama at a fixed local address, on a checked model

**Ollama is reached over plain HTTP at a fixed local address, never through a proxy, and the model
`config/caption.json` names is checked against `config/reader.json` before its first call.** The address is a constant, with no
flag and no environment variable. The call uses Ollama's own `/api/generate`, which carries the sampling
options the OpenAI-compatible endpoint cannot. Ollama's own record of the model must name the model and
projector files the manifest pins, or the call is refused and spends no attempt.
The ComfyUI transport ignores the environment's proxy the same way.

- **Why:** a photograph's destination must not be changeable by accident — an exported `http_proxy`
  once sent every photograph off the machine. An alias is a name the runtime resolves, and the files
  behind it shape the prose, so a caption can claim a pin only once those files are checked.
- **Accepts:** whatever holds port 11434 receives the photograph; nothing probes that it is Ollama.
  Reopen when a listener that is not Ollama is seen there, or the address stops being loopback-only.
- **Made by:** `0019`, `0033`, `0037`, `0052`, `0102`.

### D7 · WD14 is one artifact in two files

**WD14's model and its label file are pinned to one revision and verified together before the first
inference** — `config/vocabulary.json`.

- **Why:** row N of the label file names output N of the model. A pair from two revisions mislabels
  every tag, silently.
- **Made by:** `0020`.

### D8 · The base

**Every flow draws on WAI-illustrious-SDXL.** A flow on another base is a new flow, named for that base
([D15](#d15--a-flow-is-named-for-what-it-is)). The checkpoint and its digest belong to each flow.

- **Why:** the sheet's tags are how a render is steered, so the base's grasp of tags is the ceiling. Its
  LoRA ecosystem is what keeps the style library and a character LoRA within reach.
- **Made by:** `0010`.

### D37 · The evaluator's encoder shares no pin with the generator

**The evaluator finds, aligns and embeds a face with models only its own manifest pins,
`evaluation/eval_models.json`, and refuses to score when a destination or a digest there is one
`config/models.json` carries too.**

- **Why:** the identity adapter is trained to satisfy the generator's own recognizer, so a count on that
  recognizer is the adapter grading itself. A different encoder has different blind spots.
- **Made by:** `0053`.

### D39 · Attribute recall uses the sheet's tagger

**Attribute recall reads each render with WD14, the tagger whose tags fill the sheet, at the same floor, and
counts the approved sheet's scored tags it reads back.**

- **Why:** the sheet's vocabulary is that tagger's label set, so only it answers in the sheet's own words, and
  the same floor asks whether the render would put the tag on its own sheet. The generator is not trained to
  satisfy it, so this is not the case D37 guards against.
- **Accepts:** its blind spots are on both sides: a tag it cannot see is neither asked well nor read well.
  Reopen when a tag set a second tagger shares with the vocabulary exists.
- **Made by:** `0055`.

## The render

### D9 · Composition comes from noise

**The photograph never enters the latent: the render starts from an empty latent at full denoise.**

- **Why:** seeding the latent with the photograph blurred every render — linework came out about ten
  times weaker than the photograph's own. Starting from noise clears the style bar three times over.
- **Made by:** `0013`; `0014` deleted img2img.

### D10 · The face and the pose are carried by the graph

**The face and the pose are carried by the graph — InstantID's face embedding, OpenPose's pose — never
by words in a prompt. Hair and clothes are carried by the approved sheet's tags. A flow that takes no
photograph makes no identity claim.**

- **Why:** a face cannot be described into a render, so the embedding carries it and the pose leg carries
  the body. Hair and clothes are what tags name well, and a person corrects them at review.
- **Made by:** `0013`, `0017`.

### D11 · The photograph is scaled once

**The photograph is scaled once, before any node reads it, from its own header. It is refused past the
aspect limit, never clamped.** The numbers are `shared/image.py`'s.

- **Why:** every node must see one pixel grid, and no node can work out the size itself. A clamp would
  distort the aspect ratio.
- **Made by:** `0010`, `0011`.

### D12 · The flow owns the prompt's fixed words

**The quality words and the negative prompt belong to the flow; the subject's tags come from the
approved sheet.**

- **Why:** the prompt's fixed words are part of the flow's pinned configuration, changed only by a new
  flow or a recorded re-pin. The subject is the person's, corrected at review.
- **Made by:** `0016`, `0025`.

### D13 · The seed reproduces the graph, not the pixels

**The seed is recorded, and `--seed` reproduces the submitted graph, not the pixels.**

- **Why:** GPU computation does not promise bit-identical output, and identity does not need it to. One
  integer is the whole reproducibility contract.
- **Made by:** `0013`.

### D45 · A repeated seed is refused on every read

**An approval listing a seed twice is refused wherever `renders_of` reads it: render, the library and the review
UI.** One written before `v0.44`, when a slot could hold `0144` beside `144`, reads as damaged; the way on is a new
draft, approved without the repeat.

- **Why:** a seed listed twice renders one image twice. Reading an old repeat leniently would be a second rule for
  one file, and a change to what is rendered.
- **Made by:** `0089`.

## Flows

### D14 · A flow is one flat directory

**A flow is one flat directory of named files — `flow.json`, `graph.json`, `schema.json` — and it
shares nothing with another flow.** An edit is not a flow: it lives under `edits/`
([D51](#d51--an-edit-is-one-flat-directory-pinned-by-its-digest)).

- **Why:** the pin covers only the files directly in the directory, so a nested file would escape the
  freeze. Sharing nothing means a change to one flow can never change another.
- **Made by:** `0016`, `0022`, `0102`, `0119`.

### D15 · A flow is named for what it is

**A flow's identifier is `<verb>-<style>-<base>`, with `-v2` added only for a second generation of the
same combination.**

- **Why:** the base is in the name because other bases are candidates. A name describing the
  implementation behind a flow, rather than the flow, stops meaning anything when that implementation
  changes.
- **Made by:** `0022`.

### D31 · A flow declares whether it is tagged

**`flow.json` declares `"tagger": true | false`, and the sheet reads the declaration.** `tag` names no
flow; `sheet` fills an untagged flow's sheet with every field empty, for a person to fill, and Prepare tags a
photograph only for a flow that declares `true`.

- **Why:** flows that need no tag list are coming. A boolean, not a list of taggers: `tag` runs both
  together, so a list would declare a choice no flow makes.
- **Made by:** `0032`, `0103`.

### D38 · A control flow is its subject with the face chain at zero

**Superseded by [D49](#d49--a-control-flow-is-its-subject-with-the-face-chain-at-zero-copied-once) in `0111`: a copy
no longer names its source, and no check holds it to its source: a `T=S` render reads the source's seeds when it runs.**

- **Made by:** `0054`, `0103`; superseded by `0111`.

### D49 · A control flow is its subject with the face chain at zero, copied once

**`control-anime-wai` is `summon-anime-wai`'s directory with `ip_weight` and `identity_cn_strength` at 0, held equal
to it by a test. `approve --from` copies `summon`'s approval once — its fields and its seeds — and records neither
the source flow nor its approval; a draft from another flow's approval is taken once the same way; the copy names
the target's own sheet, filled first where it holds none, and a draft from another flow's image holds a copy of that
image in the target's `sources/`. A stage reads another flow's work only when the operator names it as a source; the
photograph's description is every flow's (D17).**

- **Why:** the floor is the same sheet and the same noise with the face mechanism off. The copy lists the source's
  seeds; a `T=S` render reads the source's latest seeds when it runs, and the copy's fields follow the source's only
  when `approve --from` is run again. A copy naming its source kept the source's approval from being cancelled or
  deleted with its renders.
- **Made by:** `0054`, `0103`, `0111`, `0112`.

### D50 · The last render takes its approval, and a flow holds only its own files

**Deleting an approval's last render deletes that approval, its prompt, its failure records, in its render group too,
and its source copy, every older approval with no render — a group of failure records alone is none — and the
newest's waiting draft; nothing goes back to a draft. A flow left with no approval keeps only its directory, its
assignment: its sheets go too, and so does its own copy of each kind of the photograph's description that `photo/`
holds, every numbered list of it, so an own caption older than the newest, which `isekai migrate` never copied, is
lost; `photo/`'s stay (D17). No file of one flow names a file of another. Deleting a render also deletes every edit of its seed, and their chain
([D51](#d51--an-edit-is-one-flat-directory-pinned-by-its-digest)).**

- **Why:** the operator deletes a render to be rid of it; an approval, a draft or a sheet left behind kept the Hub and
  Review offering what was deleted, and a reference into another flow breaks when that flow's work goes, and a
  failure record or a flow's own description left behind kept its folder from emptying.
- **Made by:** `0111`, `0112`, `0114`, `0119`.

### D51 · An edit is one flat directory, pinned by its digest

**An edit is one flat directory under `edits/` — `edit.json` and `graph.json` — named `<what>-<base>`, and a test
holds its digest against a pin and a recorded entry as it does a flow's. An edit's image is written beside its
source, in the render's group, as `<seed>.edit-<k>.png`; no edit is a flow, and no run-level directory holds one.**

- **Why:** a flow takes one photograph and gates on a sheet, and an edit takes a finished render and a composite.
  `Run.flows` reads every run-level directory as a flow, so an edit kept there would be read as one; the group
  already holds a render's files, and the next free `k` chains edits.
- **Made by:** `0119`.

### D52 · The tattoo library is kept whole until a tattoo is removed

**An upload is a folder `.tattoos/<name>/` of the library, outside every collection: `design.png` upright with no
metadata and at most `long_side` of `config/tattoo.json` on its long side, `tattoo.json` and `outline.json`. A cut is a
tattoo with no `design.png`, whose record names the run digest of the photograph it is cut from and whose size is that
photograph's; it is the folder `.tattoos/.cuts/<digest>/<name>/` and serves only that photograph's renders. A name is
one tattoo on a render: it is found by the render's digest, an upload refuses a name any cut holds, and a cut refuses
an upload's name and a cut of its own photograph's. A tattoo is removed by `DELETE /api/tattoos/{name}`, and no route
renames one. A baked edit keeps its own copy of what it was placed with, so a removal changes no edit. The photograph
a cut is taken from, and every tattoo, stays on this machine.**

- **Why:** one tattoo is an input for many renders in many collections, so a folder in a collection would copy it. The
  ink of a cut is already in the photograph's pixels, so copying the photograph would only keep a likeness twice. A
  cut carries its photograph's light and angle, so it is kept by that photograph and no other render lists it. A test
  cut and a tattoo kept by mistake must be able to go, and nothing reads the library back once an edit is baked, so
  removal costs no edit; the name a removal frees can be kept again.
- **Made by:** `0121`, `0126`.

### D53 · A placement is recorded beside its edit

**A bake is recorded as `<seed>.edit-<k>.placement.json` beside its edit's record, written by the edit stage with the
composite and never an image: the tattoo, the mode, the image it is placed on, the outline and tone, a copy of the
stage-1 pairs it used, its own pairs, the limb and the exclusions. A tattoo's stage-1 pairs are the tattoo's, kept per
photograph in `.tattoos/<name>/stage1/<digest>.json` as the page sends them; the stage-2 or direct pairs, the limb and
the exclusions are held by the page until the bake writes them.**

- **Why:** a bake is a request the render session fulfils, so its record sits where the edit's does and goes with it.
  Stage 1 depends on the tattoo and the photograph and not on the render, so a second render of one photograph
  needs only its own stage; the record's copy keeps it whole when those pairs change later. A draft file for the
  held work is a later change, when losing it on a leave is missed.
- **Made by:** `0122`.

### D54 · Automatic pairs run on the operator's machine and are kept nowhere

**The pairs stage 2 proposes are found by DWPose and SAM 2.1 on the operator's machine, in the server's process, over files
pinned in `config/placement.json` and fetched by `make setup`; each file is digest-verified before a session opens, and a
proposal is an answer to one request, never a stage, an artifact or a file. The operator accepts or corrects it, and a
placement records only the pairs the operator holds ([D53](#d53--a-placement-is-recorded-beside-its-edit)).**

- **Why:** a proposal is a guess the operator reads before forward, so it is no run's output and nothing in a
  run directory could hold it truthfully. The models are the tagger's precedent
  ([D7](#d7--wd14-is-one-artifact-in-two-files)): the gate never fetches, a missing file refuses by naming
  its fetch, and the entry point loads no package for them
  ([D20](#d20--the-entry-point-loads-no-third-party-package)). The pod image takes no part.
- **Made by:** `0123`.

### D44 · A flat flow is summon with the face chain ending early

**`summon-flat-anime-wai` is `summon-anime-wai`'s directory with InstantID ending at 0.65 of the steps, a lower
`ip_weight`, and `flat color, cel shading, anime coloring, colorful` in its trailer and `realistic, photorealistic,
3d, semi-realistic` in its negative, held equal to it otherwise by a test; `config/ui.json` offers it in the app.**

- **Why:** the face is set in the early steps and the style in the late ones, so ending the face chain early
  keeps the person and frees the look from InstantID's photographic shading. The cohort count cannot judge it:
  its photo-trained encoder does not read flat faces, so the flow was chosen by eye.
- **Made by:** `0084`, `0090`.

### D46 · A semireal and a vivid flow are flat's face chain in other looks

**`summon-semireal-anime-wai` is flat's directory with summon's whole prompt, and `summon-vivid-anime-wai` is flat's
directory with summon's trailer and `realistic, photorealistic, 3d, semi-realistic, monochrome, greyscale, muted
color` in its negative; a test holds each equal to summon but for that style, and `config/ui.json` offers both.**

- **Why:** flat kept the person but lost colour, and the prompt was the cause, not `lineart` or the early end of the
  face chain. Each look was chosen by eye on the operator's photographs, as flat was, because the cohort count
  cannot judge a stylised face.
- **Made by:** `0090`.

## Runs

### D16 · A run is keyed by the photograph's bytes

**A run's id is a prefix of the photograph's digest plus a readable slug. Opening the same photograph
again resumes the same run.**

- **Why:** the photograph is the one thing every flow shares, and its bytes are what identify it. A
  renamed file is the same run; a re-exported one is not.
- **Made by:** `0013`, `0016`.

### D17 · Input above, flow below

**`runs/<input>/photo/` holds the photograph's caption and tag lists, read by every flow;
`runs/<input>/<flow>/<stage>/` holds each flow's own work.**

- **Why:** one briefing, one model and one pinned tagger read a photograph alike, so its description is
  written once; a flow still adds one subtree, and reads another's work only when the operator names it
  ([D49](#d49--a-control-flow-is-its-subject-with-the-face-chain-at-zero-copied-once)).
- **Made by:** `0016`, `0103`.

### D18 · Runs stay out of what git tracks

**Everything a run produces lives in its runs root — `.data/runs` by default, which git ignores. A runs
root inside the repository must sit under `.data/`; one outside it may sit anywhere. The library
`isekai ui` serves, `ISEKAI_LIBRARY`, is held to the same rule, and so is each collection's `runs/` in it.**

- **Why:** a run holds a copy of the photograph, so a person's likeness is in it by construction.
  Anywhere else inside the repository, those files would be one `git add` from being published.
- **Made by:** `0014`, `0018`, `0061`.

### D32 · A run file's version moves only when an old file could be misread

**A key that only records is added under the kind's current version, as optional. A key whose meaning
changes is a new key.** A version moves only when a file written before the change could be misread by a
reader after it.

- **Why:** moving a version makes every existing file of that kind unreadable, so a run in progress could
  not resume. A record key cannot be misread by its absence; a changed meaning can, which is why the
  render's `sheet` replaced `sheet_version` rather than redefining it.
- **Made by:** `0033`.

### D40 · A collection is a library folder holding `sources/`

**A folder in the library is a collection when it holds `sources/`; its runs root is `runs/` beside it. No
file records a collection, and a dot-folder is never listed; `.tattoos/` is a dot-folder of the library,
never a collection
([D52](#d52--the-tattoo-library-is-kept-whole-until-a-tattoo-is-removed)). Every figure the UI shows of a
collection — its counts, each cell's stage — is a listing read on each request. A batch is not a folder: it is the
photographs one GPU session renders.**

- **Why:** layout alone decides, so no marker file can disagree with the disk, and a stage is a
  directory listing already. The operator never types a path: the collection is in the URL. *Batch*
  names the set a session renders, so the folder needs a word of its own.
- **Made by:** `0061`, `0082`.

### D43 · A source holds pixels and orientation only

**Import writes into `sources/` a JPEG or PNG carrying its pixels and its orientation, and nothing else:
no location, camera or time, its colour in sRGB.** Each file is verified by the strip's own walk before
it is committed; one that cannot be cleaned is left out unless the operator imports it as it is, and the
hub marks it. A tattoo is cleaned as a source is, and bounded to its long side
([D52](#d52--the-tattoo-library-is-kept-whole-until-a-tattoo-is-removed)).

- **Why:** a library holds personal photographs, and every run copies its source, so metadata kept at
  import is metadata kept everywhere. A profile dropped without conversion shifts every colour.
- **Made by:** `0062`.

## Code and environment

### D19 · One place builds the components

**`wiring.py` builds the components, and the CLI and the UI both use it; the UI builds one collection's
wiring through `wiring_from` on every request inside it. `ISEKAI_WIRING` is the one way past the real
components, and it still passes the runs-root check ([D41](#d41--the-test-seam-is-a-factory-named-in-the-environment)).**

- **Why:** the runs-root check ([D18](#d18--runs-stay-out-of-what-git-tracks)) and the choice of
  reader, tagger and transport happen in one place, so neither front end can skip them.
- **Made by:** `0015`, `0018`, `0061`.

### D20 · The entry point loads no third-party package

**The entry point loads no third-party package at module scope; a package is imported inside the verb
that needs it.**

- **Why:** `show` and the other free verbs work on a checkout that has installed none of the models.
- **Made by:** `0025`.

### D21 · Retries follow what can fail

**A stage that calls a local model may retry a dropped call. A deterministic stage gets one attempt, and
so does the paid render.** The numbers are `run.py`'s `BUDGETS`.

- **Why:** a deterministic stage fails the same way twice, while a call to the local model server can
  drop and succeed on the next attempt. The paid stage is never retried on its own.
- **Made by:** `0013`, `0023`.

### D22 · Dependencies are declared and pinned

**Runtime dependencies are declared and pinned exactly. There is no optional extra: the evaluator adds no
package to the runtime list, and one it ever needs goes into an `[eval]` extra, never into the pipeline's.**

- **Why:** an optional extra that the gate's `uv sync` is not told about gets uninstalled — the tagger
  disappeared on every gate run. The pins decide what a second machine installs.
- **Made by:** `0025`, `0053`.

### D23 · System dependencies refuse rather than being assumed

**Ollama and node are system dependencies. A missing one refuses, naming what installs it.**

- **Why:** `uv sync` cannot install either, so the refusal must name the command that does.
- **Made by:** `0018`, `0019`.

### D24 · The review UI serves only this machine

**The UI serves only on the local loopback address, and checks `Host` and `Origin` on every request.
A request with no `Origin` is answered only when `Sec-Fetch-Site` is `same-origin` or `none`, or absent
as it is from a client that is not a browser.**

- **Why:** the page shows personal photographs and writes approvals. Nothing off the machine, and no
  other site open in the browser, may reach it. A browser marks every request with `Sec-Fetch-Site`, so
  an image tag on another site, which sends no `Origin`, is still refused.
- **Made by:** `0018`, `0023`, `0061`.

### D25 · Shortcuts match the physical key

**A shortcut is matched on `event.code` and declared once, in the key store:
a plain letter moves, a command is `⇧` + a letter, or `⇧⌫`, the large view's Delete, which asks first, a plain
letter only where nothing is typed, and Mod — `⌘` on macOS, `Ctrl` elsewhere — where a command must reach into a
text field. Inside a text field only `Esc`,
`Mod+↵`, `Mod+Z`, `⇧Mod+Z`, `Mod+K`, `⌃/` and `⌃;` run, Review's `⌃P`, on macOS Review's `⌃H` `⌃L`,
which alone move between its panes, and `⌃J` `⌃K`, which move between its fields, and in ④'s seed slots
`slot-down` and `slot-up`, `j` `k` `↓` `↑`, which move between the slots.**

- **Why:** a key typed into a field is text. Option types characters on macOS and is the window
  manager's on Linux, and a layout moves letters but not keys. One declaration is what the hints and
  the key list read, so they cannot disagree with the keys. On macOS `⌃` is free of the window manager
  and of `⌘`'s shortcuts, but a text field's `⌃H` deletes backward, and Review's fields give that key up
  to the pair; elsewhere the pair is not offered, so a wrong platform guess only hides it. A seed slot takes
  digits alone, so its letters are free to move. `⌫` is the key a delete is pressed on, and the dialog's *No*
  first keeps it two keys and a choice.
- **Made by:** `0021`, `0069`, `0076`, `0078`, `0091`, `0106`.

### D41 · The test seam is a factory named in the environment

**`ISEKAI_WIRING=<module>:<factory>` replaces the components `wiring_from` builds, after its runs-root
check, and is imported then and only then. The suite's doubles stay in `tests/`; the browser tests name
`tests.e2e.wiring:fake`.**

- **Why:** the browser tests drive the real server in its own process, where no fake can be passed as
  a parameter, and CI has no vocabulary, models or GPU. Naming the factory keeps production from
  importing `tests/`, and the import inside the function keeps the entry point's graph unchanged
  ([D20](#d20--the-entry-point-loads-no-third-party-package)).
- **Made by:** `0061`.

### D47 · A change is measured from isekai's own catalogue

**`metrics/catalogue.toml` names what a change is measured by. Each measure is a stdlib script under
`scripts/metrics/` that prints one number, or a value the station passes. The build drafts the values and the
release commits them to `metrics/changes/<change-id>.json`; a measure that fails is recorded unavailable and
halts nothing.**

- **Why:** the gate says whether isekai works, not where it is heading. A version that moves tests between the
  gate and the browser run is read as numbers. The scripts count isekai's own tree and sit outside `tools/`, whose
  guards they do not need.
- **Made by:** `0092`.

### D48 · A theme is a token set, chosen in the browser

**A theme sets every colour token the app and the sheet declare, in `ui/src/themes.css`, and nothing else; Nocturne,
the vendored sheet's own, is the default. `⇧T` chooses one, and the browser keeps the choice in `localStorage` under
`isekai.theme`, applied by `ui/index.html`'s head script before the first paint.**

- **Why:** a look is the person's, not the library's, so no API or file holds it. A token set means no screen carries a
  rule of its own for a theme, and a test reads every value.
- **Accepts:** the choice is per browser and per origin, so the UI served on another `--port` opens on Nocturne. Reopen
  when the UI is served from more than one origin.
- **Made by:** `0098`, `0109`.

### D55 · A stage may be a package

**A stage is the first segment under `isekai.pipeline`: one module, or one package whose `__init__.py` is its front door. The modules of a stage import each other; no stage imports another, its front door included.**

- **Why:** the layer guard read a stage as any file under `pipeline/`, so a stage that grew past one file would have tripped it on its own modules, and its private maths went down into `shared/` instead.
- **Made by:** `0129`.

### D56 · Size and patches are held by ratchets

**`tests/test_ratchets.py` holds a ceiling for the lines of a file under `isekai/`, the lines of a function, a function's positional parameters, the lines of a file under `ui/src/` and the patches of a module's own names. An offender past its ceiling is a listed row of its table; one unlisted is red, and a row whose offender no longer offends is red until it is removed. A listed offender may grow; a row is removed by the version that removes the offender, and none is added.**

- **Why:** the gate held no rule of size or shape, so the largest files and the most-patched modules grew with every feature. A ceiling on the unlisted stops a new one; leaving a listed offender free to grow keeps the next route or screen from halting on a refactor that is queued and not yet built.
- **Accepts:** a listed offender grows unchecked until its row goes. Reopen when a refactor version leaves a row standing past its work.
- **Made by:** `0129`.

## Infrastructure

### D26 · Renders run on a rented GPU

**A RunPod pod runs this project's own ComfyUI image, with PyTorch built for CUDA 12.8. A session's limit
and price are its quote's, at most `gpunit.toml`'s `ceiling` and `max_hourly`**: the limit is the work's
estimate from recorded durations, each image at no less than `config/render.json`'s `per_image_s`, never
below the provisioning hold plus five minutes, and gpunit refuses a card dearer than `max_hourly`. Each
render records the device it ran on.

- **Why:** the render is the only work that needs a GPU, and renting by the second costs less than owning
  one. The Blackwell GPU has no kernels in older CUDA builds. A fixed limit caps a batch at what fits in it;
  a limit from the work fits the work, and a price at the hourly maximum is a bound rather than a guess.
  A median recorded on a fast card says nothing of a slow one, and gpunit takes whichever card is in
  stock, so the figure per image is the slowest card's.
- **Made by:** the founding setup, `0063`, `0107`.

### D27 · The models live on a network volume

**The volume holds exactly the manifest. A pod refuses to start when what is mounted is below the
capacity floor** — the floor is `pod_start.py`'s. A network volume reports its storage cluster's capacity,
far above the floor, so the floor tells it from the pod's own disks; it does not measure the volume's
quota, and a 20 GB volume passes. **The volume lives for a working window**: `gpunit volume up` makes it
from `gpunit.toml`'s `volume_gb` and `volume_ceiling`, in a data centre chosen from stock, and each pod of the
window runs there; `gpunit volume down` deletes it. The ceiling is not a teardown: past it, the volume bills
until gpunit's next session, `up`, `status`, `down`, `volume up` or `volume down` sweeps it, if that delete
succeeds. Nothing checks the volume's size before the create;
the pod's floor is the size check.

- **Why:** re-downloading every session costs more than a window's rent, the weights download once a window,
  and no storage bills once a window is closed. A volume filled only from the manifest is clean by construction. A missing mount would fall through to the container disk: it would
  render, bill, and lose everything at teardown. A volume cannot move between data centres, so a pod
  elsewhere boots without its models.
- **Accepts:** a pin freezes bytes, not intent: most weights come only from third-party mirrors,
  trusted as the publisher's. Reopen when a publisher ships a first-party copy, or a mirror is compromised.
- **Made by:** `0009`, `0011`, `0033`, `0041`, `0052`, `0058`, `0060`.

### D28 · The image carries code, the volume carries weights

**The image lives on GHCR with no weights baked in, is built only on request, and is pinned by digest in
`gpunit.toml`, with `config/image.json` recording the same digest and the files it was built from. A pod
is made only by `isekai render`, through gpunit, and boots that digest and nothing else.** Its base and uv
are named by digest, and its Python environment is the locked uv project under `image/`.

- **Why:** only a gpunit session knows the image, the volume and the session's SSH key, so a pod made any
  other way has no models and no way in. A moving tag is not a pin: every build under one name was a
  different image, and nothing recorded which one a render ran on. Moving the pin is a commit.
- **Made by:** `0010`, `0011`, `0033`, `0058`.

### D34 · Renders stay on a pod

**A rented pod renders, reached through an SSH tunnel; serverless endpoints are declined.**

- **Why:** serverless adds places a photograph can linger — the provider's job store, boot snapshots whose
  contents are undocumented, a gateway that decrypts in transit. The pod has one tunnel and nothing
  between.
- **Made by:** `0041`.

### D35 · The pod's operator is a trust boundary, accepted knowingly

**Whoever runs the machine can read its memory while a render runs, so the photograph is not encrypted:
the key would sit in the same memory.**

- **Why:** no program can hide memory from its host, and the provider offers no confidential computing.
  Only rendering locally removes the boundary.
- **Accepts:** gpunit's boot script holds the stop key, and ComfyUI runs without it; code ComfyUI runs can
  still read it from the boot script's `/proc` entry, since the image names no `USER`. Reopen when a node or
  model is not fully trusted, or the key's scope is account-wide.
- **Accepts:** the host's swap is inside the same boundary: memory it swaps out reaches its disk. The pod's
  start prints whether the container can swap, and holds for neither. Reopen when the provider offers swap off.
- **Made by:** `0041`, `0052`, `0058`, `0059`.

### D36 · A render session is `isekai render`

**It assembles every prompt before any pod exists, opens a gpunit session, waits for the endpoint through its
tunnel, renders, and closes the session on every exit.** With no request it renders what each approval lacks of
its count, in each collection it names, less each `--without`, on one pod, then runs the pending edits of those
collections. Three bounds hold it: the laptop's
watchdog at the session's
limit; the pod's own stop at that limit, armed by gpunit's boot script and never past `gpunit.toml`'s ceiling;
and gpunit, which refuses a session beside a recorded or listed pod of the project and leaves none listed at
teardown. One session runs at a time; the
app's Render runs it as a child, between `gpunit volume up` and `volume down`, with `--progress json`.

- **Why:** the lifecycle is gpunit's, tested as a library; isekai keeps the order of its flows, its free pass
  and its log. A pod the laptop can no longer reach must still stop, so the pod stops itself.
- **Accepts:** ComfyUI's history and node cache hold every photograph the session renders,
  from every collection, until the teardown.
- **Accepts:** gpunit's signal handlers replace isekai's while the session is open, so isekai sets none.
  Reopen when isekai needs a handler of its own.
- **Refusals:** `isekai render` exits with gpunit's code, 1, 4 or 5, and the drawer names a 4 or a 5 by its kind and
  quotes gpunit's `refused:` line, a form gpunit documents for callers to parse.
- **Made by:** `0035`, `0043`, `0044`, `0052`, `0058`, `0063`, `0083`, `0097`, `0108`, `0119`.
