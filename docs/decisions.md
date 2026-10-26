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
  neither holds it, and bundling it would make every version a research version.
- **Made by:** the project's founding decision.

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
own artifacts, and each tagger's refusal is collected on its own.**

- **Why:** the sheet reads WD14's tags, so its input must not wait on Ollama. `tag` is the sheet's input
  and `caption` is the reviewer's aid, and neither needs the other.
- **`--new-version`** re-produces only what its own verb writes.
- **Made by:** `0020`, `0032`.

### D2 · A table fills the sheet

**The sheet is filled from WD14's tags by one authored table, `config/field_map.json`, read from tag to
field. No model decides a sheet.**

- **Why:** WD14's tags are all in the vocabulary, because its label file *is* the vocabulary, and a table
  cannot invent a tag. The router placed 73% of the tags offered, and 90% of those survived review.
- **Made by:** `0021`.

### D3 · The hand path stays

**`review` and `approve` stay working verbs.** The review UI is the guided path; the hand path stays.

- **Why:** deleting it would make stage ③ a single point of failure for the whole pipeline.
- **Made by:** `0018`.

### D4 · The UI runs stages only as the CLI's children

**The browser runs a stage only as the CLI's own verb, a child of the server; the one act in it that
spends is Render's confirmation, after its quote.** Prepare is `tag`, `caption` and `sheet` run as
children, and Render is `render` between gpunit's `volume up` and `volume down`. Every other write goes
through the function that owns it: a draft, its edits and an approval through `review`'s, a tick through
the run's `assign`, a source through import.

- **Why:** the CLI is the one path, so a stage the page starts is exactly the stage the terminal runs,
  and a write no stage owns would give a run file a second author. Spend behind a web page is bounded by
  what the operator read: the confirmation carries the quote it showed, and a quote grown since is
  refused. The quote compares image total and limit, not source or approval identity.
- **Made by:** `0018`, `0061`, `0062`, `0063`.

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

**Ollama is reached over plain HTTP at a fixed local address, never through a proxy, and the model a flow
names is checked against `config/reader.json` before its first call.** The address is a constant, with no
flag and no environment variable. The call uses Ollama's own `/api/generate`, which carries the sampling
options the OpenAI-compatible endpoint cannot. Ollama's own record of the model must name the model and
projector files the manifest pins, or the call is refused and spends no attempt.
The ComfyUI transport ignores the environment's proxy the same way.

- **Why:** a photograph's destination must not be changeable by accident — an exported `http_proxy`
  once sent every photograph off the machine. An alias is a name the runtime resolves, and the files
  behind it shape the prose, so a caption can claim a pin only once those files are checked.
- **Accepts:** whatever holds port 11434 receives the photograph; nothing probes that it is Ollama.
  Reopen when a listener that is not Ollama is seen there, or the address stops being loopback-only.
- **Made by:** `0019`, `0033`, `0037`, `0052`.

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

## Flows

### D14 · A flow is one flat directory

**A flow is one flat directory of named files — `flow.json`, `graph.json`, `schema.json`,
`caption.briefing.md` — and it shares nothing with another flow.**

- **Why:** the pin covers only the files directly in the directory, so a nested file would escape the
  freeze. Sharing nothing means a change to one flow can never change another.
- **Made by:** `0016`, `0022`.

### D15 · A flow is named for what it is

**A flow's identifier is `<verb>-<style>-<base>`, with `-v2` added only for a second generation of the
same combination.**

- **Why:** the base is in the name because other bases are candidates. A name describing the
  implementation behind a flow, rather than the flow, stops meaning anything when that implementation
  changes.
- **Made by:** `0022`.

### D31 · A flow declares whether it is tagged

**`flow.json` declares `"tagger": true | false`, and the sheet reads the declaration.** `tag` refuses a
flow that declares `false`; `sheet` fills such a flow's sheet with every field empty, for a person to fill.

- **Why:** flows that need no tag list are coming. A boolean, not a list of taggers: `tag` runs both
  together, so a list would declare a choice no flow makes.
- **Made by:** `0032`.

### D38 · A control flow is its subject with the face chain at zero

**`control-anime-wai` is `summon-anime-wai`'s directory with `ip_weight` and `identity_cn_strength` at 0, held
equal to it by a test; its approval is copied from `summon`'s and its renders take `summon`'s seeds, each
recording the source. A stage reads another flow only when the operator names it as a source.**

- **Why:** the count's floor is the same sheet and the same noise with the face mechanism off; the comparison
  is sound only while the two differ in exactly that. D17 forbids a flow reaching into another on its own, and
  an operator's named source is not that.
- **Made by:** `0054`.

## Runs

### D16 · A run is keyed by the photograph's bytes

**A run's id is a prefix of the photograph's digest plus a readable slug. Opening the same photograph
again resumes the same run.**

- **Why:** the photograph is the one thing every flow shares, and its bytes are what identify it. A
  renamed file is the same run; a re-exported one is not.
- **Made by:** `0013`, `0016`.

### D17 · Input above, flow below

**`runs/<input>/<flow>/<stage>/`.**

- **Why:** adding a flow adds one subtree, and no flow reads another's artifacts unless the operator names
  it as a source ([D38](#d38--a-control-flow-is-its-subject-with-the-face-chain-at-zero)).
- **Made by:** `0016`.

### D18 · Runs stay out of what git tracks

**Everything a run produces lives in its runs root — `.data/runs` by default, which git ignores. A runs
root inside the repository must sit under `.data/`; one outside it may sit anywhere. The library
`isekai ui` serves, `ISEKAI_LIBRARY`, is held to the same rule, and so is each batch's `runs/` in it.**

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

### D40 · A batch is a library folder holding `sources/`

**A folder in the library is a batch when it holds `sources/`; its runs root is `runs/` beside it. No
file records a batch, and a dot-folder is never listed. Every figure the UI shows of a batch — its
counts, each cell's stage — is a listing read on each request.**

- **Why:** layout alone decides, so no marker file can disagree with the disk, and a stage is a
  directory listing already. The operator never types a path: the batch is in the URL.
- **Made by:** `0061`.

### D43 · A source holds pixels and orientation only

**Import writes into `sources/` a JPEG or PNG carrying its pixels and its orientation, and nothing else:
no location, camera or time, its colour in sRGB.** Each file is verified by the strip's own walk before
it is committed; one that cannot be cleaned is left out unless the operator imports it as it is, and the
hub marks it.

- **Why:** a library holds personal photographs, and every run copies its source, so metadata kept at
  import is metadata kept everywhere. A profile dropped without conversion shifts every colour.
- **Made by:** `0062`.

## Code and environment

### D19 · One place builds the components

**`wiring.py` builds the components, and the CLI and the UI both use it; the UI builds one batch's
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

**A shortcut is matched on `event.code` and declared once, in the key store: `⇧`+letter for a command,
always for one that writes, a plain letter only where nothing is typed, and Mod — `⌘` on macOS, `Ctrl`
elsewhere — where a command must reach into a text field. Inside a text field only `Esc`, `Mod+↵`, `Mod+Z`,
`⇧Mod+Z`, `Mod+K`, `⌃/` and `⌃;` run, Review's `⌃P`, and on macOS Review's `⌃H` `⌃L`, which move between its panes,
and `⌃J` `⌃K`, which move between its fields.**

- **Why:** a key typed into a field is text. Option types characters on macOS and is the window
  manager's on Linux, and a layout moves letters but not keys. One declaration is what the hints and
  the key list read, so they cannot disagree with the keys. On macOS `⌃` is free of the window manager
  and of `⌘`'s shortcuts, but a text field's `⌃H` deletes backward, and Review's fields give that key up
  to the pair; elsewhere the pair is not offered, so a wrong platform guess only hides it.
- **Made by:** `0021`, `0069`, `0076`, `0078`.

### D41 · The test seam is a factory named in the environment

**`ISEKAI_WIRING=<module>:<factory>` replaces the components `wiring_from` builds, after its runs-root
check, and is imported then and only then. The suite's doubles stay in `tests/`; the browser tests name
`tests.e2e.wiring:fake`.**

- **Why:** the browser tests drive the real server in its own process, where no fake can be passed as
  a parameter, and CI has no vocabulary, models or GPU. Naming the factory keeps production from
  importing `tests/`, and the import inside the function keeps the entry point's graph unchanged
  ([D20](#d20--the-entry-point-loads-no-third-party-package)).
- **Made by:** `0061`.

## Infrastructure

### D26 · Renders run on a rented GPU

**A RunPod pod runs this project's own ComfyUI image, with PyTorch built for CUDA 12.8. A session's limit
and price are its quote's, at most `gpunit.toml`'s `ceiling` and `max_hourly`**: the limit is the work's
estimate from recorded durations, never below the provisioning hold plus five minutes, and gpunit refuses a
card dearer than `max_hourly`.

- **Why:** the render is the only work that needs a GPU, and renting by the second costs less than owning
  one. The Blackwell GPU has no kernels in older CUDA builds. A fixed limit caps a batch at what fits in it;
  a limit from the work fits the work, and a price at the hourly maximum is a bound rather than a guess.
- **Made by:** the founding setup, `0063`.

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
its count. Three bounds hold it: the laptop's watchdog at the session's limit; the pod's own stop at that limit,
armed by gpunit's boot script and never past `gpunit.toml`'s ceiling; and gpunit, which refuses a session beside
a recorded or listed pod of the project and leaves none listed at teardown. One session runs at a time; the
app's Render runs it as a child, between `gpunit volume up` and `volume down`, with `--progress json`.

- **Why:** the lifecycle is gpunit's, tested as a library; isekai keeps the order of its flows, its free pass
  and its log. A pod the laptop can no longer reach must still stop, so the pod stops itself.
- **Accepts:** ComfyUI's history and node cache hold the batch's photograph until the teardown.
  Reopen when a pod serves more than one batch.
- **Accepts:** gpunit's signal handlers replace isekai's while the session is open, so isekai sets none.
  Reopen when isekai needs a handler of its own.
- **Made by:** `0035`, `0043`, `0044`, `0052`, `0058`, `0063`.
