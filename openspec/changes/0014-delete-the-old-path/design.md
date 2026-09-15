# Design — v0.14, the deletion

**Verdict: `feasible`.** Nothing here is untested at cut time. The four places this version cannot be
pure deletion — the aspect-ratio ceiling, the type-checker override's ordering, the `--runs`
containment, the `up.sh` readiness wait — are **content**, settled below and carried as phases, not
conditions on the verdict. One genuine unknown remains and is recorded under *Open Questions*; it
changes no spec, no approach and no task.

See [`proposal.md`](proposal.md) for why.

## Context

`main` at `v0.13.0` carries two render paths. 726 tests, 11 capabilities, 256 scenarios. The old path
is `convert.py` → `isekai/cli.py` → `isekai/pipeline.py` over `workflows/pipeline.json`, with
`isekai/workflow.py`'s injection and `isekai/mutate.py`'s dial jitter. The new path is
`python -m isekai` over `flows/summon-v1/` and `.data/runs/<photo-id>/`.

The two graphs are **structurally independent** — 23 nodes each, different sets. The old one holds
`TilePreprocessor` and `LineArtPreprocessor`; the new one holds `EmptyLatentImage`,
`UpscaleModelLoader` and `ImageUpscaleWithModel`. Deleting the old graph touches nothing the new one
reads. **The cost of this version is spec and test surface, not graph surgery.**

Three couplings are the whole of the difficulty:

```
  isekai/workflow.py
    ├── PIPELINE_PATH · inject · find_node · find_nodes   old path only ─── dies
    │     └── MAX_TARGET_LONG_SIDE  enforced ONLY inside inject
    └── image_dimensions · working_resolution             ─── survives
          ├──▶ isekai/generate.py:56    the render path
          └──▶ isekai/evaluate.py:34    the evaluation capability

  tests/conftest.py:11,50   loads PIPELINE_PATH into a session fixture the whole suite sees

  openspec/changes/archive/0010-illustrious-base/controlnet_probe.py:46-54
          imports isekai.pipeline._render and six names from isekai.workflow
```

## Goals / Non-Goals

**Goals:** one render path; nine capabilities, each a contract with one owner; every surviving
requirement still bound to a test; the v0.13 deviation discharged *and* the replacement it promised
actually performed; a green gate at every phase boundary.

**Non-Goals:** no new product capability; no change to `summon-v1`'s graph, dials or manifest; no
`migrate`; no `session()`; no `scripts/` → `provisioning/` rename; no re-measurement of anything.

## Decisions

### D1 · The old path is deleted under L3, not because the new one beat it

`workflows/pipeline.json` cannot enter the registry **L3** defines — *a selectable implementation is a
measured one*. It was measured on style and rejected, and **never measured on identity at all**: F37
5/6, F40 8/10, F41 14/17 and F47 10/10 person-level are every identity figure this project holds, and
all four belong to the flow that became `summon-v1`.

*The supporting evidence, scoped exactly.* **F24**, against the old architecture's best tuning:
`fromnoise-v1` **0.0240** median linework to `notile-d045`'s **0.0043**, same six subjects, each render
read at its own photograph's canvas. **That is style, and only style.** F11:336's table lists
`shipped (v0.12)` and `notile d0.45` as *different arms*, and F11:352 names the latter *"the candidate
setup"* — it was never shipped, which makes the comparison generous to the old path rather than
flattering to the new one.

*Alternatives rejected.* **"The old path is useless"** — refuted by its own graph: `LoadImage(2)` fans
out through `ImageScale(22)` into `VAEEncode(9)`, `ApplyInstantIDAdvanced(8)` and three ControlNet
preprocessors. It reads the photograph four ways. What it lacks is a sheet: node 3's text is fixed
style boilerplate with no subject content. **"Measured-inferior replaced by measured-better", unscoped**
— reads as a head-to-head covering identity, which was never run on either instrument.

### D2 · "Proven" meant the seam, and the record is corrected rather than the plan

v0.13's phase 9 stated its own claim: *"verify by eye that flow `summon-v1` rendered a recognisable
anime image of each subject from a photograph nobody hand-captioned — **the seam this whole version
exists to cross**."* Five photographs, approved **unedited**, recorded `edited: false` — the control
arm, not the best case.

**L30's bar has never been evaluated for any flow in this repository.** Its two tests both ran in F47
— permutation `p = 0.0000`, person-level 10/10 against a chance expectation of 2.6 — but F47 states
*"The encoder is still `glintr100`… **SFace was not run on this set**"*, and L30 exists precisely to
say that reading does not count. Nothing on `main` can compute it: `isekai/evaluate.py` is a per-render
scorer with `glintr100` as its only encoder, and `grep -i sface isekai/ scripts/ tests/` returns
nothing. The identification apparatus is `prototype/face_likeness.py` and `same_person.py`, on a branch
that never merges.

This is not a blocker, because **D1 is the licence**. It is a correction to the laws, made in the
vault by this session: L18 states what "proven" meant, and L30 records that no flow has yet been graded
against it.

### D3 · `isekai/workflow.py` becomes `isekai/photo.py`

~230 lines survive: the JPEG/PNG header walk, the EXIF transpose, `image_dimensions`,
`working_resolution`, `WORKING_SCALE`, `DIMENSION_STEP`, `MAX_HEADER_*`. They answer one question —
*what is this photograph, and what render target does it imply* — and touch no ComfyUI graph, so
`workflow` is a name that would lie. Two importers change one line each: `generate.py:56`,
`evaluate.py:34`. `evaluate.py:228`'s comment becomes true again.

**`image-generation` owns the scenarios**, not `evaluation` and not a new capability. The contract is
*"the render target is derived from the photograph's own header"*, which is the render path's claim to
make; `evaluation` consumes it in order to assert agreement, which
`evaluation:canvas:mismatched-render-is-refused` already does. *Alternative rejected:* a tenth
capability owning the header contract — a capability for one pure function pair is the
one-entry-registry shape `CLAUDE.md` rules against.

### D4 · The 4:1 target ceiling is restored to the surviving path

`MAX_TARGET_LONG_SIDE = 4096` is enforced **only** at `workflow.py:356-361`, inside `inject`, via
`sys.exit`. `working_resolution` is pure arithmetic with no ceiling, and `generate.py`'s
`photo_resolution` (`:235-251`) catches `SystemExit` out of `image_dimensions` but never checks a
target. **The new path has never had this bound.** That is a live gap on `main`, not a regression this
change introduces — and deleting `inject` is what would make it permanent.

It moves as a **`Refusal`**, not a `sys.exit`, because `photo_resolution`'s own docstring already
argues the case: *"A batch must survive one unreadable header… a `SystemExit` walks straight past it,
taking the remaining photographs with it after the endpoint is already rented."*

**It bounds the working target, at 4:1, exactly as `inject` did.** The comment at `workflow.py:30` is
explicit that *"4096 is 4:1 at a 1024 short side"* — it is an **aspect bound wearing a pixel bound's
clothes**. Hires scales both axes by 1.5 and therefore does not change the aspect ratio, so bounding
the hires target instead would silently tighten the aspect bound to 2.67:1 for a reason unrelated to
aspect. *Alternative rejected:* dropping the scenario and recording the regression — it is six lines,
and converge cannot see the gap because all five gate commands are green without it.

### D5 · The archived probe is exempted by file, permanently, in phase 1

`controlnet_probe.py` imports `isekai.pipeline._render` and **six** names from `isekai.workflow` —
`PIPELINE_PATH`, `find_node`, `find_nodes`, `inject` die, and `image_dimensions`,
`working_resolution` move to `isekai/photo.py`. It is the **only `.py` file in the entire archive**,
across thirteen changes.

Measured, not assumed:

- **`ruff` is not implicated.** Piped through `ruff check --stdin-filename` at that path, a file
  importing names that do not exist reports nothing about them. Ruff does not resolve imports.
- **`ty` reports both a missing module and a missing member as the same rule**, `unresolved-import` —
  confirmed against a throwaway file, since removed. That is exactly the rule `pyproject.toml:102-106`
  already scopes off for `isekai/eval_backends.py` and `baseline/build_contact_sheets.py`.

So the fix is **one entry in the existing `[[tool.ty.overrides]]` include list**, by literal path — the
form already proven in that file, where a `**` glob is not. It lands in **phase 1**, while it is still
a no-op, so no phase boundary is ever red and the commit that adds it carries its own rationale rather
than appearing inside the deletion diff as gate-weakening.

*Alternatives rejected.* A blanket `openspec/changes/archive/**` exemption grants cover in advance to
files nobody has written; the existing block's own comment argues the opposite — *"Scoped to those
files and to that one rule."* Editing or renaming the probe violates *"archived changes are never
deleted."* Excluding `openspec/` from `ty` weakens every rule on every future archived file.

**The cost, accepted:** a future archived file with a genuine import typo goes unreported. An archived
change is never executed, never imported, and claims only that it was true at its commit — which
today's tree cannot verify in either direction.

### D6 · `cli` is `REMOVED` × 30 and `MODIFIED` × 0

Requirements 1–6 are `convert.py`'s: `dial-defaults` 4, `dial-validation` 12, `dial-plumbing` 1,
`output-destination` 4, `reproducibility` 6, `fixed-dials` 3 — **exactly the 30 the vault records as
surviving**. Requirements 7–12 are 13 scenarios, every one written at v0.13.

`cli.md`'s three claimed survivors each fail on inspection, and the delta records why, because both
`cli.md` and `round-5/MIGRATION.md` §3 assert the opposite and both stay in the vault. Range validation
has nothing left to validate — dials come from `flow.json` under L8 and a flow is immutable under L3.
Provenance flags are superseded by L25's `producer`. And the output-directory contract's replacement
**did not exist**: `grep -rn -- "--runs|\.data|DATA_ROOT|gitignored" openspec/specs/` returned nothing
across 256 scenarios, which is D7.

### D7 · `--runs` bounds the working tree, not the filesystem

The defect is not *"outside `.data/`"* — it is *"inside the git working tree, where nothing ignores
it."* `--runs /Volumes/BigDisk/runs` is safe; git cannot track it. `--runs ./acceptance-runs` is the
hole, and `run.py:271-274` copies the photograph in by construction.

So: **refuse when the resolved run root is inside the repository working tree and not under
`DATA_ROOT`; accept any path outside the repository.** This is strictly more correct than the comment
it replaces, which claimed containment under `.data/` that is not actually wanted, and it keeps the
flag's stated purpose — a version's acceptance run getting its own directory — intact.

The requirement is the part that closes it. The claim has sat in a source comment since v0.13 and has
been false that whole time *because no scenario held it*.

### D8 · `comfy-transport`'s two orphaned scenarios are rebound, not deleted

`tests/test_polling.py` drives `pipeline.run` and dies whole, taking the only test for
`comfy-transport:polling:polls-history-until-complete` with it. The behaviour is **live** —
`generate.py:388-397` submits, loops on `client.history(...)`, then `client.view(...)`. Measured
coverage after deletion: retrieval is *partly* covered at `test_generate.py:270` (the bytes, not which
image dict was requested); polling has **none**, because every `test_generate` call passes `poll=0` and
nothing constructs `FakeComfyClient(pending_polls=…)`.

Rebinding is the two existing tests with `pipeline.run` swapped for `render`. **Deleting them would
delete a requirement that is still true** — the worst outcome available, and the one that looks
cheapest. They stay in `comfy-transport` rather than moving to `image-generation`: L7 keeps the
endpoint a seam so a second provider is an implementation rather than a refactor, and that capability's
own statement already names *"waiting for the render, and downloading the result"*.

### D9 · `draw_seed` is deleted, not moved — and one scenario survives it

`round-5/MIGRATION.md` §2 and §4 promised a move. It could not have happened: `draw_seed` takes a
`Workflow` and calls `find_node(class_type="KSampler")` under an exactly-one contract, and
**`summon-v1` has two KSamplers** (10 and 34). It would refuse on the very graph it was promised to.
`generate.py` wrote `SEED_BITS`, `draw_seeds()` and `seeds_for()` instead, and every divergence is a
law written after `draw_seed`: `already` is L26, the absence of `find_node` is L8, and the old
function's one stated property — staying the *first* draw so a held run and a jittered run align — was
deleted by L4 along with jitter.

The two agree on exactly one thing, **64-bit width**, and
`workflow-mutation:jitter:seed-is-64-bit` is the **only** binding on it in the living spec.
`image-generation:seeds:*` covers distinctness, explicitness, exclusivity and grouping — nothing about
width. So it moves: `workflow-mutation` is 43 die, 1 moves. *Alternative rejected:* folding width into
`count-draws-distinct-seeds` — distinctness and width fail independently, and a scenario that can fail
two ways reports the wrong one.

### D10 · `infra/up.sh`'s bounded wait is absorbed — and the proxy fallback is not

This does **not** pass this version's coherence test — *would this line exist if the old path had never
existed?* It is absorbed anyway, on one specific ground: `main`'s poll is `while true … sleep 5` with
**no deadline**, which the prototype's own comment calls *"the one thing in this repository that could
bill indefinitely while looking like it was working. It cost two sessions on 2026-09-08."* `main` also
lacks the `8188/http` proxy fallback for the `runtime: null` / no-public-IP case.

**v0.14 is the only version in the arc with no GPU phase**, so it is the one place infra work does not
compete with a version's own metered risk — and every version after it needs a pod to accept. Leaving
it on a branch that never merges, in front of v0.15's acceptance run, is P4's *"an unwritten limit is
what produced three orphaned pods"* repeating with the limit written down somewhere that does not ship.

**Only the bounded wait is taken.** The prototype's companion change — the `8188/http` port and the
proxy probe — is **deliberately excluded**, and the vault already says why: the RunPod proxy is a
**public, unauthenticated endpoint**, ComfyUI has no auth, and the backlog's `P1` states that *"a
version adopting it must put authentication in front of ComfyUI first."* It also puts a pod id into a
public URL, which is the live half of `0008-one-path:S1b`. The prototype accepted that because its
sessions were minutes long and torn down; a released version is not a prototype. **The bounded wait
adds no exposure — it only removes one — and that asymmetry is the whole reason one half crosses and
the other does not.**

`scripts/` → `provisioning/` is declined even though its trigger technically fires — this version does
open `scripts/models.json`. It is cosmetic, it touches `pyproject.toml`'s `extra-paths`, `pytest`'s
`pythonpath`, the `Dockerfile` and `download_models.sh`, and landing it inside the deletion diff makes
both harder to review. It belongs with v0.19's `provision`.

### D11 · `CLAUDE.md`'s one-path bullet is replaced, not restored

v0.13 declared **two** deviations: that it carried both paths, scoped to itself, and that *"the
one-path bullet is replaced by an entry gate, not a count."* It discharged neither — the first lapses
only when the old path is deleted, and **the second was declared and never performed**.
`CLAUDE.md:17` still says *"There is one path."*

Restoring it verbatim would forbid the flow registry **v0.16 adds** (`conjure`), making the next feature
version a deviation again. It is replaced by L3's gate, keeping the history clause that explains why
the rule exists — a count permits an unmeasured single path, which is precisely what
`workflows/pipeline.json` was.

`CLAUDE.md` is stale at **13 sites**, of which two are rules (`:17`, `:178-179`) and eleven are facts
that become false — including `:109-110`, which still describes the living spec as *"four
capabilities… a fifth, `model-provisioning`, is written and test-backed on the v0.9 branch."*

### D12 · Two identifiers deliberately keep a historical word

`evaluation:canvas:resolution-comes-from-the-injector` keeps its key **and its scenario name**. The key
is a test-marker binding, the name is what `openspec validate` matches a MODIFIED block against, and
churning both to replace one word would change a marker for no behavioural reason. The requirement's
normative text names the render path.

### D13 · The evaluator's orphaned reader is recorded, not repaired

`tests/test_evaluate.py:601` and `:626` drive `pipeline.run` to obtain a manifest **the pipeline actually
wrote**, then assert the table names the image from it. Their driver is deleted, and the render path this
version keeps writes no `pod_image` key at all — `generate.py`'s render provenance is
`flow · seed · sheet_version · graph_sha256 · flow_graph_sha256 · edited`.

**They are deleted, and nothing else moves.** The scenario they bind,
`evaluation:report:names-its-run`, keeps **three** passing tests — `:574`, `:589`, `:640` — which build
their inputs directly and do not touch the old path. No requirement loses its binding, `pod_image_of`
stays correct code for a manifest that carries the key, and it already answers `"unrecorded"` honestly
when one does not.

*Alternative rejected: teaching `generate` a `--pod-image` flag.* It is real provenance — the image is
the **third leg** of what determines a render, beside the flow (pinned by digest) and the weights (pinned
by digest), and it is the only leg nothing pins or even labels. But the flag records **a string the
operator types**, not something read from the pod: v0.13's own acceptance run recorded
`ghcr.io/…/isekai:latest`, a moving tag, which is close to worthless as evidence. Adding it here is scope
in a version whose content is deletion, and the operator's decision is that v0.14 stays pure.

**The fact worth recording is larger than the flag, and it is the reason this is a note rather than a
fix.** The standalone evaluator's entry point reads a `run.json` of v0.12's shape — it refuses unless the
manifest carries `photo_sha256`, `base` and `renders` — and **the v0.13 run frame writes none of those**.
So the evaluator **already cannot read a v0.13 run today**; what v0.14 removes is the only remaining
producer of the shape it *can* read. That is a pre-existing gap this version makes total, and it belongs
to **v0.18**, the version whose entire content is the evaluation tool. Its proposal must repoint the
reader at the run directory — and, if the image is wanted in the table, add the field then, in the
version that publishes the baseline every later release is measured against.

## Risks / Trade-offs

- **A scenario key survives its subject's name** (D12) → the requirement text is authoritative and says
  "render path"; the key is an identifier.
- **`conftest.py`'s `workflow` fixture is repointed at `flows/summon-v1/graph.json`**, and five tests
  in two files then assert LineArt/Tile facts the new graph does not have → they are content edits with
  known expected values: `annotator_files` yields 2 rather than 4, and `unclassified_node_classes` is
  empty against the new graph.
- **The `-S` stdlib guard pair splits.** `tests/test_evaluate.py:750` guards `import convert` and dies
  with its target; its falsifiability twin at `:769` then sits in a file whose guard has gone → the twin
  moves beside `tests/test_pipeline_cli.py:92`, the guard v0.13 already built against
  `isekai.__main__`. **L1 as written said the guard would point at `isekai.cli` after `convert.py` went;
  `isekai/cli.py` is deleted in the same version, so there is no such target** — corrected in the vault
  by this session.
- **The standalone evaluator cannot read a run this pipeline produces**, and after this version nothing
  produces a run it can read → recorded in **D13**, owned by **v0.18**. It is an opt-in operator tool
  that no gate command exercises (nothing under `tests/` imports the root entry point at all), so it
  fails no check and blocks nothing — which is exactly why it has to be written down.
- **Four `models.json` entries are orphaned** by the old graph's deletion — the Tile and mistoLine
  ControlNets and two `sk_model` annotators, ≈2 GB → removed from the manifest and from
  `derive_manifest.py`'s `PINNED`, with three publishers dropped from `PUBLISHERS`. `test_flow.py:138`
  uses a subset check, so leaving them would not fail the gate — it would just download 2 GB nothing
  reads.
- **`.gitignore`'s v0.13 comment schedules two lines for this version and is wrong about one** —
  `.inputs/` still has a reader in `baseline/build_contact_sheets.py:107`, which survives. Only
  `outputs/` goes.
- **No API-free render path exists between v0.14 and v0.15** → named rather than argued away. The
  README already declares work in progress for this reason, and v0.15 restores it.
- **Inherited obligation for v0.18:** repoint the standalone evaluator's `run.json` reader at the run
  directory (**D13**), and decide there whether the table names the image — because v0.18 publishes the
  baseline every later release is compared against, and a baseline is the one run that cannot be
  re-recorded later.
- **Inherited obligation for v0.15, recorded here so it cannot be forgotten between versions:** L3
  removes an implementation only in the version that retires it. **v0.15's proposal must state in as
  many words that Claude stays registered at ① and ② until an open implementation clears its bar.** The
  fallback for v0.15's risk is `--impl claude`, not the path this version deletes — and JoyCaption
  already missed its own stated floor once (F42: **0.518** against **0.60**).

## Migration Plan

Deletion only; no data migration. Existing run directories are untouched — `summon-v1` and the schema
version are unchanged. **Rollback is the tag**: `v0.13.0` remains, and `convert.py` works in any
checkout of it.

Ordering is the one constraint that matters: **the `ty` override lands first** (D5), while it is still
a no-op, so no phase boundary is red.

## Open Questions

- **The allocation at the aspect bound is unmeasured, on either path.** At 4:1, `summon-v1` allocates
  `1536×6144` ≈ **9.4 MP** — 2.25× what `MAX_TARGET_LONG_SIDE`'s stated rationale measured
  (`1024×4096` ≈ 4.2 MP, on a path with no hires pass). Whether that OOMs on the target card is not
  known. The bound is restored at its original value and its original meaning; **whether 4:1 is still
  the right number is a question for a version with a GPU phase.** This changes no spec, no approach
  and no task in this change.
