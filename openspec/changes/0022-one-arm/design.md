# Design — 0022 one arm

**Verdict: `feasible`.** Every decision below was settled against a body read at `main` `44e5a2d`,
after v0.21.0 was tagged and `0021-sheet-from-the-tagger` archived. Nine of the twenty-one decisions
the grilling brief carried were overturned by evidence; each overturn is recorded at the decision it
replaces.

## Context

v0.19 added a second reader arm beside the `claude` CLI and proved, with a resident falsification test,
that a flow declaring one implementation reaches no name from the other. v0.21 removed the hosted
*sorter* — the sheet is now filled from `wd14/` through an authored table — and left
`hosted.sorter: "qwen3:8b"` in `summon-open-v1`'s manifest as a required key nothing reads, carried
dead because removing it would move a frozen flow's digest.

This change retires the first arm. What makes it larger than a deletion is the flow set: two of the
three tracked flows select the Claude arm by declaring *no* `hosted` block at all, so the arm cannot be
removed without replacing them, and a flow is immutable — editing one is not a variant of a flow, it is
an untested flow (`CLAUDE.md:211-212`).

**The measurement that licenses the retirement** is v0.21's phase 9, recorded in `CHANGELOG.md:170-182`:
over eight fresh photographs WD14 offered 309 tags, the router placed 226 (73%), 204 of those survived
review (90%), and the operator typed 2.6 tags a photograph by hand. The arm being deleted contributed
nothing to any of it.

## Goals / Non-Goals

**Goals.** One reader implementation. One manifest key naming the model it runs. No sentence in the
source or the live documents that claims something untrue of the running system.

**Non-Goals.** The tag table, the deriver and the router are not touched (D7). No second checkpoint is
tried. `scripts/` → `provision/` waits for v0.22.1. No new capability.

---

## Decisions

### D1 · The `hosted` block is deleted, not shrunk, and a required top-level `model` replaces it

The brief settled that `hosted` collapses to one live key, `reader`. That is half an argument. `hosted`
named a distinction — `openspec/specs/caption/spec.md:169-172`: *"one reaches a model over a network to
a third party, the other over a socket to this machine"* — and after this change only the second
exists. A block whose name no longer distinguishes anything, holding a single key, is exactly what
`CLAUDE.md:208-210` calls not a declaration, in the sentence that explains why the manifest names none
of its siblings.

So the manifest declares `"model": "joycaption-beta-one-q4k"` at the top level. `Hosted`
(`flow.py:221-234`), `REQUIRED_HOSTED` (`:94`), the missing-key check (`:371-379`) and the construction
(`:425-433`) are all deleted; `model` joins `REQUIRED` (`:63`) and therefore `KNOWN` (`:86`).

**The name is `model`, not `reader`, and that is measured.** `wiring.py:117-119` builds the reader from
it and `wiring.py:131-139` builds the hosted tagger from *the same key* — its docstring says so: *"One
model answers both prompts, which is exactly why `TAG_PROMPT` is not chat-framed: two calls to the same
alias must not arrive framed differently."* All eight v0.21 runs carry a `tags/` artifact whose
producer reads `"models": ["joycaption-beta-one-q4k"]`. A key named `reader` names it after one of its
two callers; `model` names what it is, and the manifest then says once what a seven-line docstring
currently has to explain.

### D2 · `MANIFEST_VERSION` 2 → 3, and the reason it stayed at 2 expires here

`flow.py:83-85` records why the key was made optional: *"Required plus a version bump was this change's
first shape and it was wrong: it forced an edit to two frozen directories in a change whose whole point
is to add one and touch nothing."* Both of those directories are deleted by this change, so the cost
the comment was avoiding is no longer payable — it is already being paid for other reasons.

### D3 · The allowlist the brief wanted inside `hosted` dissolves — overturns brief decision 14

The brief settled that the `hosted` block gets a key allowlist, on the ground that `load_flow`'s
docstring (`flow.py:326-333`) calls the typo *"the only silent path left"* while the block itself checks
only for missing keys. Measured, that is true: `flow.py:371-379` iterates `REQUIRED_HOSTED` and nothing
rejects an unknown key inside the block, so `{"implementation": …, "reader": …, "sorter": …, "sortr":
"x"}` loads clean.

Flattening closes it for free. A top-level key is guarded by the allowlist that already exists at
`flow.py:350-357`, which refuses any key `KNOWN` does not carry, naming it. **No new check is written.**

### D4 · The loader validates the value, not only its presence

`flow.py:425-433` applies a bare `str()` to each hosted value with no validation, so `{"reader": null}`
loads today as the Python string `"None"` and a run proceeds against a model alias that cannot exist.
Since D1 rewrites this parse, `model` is checked for being a non-empty string and refused by name
otherwise. This is not scope creep: it is the same three lines, and leaving the defect in code being
rewritten in the same commit is how a known bug becomes a carried one.

### D5 · Three directories out, two in — a rename is a delete plus a create

`manifest_digest` (`flow.py:437-451`) hashes *the name and bytes of every regular file* in a flow
directory. Deleting `sheet.briefing.md` from `summon-open-v1` moves its digest off the pinned
`e035d227…`, and `SIBLINGS` (`flow.py:59`) makes `load_flow("summon-open-v1")` refuse outright until the
loader itself changes. There is no edit that keeps the identifier: the survivor is a rename, which at
this digest rule is a deletion and a creation.

The roadmap's ships-block deleted `sheet.briefing.md` from *"every flow"* while replacing only two, and
had no stated outcome for the third. The truth is three out and two in.

### D6 · The names carry the base, and `CLAUDE.md` gains its first flow naming rule

`summon-anime-wai` and `conjure-anime-wai`: `<verb>-<style>-<base>`. The roadmap deferred the
base-in-the-name question *"because there is one base"*; the catalogue holds **twelve** candidate
checkpoints of which eleven are marked untried and **zero — including the pinned WAI v1.70 — is
provisioned on this machine** (`models/checkpoints/` does not exist; the base is fetched onto the pod).
With eleven queued, a second base is the likely next move and `summon-anime` could not tell two of them
apart.

**There is no flow naming rule in `CLAUDE.md` today** — the brief's premise that the convention is
"recorded there" is false; what is recorded at `:211-212` is an *identity* rule, that a changed digest
is a new flow. This change writes the naming rule, and writes both halves of it: the triple, plus `-v2`
appended only when a second generation of the same triple exists. A rule that forces a new identifier
without saying what one looks like is the gap that produced `summon-open-v1` — a name describing the
*arm* rather than the flow, which this change is deleting for that reason.

### D7 · `eyelashes` stays in `conjure-anime-wai`'s schema — overturns brief decision 2

The brief settled the drop on *"a new flow's schema is authored fresh, so it costs nothing."* Measured
against the bodies, it is the most expensive act in the version, and none of the cost is about Claude or
Qwen.

`scripts/derive_field_map.py:628` reads the criterion list from the tracked flows' own schemas
(`fields = sorted({name for names in declared_fields().values() for name in names})`), then `claims()`
seeds `groups` from *those names only* and unconditionally indexes three criterion-keyed constants into
it — `SUFFIXES:98`, `BRIEFING:181`, `PRECEDENCE:361` all carry `eyelashes`. `groups[field] |= …` reads
before it writes, so an undeclared criterion is a `KeyError` before the deriver emits anything. This was
confirmed by running `claims()` against a shrunk union.

And the table cannot simply be corrected by hand: converge's round-1 fix added
`tests/test_field_map.py:394`, which runs the whole deriver into a temp path with `filings()` rigged to
raise and compares **raw bytes** against the committed file. A hand edit is red by construction.

So dropping one `scored: false` field means editing three deriver constants, regenerating
`scripts/field_map.json`, bumping its `revision` — which `field-map:table:it-names-its-own-revision`
pins and the sheet's producer records — and moving two assertions in `tests/test_field_map.py`.
Keeping it costs nothing at runtime: the operator already fills it by hand from the prose, an empty
field is legal, and `field-map:coverage:an-empty-group-is-legal` exists precisely to record that the
vocabulary holds four `eyelashes` tags in total. **The flow-set change is five artifacts, not seven.**

### D8 · `conjure-anime-wai`'s caption briefing is a byte-identical copy of `summon-anime-wai`'s

The brief framed this as *conjure-v1's briefing was authored for Claude, summon-open-v1's for
JoyCaption*. **No file under `flows/` contains the word `claude`, or any model or implementation
name** — the arm was selected by the *absence* of a block. What actually differs is register:
`conjure-v1`'s (4039 B) negotiates with a reader that reasons, adding a nine-item walk-through and three
prohibition paragraphs about the face; `summon-open-v1`'s (2185 B) commands one that under-produces —
*"write a long, detailed description"*, *"look carefully"*.

The face content was authored for a path v0.21 deleted. `CHANGELOG.md:1355-1357` records why conjure
declares five extra face fields: *"In `summon` the identity and pose legs supply the face; `conjure` has
neither, so the face reaches the render only as tags."* Those tags came from the prose, through the
sorter. Since v0.21 the sheet is filled from `wd14/` and the prose is a reading aid with no machine
consumer (`README.md:108`).

So both flows read the same model with the same purpose, and a second authored briefing would be a
second untested artifact — the thing `tests/test_flow.py`'s own docstring calls *"a paraphrase is an
untested briefing wearing a tested one's reasoning."* Byte-identical files across flows are established
practice: `summon-open-v1`'s graph and schema already are.

### D9 · `sheet.briefing.md` leaves every flow, and `SIBLINGS` drops to three

It has had no reader since v0.21, which `CLAUDE.md` already records as carried dead. It is deleted from
both new flows and from `SIBLINGS` (`flow.py:59`), and `Flow.sheet_briefing_path` (`:282-284`) goes with
it — a property resolving a path inside a frozen directory where no file exists is a worse artifact than
no property.

### D10 · The structural rule stops counting

*"A flow is five flat files"* is asserted in thirteen places — `CLAUDE.md:205`, `image-generation`'s
requirement and scenario, `flow.py:9, :11, :49, :410`, `README.md:287`, `foundation/README.md:12`, and
four sites in `tests/test_flow.py` — **and in none of them is it an integer.**
`test_a_flow_is_five_flat_files_and_the_manifest_names_none_of_them` asserts set-equality of
`iterdir()` against `(MANIFEST_NAME, *SIBLINGS)`, which shrinks on both sides at once and stays green.
The count is load-bearing only in prose and test names.

v0.19 **refused to weaken** this rule to house `joycaption.Modelfile`, and the refusal is still on the
record in the source — `claude_cli.py:286-289`, in `constant_record`'s own docstring: *"The alternative
considered and refused was a sixth file in the flow directory: that is the trade v0.19 already priced
when `joycaption.Modelfile` went to `scripts/`."* **Shrinking a rule because its fifth member stopped
existing is not that act, and the record says so here rather than leaving the two to be confused.**

Renumbering five to four would only defer the question, because the count has now changed once and will
change again. So the rule names its files instead of tallying them, the spec key loses its numeral, and
`len(SIBLINGS)` gains the assertion it has never had — the first thing in the suite that would notice a
sixth sibling being added silently.

### D11 · `summon-anime-wai`'s graph and schema are carried verbatim, stale `filename_prefix` and all

`flows/summon-open-v1/graph.json:174` carries `"filename_prefix": "summon-v1"`, byte-identical to the
incumbent's, so the new flow will render files named for a flow that no longer exists.

**It is inert.** `filename_prefix` has zero reads in `isekai/` and `tests/`. isekai names its own output
(`generate.py:410`, `image = directory / f"{seed}{flow.output_suffix}"`) and treats ComfyUI's returned
`{filename, subfolder, type}` as a download coordinate it discards; node 12 is never patched; no sidecar
records it. The stale string is visible only pod-side, in ComfyUI's own `output/` folder.

Carried rather than corrected, deliberately: this version's acceptance is *the renders are what the
operator wants*, and a moved graph byte makes a failed acceptance unattributable. *Trigger to revisit:
the next version that opens either graph for a reason of its own.*

### D12 · Five names rehome to `foundation/run.py`; `ROOT` is deleted rather than rehomed

`foundation/refusal.py` cannot host them — its first line is *"The one refusal exception, in a module
that imports nothing"*, `CliFailure` needs `Kind` from `run.py:124`, and `run.py:41` already imports
`refusal.py`: a cycle. `run.py` already owns `Kind`, `record_failure`, `attempts` and `hashlib`
(`:32`), so the four survivors land without a new import.

The brief counted six shared names. **It is five.** `ROOT` (`claude_cli.py:51`) has no production
importer at all — it is read only at `:268` and `:270`, inside `instructions_record`, and its one
outside reference is `tests/test_package_paths.py:56`. `foundation/run.py`'s `DATA_ROOT` (`:52`) is
computed from a file at the same depth with the same three `.parent` steps, so `DATA_ROOT.parent` is the
same path by construction — and `wiring.py:237` already spells exactly that as `REPOSITORY`. So `ROOT`
is deleted and `instructions_record` reads `DATA_ROOT.parent`.

The other five names the brief listed as shared — `BASE_FLAGS`, `BINARY`, `Runner`, `spawn`, `invoke` —
are imported by `caption.py` only from inside `ClaudeReader` (`:136, :137, :150, :159`), so they die with
it. `invoke` is in turn the sole caller of `require_binary`, `classify`, `classify_text`, `detail` and
`models_that_ran` and the sole constructor of `Envelope`; `classify_text` is the sole reader of
`TRANSIENT_MARKERS` and `classify` of `DECLINED`. **Thirteen names die, all of them unreferenced once
the reader goes.**

### D13 · `CliFailure` becomes `StageFailure`, with no alias

The name says CLI; two of its three raising modules have no CLI in them. `tagging.py:195, :198` raise it
for an Ollama transport failure and `caption.py:227` for an Ollama reader failure. Renamed at the split,
in one commit, with no compatibility alias — an alias is how the old name survives a version that
existed to remove it.

`caption.py:121` is the site the brief's inventory misses: `FakeReader`, which is **production** code in
`isekai/pipeline/caption.py` and in its `__all__`, carries `failure: CliFailure | None` and
`raise self.failure` at `:128`.

### D14 · `refusal_for` widens from a `CliFailure` to `(kind, detail)`

`claude_cli.py:148-166` reads exactly two attributes off its `failed` argument — `failed.kind` and
`failed.detail`, both at `:163`. Nothing else. The type is friction, and `tagging.py:271` pays for it by
**fabricating** an exception purely to satisfy the signature: `CliFailure("permanent", str(failed))`,
where `failed` is a `Refusal | OSError` caught at `:258` and the very same two values are already
spelled literally at `:265-266` for `record_failure`. Widening removes the fabrication and removes the
last `StageFailure` reference from `caption_wd14` entirely. The other two call sites
(`caption.py:269`, `tagging.py:332`) each already hold `failed.kind` and `failed.detail` one line above.

### D15 · `briefing_text` is inlined and deleted

`claude_cli.py:143-145`. Its whole body is `return path.read_text()`. It has exactly one caller
anywhere including tests — `caption.py:259` — and rehoming a one-line alias over a stdlib method to
keep a single call site is carrying a name for its own sake.

### D16 · `DEFAULT_IMPLEMENTATION` is deleted with no fallback, and both registries collapse

`wiring.py:97`, one production read at `:176`. With every tracked flow declaring a `model`, a default is
a value that can never be selected. `READERS` (`:151-154`) and `HOSTED_TAGGERS` (`:163-166`) lose their
`claude-cli` entries; `_claude_reader` (`:100`) and `_no_tagger` (`:122`) are deleted. With a single
implementation there is no string to key a registry on, so `_resolve` (`:169-184`) and `_named_by`
(`:105-114`) collapse: the seams read `flow.model` directly.

### D17 · The registry tables' recorded justification is rewritten, not carried

`wiring.py:142-150` justifies a table over a conditional as preventing *"a complete run on the wrong
models with the artifact's own provenance disagreeing with the manifest that asked for it — silent, and
it corrupts any later comparison between the two arms."* **With no second arm to fall into, that premise
is gone.** What survives is that a manifest naming a model this build cannot reach still refuses by
name. The comment states the surviving reason; it does not carry the dead one.

### D18 · `tests/test_isolation.py` is deleted whole — overturns brief decision 9

The brief settled two tests retired and the third rehomed. The third,
`test_a_permanent_open_failure_reaches_no_other_implementation` (`:116`), binds
`caption:failure:decline-is-permanent` — a key with three other bindings, one of which
(`tests/test_caption.py:346`) already asserts the same claim without the seal. The seal is the only
thing the isolation version adds and there is nothing left to seal against.

The file's own docstring is the argument for deleting it rather than moving it: *"The obvious form of
this test passes vacuously, and that is the whole reason this module exists separately."* With one arm,
the sealed form is the vacuous one. **Retiring a guard deliberately is different from losing one, and
this is the deliberate case.**

*Recorded incidentally, because it is the kind of thing a later version should not rediscover:* the
`sealed` fixture's `spawn` patch (`:47`) is already inert. `ClaudeReader.runner: Runner = spawn`
(`caption.py:137`) is a frozen-dataclass default bound at class-definition time, so the patched module
attribute is never consulted — the exact failure mode the file documents for `ollama.post` at `:59-67`.
The seal fires through `require_binary` alone.

### D19 · `caption:selection:no-path-reaches-another-implementation` is REMOVED, not rehomed

It has **exactly two bindings, both in the file D18 deletes** (`test_isolation.py:91` and `:101`). With
one arm there is no other implementation for a path to reach, so the scenario is not merely unbound —
it is unprovable, and its parent requirement's rationale (`caption/spec.md:169-172`) describes a
two-arm world that no longer exists.

**`CLAUDE.md:173-175` records that this repository has no spec↔test binding checker**, so nothing in the
gate would have caught this. It is named here so the removal is deliberate rather than discovered at the
fold.

### D20 · `caption:refusal:absent-reader-names-the-fix` is REMOVED — overturns brief decision 13

The brief settled that it is rewritten for the surviving arm and gains the model-not-pulled case. That
case already has a scenario. `openspec/specs/caption/spec.md:198` — *"A hosted model that is not running
or not installed is refused before any attempt is spent"* — carries three:
`:213 unreachable-host-refuses-without-an-attempt`, `:220 absent-model-names-how-to-create-it`,
`:227 the-check-fires-at-first-call`.

`boundary/ollama.py` is HTTP to localhost; there is no binary to be absent. The requirement at `:86` is
entirely the missing-`claude` message with its `npm install` remedy, and both its tests
(`test_caption.py:413`, `:427`) drive `ClaudeReader` directly. Rewriting it would produce a second
requirement saying what `:198` already says with three scenarios behind it.

### D21 · Two scenarios are narrowed where they assert what a one-armed system cannot fail

- `caption:seam:producer-names-the-implementation` (`:50`) — *"a caption produced by a **different
  implementation** is distinguishable from the record alone"*
- `caption:failure:decline-is-permanent` (`:73`) — *"**no other implementation** is substituted to
  produce the caption"*

Both second clauses become vacuously true. This repository has a written standard against exactly that,
in the docstring quoted at D18. Each keeps its first clause — the producer names the implementation; a
decline is recorded as permanent — and loses the second. Neither is in the brief's casualty list.

### D22 · `caption` keeps a requirement, narrowed to the model

The flow still selects something, and getting it wrong still costs time: `joycaption-beta-one-q4k` not
created is the failure that will actually happen, and it is already specified at
`caption:reachability:absent-model-names-how-to-create-it`. So the requirement that survives says the
flow names the **model** it reads through, not the implementation — the thing that still varies per flow
once the implementation cannot.

### D23 · `cli:resolution:one-command-two-implementations` is REMOVED

It is premised on there being two, and v0.21 already MODIFIED it once. The per-flow resolution it
guarded survives in its two sibling scenarios, `cli:resolution:uncomposed-seam-refuses-by-name` and
`cli:resolution:a-seam-without-a-manifest-key-resolves-for-every-flow`, and `cli.py:406-409`'s comment —
*"Resolved per flow, not once per invocation"* — is narrowed rather than deleted, because two flows
still each get their own seam.

### D24 · All three `image-generation:hosted:*` scenarios are REMOVED — sharpens brief decision 12

The brief named one casualty and was corrected to three. The bodies say all three die and the
requirement goes with them:

- `incumbent-flows-are-unchanged` — its comparison target (`summon-v1`) is deleted.
- `absent-block-means-the-default` — becomes **false**, not unreachable: there is no default, and with
  `model` required, a flow declaring none is unrepresentable.
- `an-unread-key-is-carried` — added by 0021, and bound at converge round 1 to
  `test_the_sorter_key_is_carried_dead_and_has_not_moved_the_digest`, which asserts four things this
  change destroys: `hosted.sorter == "qwen3:8b"`, `sorter ∈ REQUIRED_HOSTED`, that no module reads
  `.sorter`, and that the digest is unmoved.

**That scenario was added at v0.21 and is removed at v0.22 — one version.** Worth the sentence: converge
is the pass that gave it a body, and the next version is the one that deletes the key it describes.

### D25 · `tagging`'s hosted-absence case is REMOVED

`tagging:independence:the-hosted-tagger-is-absent-without-a-hosted-block` describes a flow whose
manifest declares no hosted model. Once `model` is required, no tracked flow can be in that state.
`tagging:independence:the-local-tagger-needs-no-manifest-key` is untouched and still true — the WD14
tagger resolves through no manifest key at all.

### D26 · Four phases, not five — overturns brief decision 20

The brief settled five: the split, then the flow set and loader together, then the arm, then the
documents, then the acceptance. **The middle boundary cannot be made green in either order.**

`isekai/interface/wiring.py:176` — `declared = flow.hosted.implementation if flow.hosted else
DEFAULT_IMPLEMENTATION` — is the only line in the package that selects an arm, and it reads the key the
flow-and-loader phase deletes. `wiring.py` also imports `Hosted` at `:28` and reads `flow.hosted` at
`:112`, `:114` and `:208`. Deleting `Hosted` while the arm still stands gives an `ImportError` on
`isekai.interface.wiring`, so `ty check` fails, `import isekai.__main__` fails, and
`tests/test_pipeline_cli.py:230`'s stdlib guard fails with it.

Reversing does not help. Delete the arm first and `summon-v1` and `conjure-v1` — still tracked, still
declaring no block — resolve to a `DEFAULT_IMPLEMENTATION` that no longer exists. Making them resolve
would mean editing two frozen manifests, which `tests/test_flow.py:430-438` forbids by design and whose
message says so.

The brief's own forcing argument — *"deleting it while `summon-v1` is still tracked leaves a flow that
loads, is pinned, and cannot run"* — is sound, but it proves the two cannot be **separated**, not that
the arm comes second. **The flow set, the loader and the arm are one phase.** It is the largest phase in
the change and that is the honest cost; the alternative is a phase that ends red, which `mf-build`
treats as a halt.

### D27 · No grep tripwire and no PATH-absent acceptance

Considered and declined at the operator's call. The guard is `CLAUDE.md:18-25`'s rule — *a selectable
implementation enters on a measurement* — rather than a test, and with a one-entry `READERS` table a
second entry is a visible, deliberate act.

**Recorded cost: nothing in the gate would catch a reintroduction.** Stated here rather than left
implied, because a guard declined is only a decision if its price is written down.

### D28 · The scrub is Claude **and** Qwen, and Qwen's live footprint is nine lines

The test is *does this sentence claim something untrue of the running system*, not *does the word
appear*. Historical records keep both words: `openspec/changes/archive/` (148 lines across 30 files),
`CHANGELOG.md`'s released sections, git history, `ui/design/`, `CLAUDE.md`'s filename, and the
`Co-Authored-By` trailers. `CLAUDE.md:158-159` says archived changes are never deleted, and `0008`'s own
note says editing an archive *"would falsify the record it exists to be."*

The brief said Qwen's live footprint is three lines. **It is nine**, and the five it missed are in the
two documents this change rewrites anyway: `README.md:224`, `:228`; `CLAUDE.md:275`, `:281`, `:332`;
plus `flows/summon-open-v1/flow.json:99` and `scripts/joycaption.Modelfile:35`, and two sites in
`tests/test_flow.py` that die with the flow.

`scripts/joycaption.Modelfile:37` carries a live contradiction v0.21's phase 6 missed: it still calls
`qwen3:8b` *"the sorter, stage ②"* in the present tense, against `README.md:227` and `CLAUDE.md:280`
which v0.21 corrected. It is fixed here.

### D29 · The acceptance — one metered run, both flows, the same photographs

v0.19's isolation proof is the shape, inverted: there is no second arm to prove separation from, so the
claim is that the one arm is **complete**. Both flows run `caption` → `sheet` → `ui` → `generate` end to
end on the same photographs, two reviews, one per flow.

Supported as-is by the layout: one run, two flow subtrees
(`run-directory:layout:a-second-flow-adds-one-subtree`), two `ui` invocations because the surface serves
one flow at a time (`cli:flow-selection:a-serving-verb-takes-one-flow`). The cost is the prose read
twice and WD14 run twice per photograph, both local.

**`conjure` is not an unexercised path.** It has rendered four times —
`.data/v0.17/runs/*/conjure-v1/outputs/*/20260917.png`, 1536×2592, sheets edited and re-approved at
`review/002` — and each of those runs carries its own `conjure-v1/captions/001.json` under its own
briefing digest. Its `inputs: ["sheet"]` gates exactly one thing: `generate.py:405`'s
`upload_image`, i.e. whether the photograph's bytes cross the wire. It runs every stage.

**Metered cost is zero on phases 1–3.** A pod in any earlier phase is a halt. v0.21's comparable run was
21m36s on an RTX PRO 4500 Blackwell at ≈$0.30 for eight renders.

### D30 · What this change does not touch, and why it is named rather than assumed

`scripts/field_map.json` keeps `revision: 3`. `scripts/derive_field_map.py`, `isekai/shared/field_map.py`
and the WD14 tagger are not opened. Two table gaps v0.21's phase 9 surfaced — `accessories` holding two
candidates while `jewelry`, `earrings`, `bracelet` and `ring` were dropped on six of eight photographs,
and `marks` holding none while `mole` was dropped on four — are **left deferred**, at the operator's
call, so this version stays the arm and not the table. *Trigger: the next version that opens the table
for a reason of its own.*

### D31 · The acceptance ran, and the claim held — both flows, five photographs, one pod

Recorded here rather than in `CHANGELOG.md` alone because D29 set the claim and this is its answer.

**The operator's verdict: yes, both flows.** Stated directly, as 4.2 requires. Nothing was retried into
it — the ten renders this judgement was made on are the first ten the pod produced.

| | `summon-anime-wai` | `conjure-anime-wai` |
|---|---|---|
| WD14 offered | 160 | 160 |
| router placed | 118 (73%) | 124 (77%) |
| survived review | 114 | 126 |
| sheets the operator corrected | 3 of 5 | 4 of 5 |
| face-only fields filled by hand | — | **7 of 25** |

**The 7-of-25 is 4.3's number, and it is the one a later version re-reads.** `conjure` declares five
fields `summon` does not — `bangs`, `eyelashes`, `nose`, `lips`, `facial_hair` — because it has neither
an identity leg nor a pose leg, so the face reaches the render only as tags. Across five photographs the
operator filled seven of those twenty-five cells. `eyelashes`, the field D7 argued about keeping, is in
that set: keeping it cost nothing at runtime, exactly as D7 predicted, and dropping it would have cost a
table regeneration. **The prediction was right and is now measured rather than reasoned.**

**Both routing rates sit where v0.21's did** — 73% and 77% against v0.21's 73% over eight photographs.
The table was not touched by this change (D30) and the rate did not move, which is the negative result
that matters: retiring the arm changed nothing about what the router can place.

**The pod.** `r8gcl050ob1dox`, RTX PRO 4500 Blackwell in EU-RO-1, on `ghcr.io/alxb1t/isekai:latest` —
the released image, correct here because this version changes no `Dockerfile` and no model pin.
**Wall time 15m08s** against a 45-minute ceiling: created 06:19:03Z, ComfyUI reachable 06:24:08Z, first
render 06:24:48Z, all ten landed 06:33:55Z, `infra/down.sh` at 06:34:11Z.
Teardown confirmed twice by the RunPod MCP — `list-pods` returned `pods: []` and `get-pod
r8gcl050ob1dox` returned `404 pod not found`.

**The cost is not asserted.** At the time of writing RunPod had posted `podGpuAmount: 0` for the day and
only `storageStandardAmount: 0.0117` (the network volume, which bills whether or not a pod exists).
Billing lags, so the GPU figure is **unposted rather than zero**; at v0.21's implied rate 15m08s is
≈$0.21. Written this way because a number read off a lagging ledger and reported as final is exactly the
kind of claim this repository does not make.

**What the acceptance did not prove, stated so it is not read as proven.** Ten renders on five
photographs is a judgement, not a measurement: no identity score was taken, no pass mark was set, and
`--count 1` means no seed variance was sampled. D29 asked whether the one arm is *complete*, and the
answer is yes — every stage ran, both flows, end to end, with no refusal and no manual repair.

## Risks / Trade-offs

| risk | what it costs, and why it is accepted |
|---|---|
| Nothing in the gate would catch a reintroduced arm | D27, at the operator's call. The one-entry registry makes a second entry visible in review. |
| Phase 2 is large | D26 — the alternative is a red gate, which halts the build. It is one phase because the code makes it one. |
| Two new flows ship unrendered until phase 4 | Every earlier phase is offline and free; the render is the acceptance, and that is where the money is spent. |
| `summon-anime-wai` renders pod-side files named `summon-v1` | D11 — inert, and correcting it would move a graph byte in the version whose acceptance is a judgement about renders. |
| The absence-licence test is retired with its briefing | `caption:inputs:only-the-photograph-is-passed` keeps five other bindings (`test_caption.py:112, :125, :135, :461, :495`), so no scenario is left unbound. |

## Migration Plan

There is no data migration: `.data/` runs written under the old flow ids remain readable and are never
re-read by a new flow, because every artifact lives under its own flow's subtree
(`run-directory:layout:one-flow-s-work-is-one-directory`). Runs already captured under `summon-v1`,
`conjure-v1` or `summon-open-v1` keep their directories; a new run under a new flow adds a new subtree
beside them.

The operator's provisioning does not change: `ollama create joycaption-beta-one-q4k -f
scripts/joycaption.Modelfile` is still the one command, and `ollama pull qwen3:8b` stops being
mentioned because nothing has called it since v0.21.

## Open Questions

None. The grilling closed the frontier; every decision above cites the body it was settled against.
