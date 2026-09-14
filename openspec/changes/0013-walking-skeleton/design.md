# Design — the walking skeleton

**Verdict: `feasible-with-caveats`.** The four boundaries can be crossed in one version on one flow.
Two caveats are recorded below and neither blocks: the reading and sorting stages depend on a hosted
CLI that cannot be pinned to a revision, and the sorting stage's measured score for the configuration
this version actually ships is **0.537** — below the 0.575 it is modelled on, above the 0.482 open
alternative, and measured with a known defect that the shipped version will not carry.

## Context

See `proposal.md` — *Why*. What matters for the approach:

- **The runtime is stdlib-only.** `pyproject.toml` declares `dependencies = []`, and a subprocess test
  imports the entry point with no site-packages on the path. Anything the pipeline needs must be in the
  standard library or must not be an import.
- **The existing path is not to be touched.** `convert.py`, `isekai/cli.py` and the graph they drive
  stay exactly as they are for the whole of this version. That is a deliberate deviation from the
  one-path rule, scoped to this version; the deletion is v0.14's, after the replacement is proved.
- **The suite runs offline and deterministically.** No test reaches a GPU or the network; the ComfyUI
  transport is behind a Protocol with a fake, and randomness takes an injected source. Every new seam
  has to fit that or the gate stops being runnable.
- **Sixty criteria sheets exist, on a branch that never merges.** Nothing is promoted as code. The
  field list, the mapping rules and the dial values below are restated here because they were measured,
  not because they are inherited.

## Goals / Non-Goals

**Goals**

- Cross each of the four boundaries once, on one flow, while each is still thin. A boundary nothing has
  been passed through is a boundary by assertion.
- Make "where are we" answerable from a directory listing after a crash, a closed laptop or a week.
- Make the machine's sheet structurally unable to be edited, so the correction step has a baseline to
  be measured against later.
- Leave the existing render path working, unchanged, and reachable.

**Non-Goals**

- **No session lifecycle.** This version's rendering talks to an already-reachable endpoint, as the
  prototype did by hand. Acquiring, tunnelling, releasing and reconciling orphaned machines land
  together with the version that adds a second flow, rather than being dragged into the version whose
  only risk is the architecture.
- **No second implementation of anything.** One reader, one sorter, one flow. A selector over one entry
  is a dispatch mechanism with nothing to dispatch.
- **No schema migration.** Only one schema version exists, so a migration ladder would be empty.
- **No progress file.** Nothing but a human is watching before the review UI exists, and the inspection
  command is what a human reads.
- **No evaluation.** It needs optional heavy dependencies, and its unit is a cohort rather than a run.

## Decisions

### D1 · The new surface is a new module, not an extension of the existing parser

`convert.py` is a shim over `isekai/cli.py`, and the stdlib guard imports it. Adding subcommands to
that parser would edit the entry path the existing flow depends on. So the pipeline lives in
`isekai/__main__.py`, invoked as `python -m isekai <verb>`, with its own parser.

*Alternatives.* Keeping the existing shim and adding verbs to it — rejected, it is the one file this
version promised not to touch. Four separate scripts — rejected, it multiplies the stdlib guard by four
and gives argument parsing four places to drift. A console entry point — rejected, it adds an
installed-versus-source ambiguity for nothing.

**Consequence worth stating: the stdlib guard does not move, it is joined.** The existing test still
imports `convert`; a second one imports the new entry point, and the falsifiability twin that proves
the mechanism actually refuses a third-party import is unchanged and covers both.

### D2 · Six verbs, and schema migration is not one of them

`caption · sheet · review · approve · generate · show`.

Migration was considered for this version and moved out. Only schema version 1 exists, so the upgrade
ladder would be a dispatch table with no entries, and the refusal that would name the command is
unreachable — nothing can write a version 2 artifact. The command belongs to the version that
introduces the second schema version. What does ship now is the `schema` field on every artifact and
the refusal on an unknown version, because deciding those later would mean running a migration in order
to enable migrations.

### D3 · The correction stage gets its own directory

`sheets/<flow>/` is written once by the sorting stage and read-only to everything else.
`review/<flow>/` is the only mutable directory in a run.

The alternative — both stages writing into one directory, told apart by number — makes "the machine's
sheet is never edited" a convention that an editor, a script or a careless command can break silently
and permanently. Separating them makes it a property of the layout. It also cleans up the boundary
claim: each stage is handed a path into its own directory, so no stage is in a position to read
another's output at all.

**It changes how the correction's value gets measured, and for the better.** The machine's draft is
never approved, so rendering it is now an explicit act — approve it unedited, then edit and approve
again, and render both. That is more honest than the accident, and it lets the approved artifact record
whether anything actually changed, which turns "was this reviewed" into a fact on disk.

### D4 · Numbering is per directory, linked by provenance

Each stage numbers within its own directory; the link between them is the producer record, which names
the version it came from. `caption 001 → sheet 001 → review 001`, and prompts, outputs and evaluations
inherit the review artifact's number because only an approved artifact is ever rendered.

*Alternative.* One number space shared across the sheet and review directories, so that a single
integer identifies a flow's state — rejected because computing "the next number" would have to read two
directories, coupling exactly the seam D3 exists to open. The chain already worked this way between the
caption and the sheet; this adds one more link of the same kind.

### D5 · A filename carries version and approval — and an error's kind and attempt

A filename earns a field exactly when resume must decide on it without opening the file. That is true
of the version number, of approval, and — because retry budgets are a resume decision — of an error's
kind and its attempt ordinal.

**An error record is a sibling of the artifact it failed to produce, not a consumer of its number.**
The scheme it replaces said a retry writes the next number. That breaks at the two stages that take
their number from an upstream artifact rather than counting their own: there is no next number to
advance to. So `001.error.1.transient.json` sits beside where `001.json` would have gone, the budget
check is a glob, and a permanent record short-circuits it.

Everything else — the model, the instruction digest, the revision, the source version — lives inside
the artifact. Encoding the producer in the filename was considered and rejected: a name cannot express
a pinned revision, so it would be a lossy duplicate of the authoritative record, and the dangerous kind,
because two files with the same name could be different models and people would trust the name.

### D6 · Reading and sorting go through the `claude` CLI, and the invocation is locked down

The runtime cannot take an SDK — `dependencies = []` — so the choice was raw HTTP to an API, or the
CLI. The CLI was chosen for this version because it needs no key handling and no per-token budget, and
because it is closer to what was actually measured: the reading score this design is built on came from
an agent session with tools, not from a bare completion call.

Three things in the invocation are load-bearing:

- **`--safe-mode`.** By default the CLI discovers a `CLAUDE.md` from the working directory. Run from
  this repository, the reading stage would get sixteen kilobytes about this repository injected into the
  context that is supposed to describe a photograph. `--safe-mode` disables that and every other
  customisation while leaving authentication, model selection and the built-in tools working. The
  minimal-mode flag was rejected: it forces API-key authentication and defeats the point.
- **`--tools Read` at the reading stage, `--tools ""` at the sorting stage.** The reader needs to open
  the photograph. The sorter needs nothing, and a stage that can run shell commands is not a stage.
- **`--permission-prompts none`.** Without it a misconfigured stage can wait for a human forever.

Output is always the JSON envelope, never plain text — the envelope is what carries the error status,
the stop reason and which models actually ran. The sorting stage additionally passes the schema's field
structure, which constrains the *shape* of the answer and not its wording.

**Failure classification comes from the envelope**, measured rather than assumed: a rate limit, a
server error or a timeout is transient; any other error status, a declined request, a denied permission
or a response that does not match the required structure is permanent.

**No fallback model.** A fallback would render the artifact on a different model than the one asked
for, and the whole provenance discipline is that the record names what actually produced it.

### D7 · The producer records what ran, the instructions, and honestly declares it is unpinned

A probe of the invocation showed two models in a single envelope — the one requested and a smaller one
doing CLI-internal work — so the record names the models that actually ran rather than the flag that was
passed.

**It records the digest of the instruction text.** This is the variable the evidence says matters most:
one change to a reader's instructions — telling it never to leave a field blank — produced nineteen
invented identity marks across seven of ten subjects and moved its score from 0.518 to 0.307. An
artifact whose provenance names the model but not the instructions cannot explain its own result.

**It declares `pinned: false`.** The standing rule is that every model is pinned to a revision and a
digest with no exception for a hosted runtime. A hosted CLI cannot satisfy that: the model identifier is
a moving alias with no revision and no digest. The honest record is a field saying so, rather than a
revision field that would be untrue. This is the same defect the project already has on one hosted
model, and it is a second reason the open, digest-pinned readers at v0.15 restore something real.

### D8 · The schema is a versioned data file, and its field names are identifier-safe

The schema declares, in order, the sixteen fields, which seven are scored, and the per-field suffix
convention. Data rather than code, so it can be checked without executing anything and a second schema
is a file rather than a branch.

**Field names are slugs, not prose.** This is forced, not stylistic: the structured-output flag becomes
a tool input schema at the API, which enforces `^[a-zA-Z0-9_.-]{1,64}$` on property keys, and six of the
sixteen field names carried a space or a slash. The probe hit a hard 400 on the first call. Aliasing at
the boundary was tried and is the *cause* of the one caveat on the measured number below: the model read
one set of names in its instructions and was structurally held to another. One name everywhere removes
the class of error.

```
count · age_band · skin_ancestry · hair_colour · hair_silhouette · eye_colour
eyebrows · marks · clothes · accessories · expression · gaze · pose
framing · body_shape · background
```

Seven are scored: `hair_colour`, `hair_silhouette`, `eye_colour`, `marks`, `clothes`, `gaze`, `pose`.

**The suffix table belongs to the schema, not the mapper.** Expecting a hair-colour field to hold tags
ending in "hair" is a statement about a particular tag list paired with a particular field. Putting it
in the schema and passing it into the mapper is what makes the mapper genuinely independent of field
names — which the current prototype code claims and does not deliver, because its suffix table is keyed
by them.

### D9 · The vocabulary is a provisioned artifact and the mapping over it is code

The tag list — 8,106 canonical tags with their post counts — gets its own pinned, digested manifest.
It is untracked today, produced only as a side effect of downloading an unrelated model, so a fresh
clone cannot fill a sheet at all.

**Two corrections to the entry it is derived from.** It currently resolves a mutable reference, which
the repository's own pinning rule forbids; it must be resolved to an immutable one. And at 308 KB it is
not stored as a large file, so the digest cannot be read from a published record and must be obtained by
fetching and hashing — which is why the shared derivation module has to carry both strategies.

The mapping cascade stays in the repository. The artifact is a tag list; the four-pass cascade over it
is ours, it is tested, and shipping it as data would put a dependency into the guarded import graph.
The deciding question is which outlives which: swap the sorting model and the mapper is still needed;
swap the vocabulary and it is useless.

### D10 · One shared derivation module, three derivers

`scripts/manifest.py` carries the entry types, both digest strategies and the writer. Each deriver
becomes a table of what to pin plus a `derive()`.

The premise this replaces is that the two existing derivers are near-copies. They are not — the second
imports four names from the first, and the decision not to merge them is recorded in the second's own
docstring: merging the manifests would make one file answer two questions. That decision stands, and is
not what this changes. What changes is that the shared names move out of a *script* into a module, which
matters because a third importer makes an accidental structure load-bearing — and because the entry
spec type is currently declared twice, under one name, with two different shapes. A third shape is how
that becomes a defect.

*Alternative.* A third deriver importing from the first, as the second does — rejected on the shape
collision and on the cost of the same edit in three places every time an entry gains a field.

**The refactor is verifiable for nothing:** re-run all three and require the manifests to be
byte-identical, which is already the rule they are held to.

### D11 · P8's watch channel does not ship

The standing item says each manifest entry should record the channel to watch beside the revision it is
pinned to, from this version, on the grounds that adding it later would re-derive every manifest.

**That argument does not survive contact with how the manifests work.** They are generated; re-deriving
them is the normal operation, and adding a field later costs one regenerated file and one commit.
Against that, the field has no reader until the watcher ships, which is parked with no version. The
repository's own rule, written in the very file this would edit, is that a field nothing reads is a
one-entry registry. **The item is deferred, and the reversal is recorded here rather than dropped.**

### D12 · A flow is immutable, named descriptively, and pinned by equality

`flows/summon-v1/`. Changing a dial, a prompt fragment or a negative does not edit this flow; it creates
a new identifier. A tuned dial is not a variant of a flow, it is an untested flow.

An output's path identifies a configuration only if a flow identifier never silently means something
else. A test holds each tracked manifest against a committed digest — the same mechanism the repository
already uses to pin its committed prompts, where changing one is a deliberate test edit. That is what
makes the graph digest already carried in every render's provenance a check rather than a decoration.

**The dials are the measured ones, not the graph file's.** The prototype's committed graph carries a
guidance scale of 7 and an identity control strength of 0.5; every measured run overrode them to 5 and
0.8. A manifest transcribed from the graph would ship a configuration nothing measured.

```
base WAI-illustrious-SDXL v17.0 · EmptyLatent, denoise 1.0 · cfg 5 · 28 steps
euler_ancestral / normal · clip skip −2 · ip_weight 0.9 · identity cn 0.8
openpose 0.6 · hires R-ESRGAN Anime6B ×1.5, 20 steps, denoise 0.35
quality prefix, then the sixteen fields in schema order, then the style trailer
```

### D13 · Seeds: a count draws, explicit seeds reproduce, and the two do not combine

`--count N` draws N seeds from an injected source. `--seed S`, repeatable, renders exactly those. They
are mutually exclusive — one explores, one reproduces, and combining them has no meaning.

The reproducibility contract moves from "one integer reproduces a run's whole sequence" to "the filename
is the seed", which is the same guarantee at a finer grain and a stronger one: it reproduces an image
rather than an ordering. **Explicit seeds earn their place in this version for one concrete reason** —
measuring what the correction is worth means rendering the uncorrected and corrected artifacts and
attributing the difference to the sheet, which only holds if both render at the same seed.

### D14 · Everything a run produces lives under one gitignored root

Run directories are `.data/runs/<photo-id>/`, beside `.data/inputs/` and `.data/outputs/`. One ignored
root, not a top-level directory per kind.

**The reason is not tidiness.** The run directory holds a *copy of the photograph* — that is what makes
a run reconstructable from disk — so `runs/` contains personal photographs by construction. The
repository's standing rule is that no personal photograph is ever committed, and under a top-level
`runs/` that rule depends on one `.gitignore` line staying correct forever. Under a single ignored root
it is structurally true instead: there is nothing generated outside it to get wrong.

**`models/` deliberately stays where it is.** It is a different kind of thing, and the two fail
differently: `.data/` is captured or generated and its loss is the loss of work, while `models/` is
fetched from a pinned manifest and verified, so its loss costs a re-download that is byte-identical by
construction. Moving it would also edit the provisioning policy, the scorer's command-line default and
the pod's namespace conventions — real risk in a version whose only intended risk is the architecture.
The rule is stated in `CLAUDE.md` with that boundary named, so it does not drift into meaning
"everything untracked".

## Risks / Trade-offs

**The sorting stage's shipped configuration scores 0.537, not 0.575.** → Measured, not estimated: five
subjects, the same harness that produced the recorded 0.575 and 0.482 (verified by reproducing both
before the probe), mean recall over the seven scored criteria. It ties the hand-routed incumbent on six
of seven fields; the whole 0.038 gap is `pose`, on two subjects. Three caveats travel with it and are
recorded rather than smoothed: the measure is recall-only and this arm emitted 19% more tags than the
incumbent at the *lowest* precision of the three arms (0.553 against 0.688 and 0.630) — it lost while
emitting more, which is the unflattering reading and the right one; extended thinking was on where the
open alternative's was explicitly off; and the probe ran with the field-name aliasing D8 exists to
remove, so the model read one set of names and was held to another on all five calls. The number is a
floor, not a ceiling, and it is above the open alternative this version is not yet shipping.

**The mapping pass buys this arm nothing measurable.** → Scoring the raw pre-mapping sheets gives the
identical 0.537 and identical per-field figures; it changed four tags out of 130, none of which appeared
in any reference. It still ships, because on this arm it is a *validator* — those four were outside the
vocabulary and it caught all four — and because on the open model at v0.15 the same pass is worth
0.033 → 0.482. Stated plainly so nobody later reads its presence here as evidence it helped.

**Two stages depend on a binary resolved on `PATH`.** → New for this repository: tooling has always
resolved binaries, the runtime never has. Mitigated by a refusal naming what to install, and bounded by
being a version-scoped choice — v0.15's open readers remove it, and an API implementation would be a
third one entering the same seam.

**A fresh clone cannot run stages ① and ②.** → It needs the CLI and a subscription. Same shape as the
API-key gap already on the roadmap, and the README says work in progress for exactly this reason.

**The rendering stage talks to an endpoint somebody else brought up.** → Deliberate: it keeps machine
lifecycle out of the version whose only risk is the architecture. The cost is that an orphaned machine
is exactly as possible as it is today, and no less. The lifecycle and the reconciler land together with
the second flow.

**Two writers on one run directory would race on numbering.** → Out of scope by decision: there is the
CLI or a UI, not both, and the human is the only orchestrator until a UI exists. Recorded so it is not
re-derived when it bites: making "claim the next number" atomic is an exclusive-create on the target
name, so the loser retries the next number and no write is lost. No lock file, no staleness heuristic,
no daemon.

**`Refusal` moves out of the evaluator's module.** → It is a pure move with a re-export, so both
existing importers keep resolving and no behaviour changes. The alternative — importing the evaluator
from the pipeline — would make every pipeline command load several hundred lines of scoring rules, and
defining a second class with the same name is the collision D10 exists to prevent.

## Migration Plan

Nothing migrates. The new path is additive and the existing one is untouched, so this version has no
cutover and no data to convert. Rollback is deleting the new directories and the new module; the render
path that shipped before this version still works because it was never modified.

The irreversible act — deleting the old flow and restructuring the living spec — is v0.14's, deliberately
a version of its own, so that if the architecture is wrong there is still a proven path to fall back to.

## Open Questions

- **Re-rendering a seed on a flow that did not produce it** has no surface here. It becomes meaningful
  when a second flow exists and two arms are compared at one seed; the mechanism is already in place and
  only the invocation is missing.
- **Whether the sorting stage's effort setting helps or hurts.** The shipped invocation lowers it on the
  argument that sorting is slot-filling rather than reasoning. The probe ran at the default and did not
  test the alternative. It changes no spec, no interface and no task — it is one flag and a re-run.
