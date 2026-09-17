# Design — v0.17, flow `conjure`

**Verdict: `feasible`.** This is the change's first content because it is the change's subject: the
question is not *can this be built* but *what does building it cost outside its own directory*. The full
edit set was derived by reading every call site rather than by grep alone, and it is **five new files
plus two lines in one test module.** Nothing under `isekai/`, `scripts/`, `Dockerfile`, `start.sh`,
`infra/`, `Makefile`, `pyproject.toml`, `.github/` or `openspec/specs/` is touched.

**One caveat, settled below rather than left as a condition.** Two of those lines are not the same kind
of thing, and conflating them would make this change report the freeze *working* as the registry
*failing* — D1.

See [`proposal.md`](proposal.md) for why, and [`no-spec-delta.md`](no-spec-delta.md) for the
`skip_specs` argument.

## Context

```
  flows/summon-v1/          5 flat files · manifest_digest walks iterdir() filtered
                            by is_file(), so the flat shape is load-bearing
  load_flow                 8 checks, 3 of them new at v0.16 and 2 of those never
                            exercised by a second flow:
                              REQUIRED_NODES     flow.py:81   positive negative
                                                              latent sampler
                              TRANSFERRED_INPUTS flow.py:91   checked at :327 --
                                                              `photo` must appear on
                                                              BOTH sides or NEITHER
  build_graph               generate.py:280-346 · 4 roles always patched,
                            7 guarded by `if role in flow.nodes`
  upload_image              generate.py:405 · gated on `"photo" in flow.inputs`
  photo_resolution          generate.py:302 and :170 · UNCONDITIONAL, and correct:
                            `run.photo` belongs to the RUN (run.py:285-290), not to
                            the flow, so it always exists and always parses
  PINNED                    tests/test_flow.py:44 · the pinned set must EQUAL the
                            tracked set (:418)
```

`tests/test_generate.py:804-815` already renders an `inputs: ["sheet"]` fixture flow with only the four
required roles through a fake transport — so the **code path** is exercised. What is not exercised is a
**tracked, pinned, provisioned flow** in `flows/`, which is a different claim.

## Goals / Non-Goals

**Goals.** Establish, before the build rather than after it, what adding a flow costs outside its
directory — and record the answer whatever it is.

**Non-Goals.**
- **Fixing what this change finds.** Seven findings leave with triggers. *A version that repairs
  everything it finds cannot report what its own subject cost.*
- **Any identity claim for `conjure`.** It is not evaluated and is measured against nothing. The flow
  that *is* evaluated is `control`, fed `summon`'s own approved sheet, which needs a manifest able to
  express consuming another flow's output — it does not exist and is not built here.
- **Touching `scripts/models.json`.** `conjure-v1` declares two of its twelve entries; nothing asserts
  the reverse direction, and provisioning has no flow concept at all.

## Decisions

### D1 — Two edits outside `flows/`, and they are classified separately

`tests/test_flow.py:44` gains `PINNED["conjure-v1"]`. **This is the freeze working.** The pin list is
what makes adding or removing a flow a deliberate act rather than a casual one; a change that reported
it as an incompleteness would be arguing to delete the mechanism.

`tests/test_flow.py:124` asserts `tracked_flows() == ["summon-v1"]`, inside
`test_every_tracked_flow_parses`. **Nobody designed this.** Every other test in the module names a flow
and iterates `tracked_flows()`. It is widened here, and it is **the only defect this change repairs**.

*Alternatives:* *"only `isekai/` counts as code"* — the definition that makes the change pass, rejected
for that reason. *"anything outside `flows/` counts"* — honest but flattening, and it produces the wrong
verdict about `PINNED`.

### D2 — The graph is reduced and reconnected, not rewritten

Delete nine nodes: `2` `5` `6` `7` `8` `16` `17` `18` `22`. Exactly six edges dangle, on exactly two
nodes, and each repoints to **the source InstantID displaced**: `10`/`34`.`model` → `["1",0]`,
`.positive` → `["3",0]`, `.negative` → `["4",0]`. Node `8`'s own inputs are those same three, so the
edit **restores rather than invents**. `32` is an `ImageScale` but belongs to the hires chain and stays.

**The prototype's ablation left `2` and `22` orphaned — 10 nodes, 8 reachable. This change deletes
them.** ComfyUI ignores unreachable nodes, so renders are unaffected; a frozen product graph carrying a
committed photograph filename that nothing will ever patch — `nodes.photo` cannot be declared, per D3 —
is dishonest rather than harmful.

### D3 — `photo` is declared on neither side, and the photograph is still read

`inputs: ["sheet"]` and no `nodes.photo`. `TRANSFERRED_INPUTS` refuses a manifest declaring it on one
side only; omitting it from both is the sheet-only case and passes (`flow.py:327-341`).

**And `photo_resolution` still runs** (`generate.py:302`), sizing `latent` and `hires_resize` from the
run's photograph header. **That is correct and required**: without it the two flows are not rendered at
matched resolution. It is not an incoherence, because `run.photo` is a property of the **run** — written
and media-type-validated by `open_run` — not of the flow's declared inputs.

### D4 — 21 fields, chosen by vocabulary depth

`summon-v1`'s sixteen plus `bangs` (17 canonical tags), `facial_hair` (9), `lips` (4 shape + 7 colour),
`nose` (3), `eyelashes` (4). **Every one is reachable by the suffix pass or by containment**, so the
schema is pure data: `map_phrase(phrase, vocabulary, suffix)` takes the suffix from the schema
(`vocabulary.py:278-323`), and "thick" + `lips` → `thick_lips`, "long" + `nose` → `long_nose`.

**In `summon`, InstantID and OpenPose do part of the job on the face, so its schema never needed facial
structure.** `conjure` has neither, so the face reaches the render only as tags.

*Refused:* **`jaw`** — the 8,106-tag vocabulary has **zero** jaw tags, and a field that cannot be filled
produces a sheet that looks more complete than it is. *Deferred:* **`eye_shape`** — and the reason is
**what a reader would actually write**, not the tags' existence. Measured rather than assumed, during
the `/simplify` pass: of eight English eye-shape phrases, **only `upturned` maps** — `upturned` +
`eyes` → `upturned eyes` (count 2,096) through the ordinary suffix pass, while `droopy`,
`downturned`, `narrow`, `almond`, `hooded`, `sharp` and `round` all return `[]`. The four canonical
tags (`tsurime` 31,622, `tareme` 32,196, `jitome` 26,634, `sanpaku` 7,731) are reachable by the
**exact-match** pass — `map_phrase("tsurime", v, "eyes")` → `["tsurime"]` — so they need no curated
span at all; what they need is a sorter that already writes Japanese, which the briefing does not ask
for and should not. So the field would ship with one reachable English phrasing out of eight, and the
route to the rest is `CURATED` (`vocabulary.py:77`), a module constant shared by every flow that no
manifest can declare. **Seven dead phrasings is the wrong price for the first edit to shared
routing** — and the counts say the loss is larger than "four tags" implies, which is the honest way
to leave it parked.

All five are `scored: false`: the evaluator has no measurement for any of them, and `scored` is what
keeps a published table's coverage checkable rather than asserted.

### D5 — The briefings both differ, and inference is licensed on named axes only

`caption.briefing.md` is richer on the face and **licenses inference on expression and the scene's
light**. *"Do not interpret"* is **kept and narrowed to the identity-bearing fields** — marks, hair,
eyes, skin, build — which is where the measurement behind it was taken: a reader pressed into a schema
manufactured nineteen identity marks across seven of ten subjects and its score fell from 0.518 to
0.307. **`marks` keeps the absence licence and the no-pressure rule verbatim**, because the follow-on
failure is that a stated absence reaches the prompt and CLIP has no negation. `gaze` stays surface.

`sheet.briefing.md` differs because it must: it carries a `## The fields` section naming each field and
**two worked examples printing a complete sheet.**

### D6 — Dials are `summon`'s minus three, and every survivor is measured

`ip_weight`, `identity_cn_strength` and `openpose_strength` go dead. `cfg` **5** was chosen on the
identity-leg ladder, which raised the question of whether it transfers to a leg-less graph; **it was
already measured there** — the prototype's sheet-only arm rendered at `cfg: 5`, recorded in its own arm
files. **This flow ships no unmeasured value.**

**And every dial is checked against the publisher's own recommendation rather than against this
project's habit** — `tasks.md` carries WAI-Illustrious-SDXL's *"How to achieve optimal results"*
verbatim, and phase 2.5 writes the provenance table into this file. Sampler, the quality-tag prefix, the
upscale model, its 20 steps and the comma-separated tag form are the **publisher's exactly**; steps 28,
CFG 5 and hires denoise 0.35 sit **inside** its stated ranges. **Three values the publisher does not
specify at all** — `clip_skip` **-2**, `scheduler` **normal**, and the VAE/base resolution — and
`clip_skip` is the weakest provenance in the manifest: it rests on every published v17 sample generating
there, which is inference from images, not a recommendation. It is kept because changing it would make
this flow incomparable to `summon-v1`, and it is **not** described as the publisher's.

**`hires_denoise` ships at 0.35, decided 2026-09-17: it is the only value proved on this graph.**

> F39 moved `A` from 0.50
> to 0.35 because *"0.50 wins one axis by 0.014 and loses three"* — linework, **face identification** and
> **pose**. `conjure` has no identity claim and no OpenPose, so two of those columns do not apply and the
> tally is **1–1**, not 3–1. It ships 0.35 anyway, because that is the value the sheet-only flow was
> directly measured at: **+0.025 posterisation and +47% linework** over the same flow without hires.
> **The value is right and the argument is smaller**, which is exactly the shape F39 itself warns about:
> *a settled value is settled against the axes that existed when it was set.* For a flow, that becomes
> the axes **the flow has**.
>
> **And the direction differs between the two flows, which is what settles it.** For `A`, 0.35 **lost**
> posterisation (−0.004); for the sheet-only flow it **gained** (+0.025). `A`'s reasoning does not
> transfer either way — but the sheet-only flow has its own measurement, and at 0.35 it is **the only arm
> in the project to improve both style axes at once.**

**0.50 is deferred, not refused, and the test is a directory rather than a flag.** There is no dial
override: the CLI has no dial flags and `build_graph` patches from `flow.dials` alone, so a different
denoise is a different manifest, a different digest and therefore **`conjure-v2`** — which the
append-only registry then keeps forever. That is the freeze working as intended, since it is what makes
the two comparable; it is stated here so nobody discovers it mid-build.

**Its delta on this graph can be settled with no pod.** Six sheet-only renders at denoise 0.50 exist on
disk from 2026-09-09 (cfg 5, seed 20260908), seed-matched against six of the same subjects without
hires — **the delta has never been scored.** Two cautions for whoever does it: the scorer lives only at
the prototype ref and imports module paths v0.15 moved, and **the renders must be read at the
photograph's canvas rather than natively** — read natively, F35's hires result came out with the wrong
sign.

## Dial provenance

Every dial `conjure-v1` ships, against WAI-Illustrious-SDXL's own *"How to achieve optimal results"*
(`https://illustriousxl.org/wai-illustrious-sdxl`, read 2026-09-17). Recorded here rather than in
`flow.json`, because the manifest carries eight keys and JSON has no comments — D6.

Three standings, and the distinction is the point: **the publisher's** is a value the page states,
**inside the publisher's range** is a value the page bounds but does not pick, and **inference** is a
value the page does not address at all.

| dial | ships | what the publisher's page says | standing |
|---|---|---|---|
| `sampler_name` | `euler_ancestral` | *"Euler a or K_EULER_ANCESTRAL"* | **the publisher's** |
| `steps` | `28` | *"20-30"* | inside the publisher's range |
| `cfg` | `5` | *"between 5 and 7"* | inside the publisher's range, at the floor — and measured there on this graph (D6) |
| `scheduler` | `normal` | nothing | **inference** |
| `denoise` | `1.0` | nothing directly; implied by generating rather than transforming | **inference** — it is what *from noise* means, and it is what removed the blur (F24) |
| `clip_skip` | `-2` | nothing | **inference**, and the weakest provenance in the manifest: every published v17 sample generates there and none of its prose says so |
| `hires_scale` | `1.5` | *"native 1536x1536 high-resolution"* | consistent — 1.5× off a 1024 short side lands at 1536 |
| `hires_steps` | `20` | *"20 steps"* | **the publisher's** |
| `hires_denoise` | `0.35` | *"0.35~0.5"* | inside the publisher's range, at the floor — and the only value proved on this graph (D6) |

Three of the flow's settings are not dials at all, and each is **inference** rather than a
recommendation:

- **The VAE** comes from the checkpoint — graph node `1`, slot 2. The publisher's page names no
  external VAE, and nothing in this flow loads one.
- **The base resolution** comes from the run's photograph header, through `working_resolution`
  (`isekai/shared/image.py`), not from a dial. The publisher speaks only of the hires target.
- **The prompt's form and its prefix** are the publisher's exactly — *"List concepts using
  comma-separated tags"* and *"masterpiece, best quality, amazing quality, newest"* — and are carried
  under `prompt` rather than `dials`. The trailer and the negative are this project's.

**`ip_weight`, `identity_cn_strength` and `openpose_strength` are absent**, because the nodes they
patched are. A dial whose node was deleted is a declaration nothing reads.

## Verdict, measured

Written after the build, from the commands rather than from the plan. Phase 3 changes no code; it
records what the diff says, and the diff is this change's subject.

### The production surface — empty, as the verdict predicted (task 3.1)

```
$ git diff --stat v0.16.0..HEAD -- isekai/ scripts/ Dockerfile start.sh infra/ \
    Makefile pyproject.toml .github/ openspec/specs/
$
```

No output. **`conjure-v1` renders through v0.16's code unchanged** — `load_flow`'s eight checks,
`build_graph`'s four required roles and seven guarded ones, the `inputs`-gated upload, and the
unconditional `photo_resolution` all accepted a second, sheet-only flow with nothing added to them.
The two claims never exercised by a second flow — `REQUIRED_NODES` and `TRANSFERRED_INPUTS` — were
both exercised here and both held: seven declared roles satisfied the four required, and `photo`
absent from both sides passed as the sheet-only case.

### The test surface (task 3.2)

```
$ git diff --stat v0.16.0..HEAD -- tests/
 tests/test_flow.py | 6 +++++-
 1 file changed, 5 insertions(+), 1 deletion(-)
$
```

**One module, as predicted — and six lines, where the verdict above says two.** Recorded rather than
reconciled. The gap is entirely accounted for, and it is not a discovery about v0.16:

| the diff's lines | what they are | bucket |
|---|---|---|
| `+"conjure-v1": "3869…"` | the pin | the designed pin |
| `+` three comment lines above it | the comment `tasks.md` 2.8 required the pin to carry | the designed pin |
| `-assert tracked_flows() == ["summon-v1"]` / `+assert tracked_flows()` | the widened vacuity guard | the undesigned assumption |

**Two *edits*, six *lines*.** The verdict counted edits and the acceptance row counted lines, and the
four extra lines are a comment the same `tasks.md` mandated in task 2.8. **The verdict `feasible`
stands and the edit set is what D1 says it is**; the prediction that was wrong is *"two lines"*, and
what makes it wrong is an instruction in this change's own plan rather than anything about v0.16's
completeness. Stated here so a later reader is not left reconciling `6` against `2` alone.

### The three buckets, against what landed

1. **The flow — `flows/conjure-v1/`, five files, 646 lines.** This is the change's product and it is
   entirely inside its own directory. Nothing was added to a shared module to make it load, render or
   score, including `CURATED` (`isekai/shared/vocabulary.py`), which D4 named as the standing risk:
   all five new schema fields proved reachable by the suffix or containment pass, checked in task 2.6.
2. **The designed pin — `PINNED["conjure-v1"]` and its comment, four lines.** *The freeze working.*
   The pin list is what makes adding or removing a flow deliberate; a version that reported this as an
   incompleteness would be arguing to delete the mechanism (D1).
3. **The undesigned assumption — `test_every_tracked_flow_parses`'s opening assertion, two lines.**
   *The one defect this change repaired*, landed first and on its own commit so that it reads as a
   defect rather than as part of the flow. It was a vacuity guard written as a registry census; every
   other test in the module already iterated `tracked_flows()`.

**No fourth bucket appeared.** Nothing outside `flows/`, `tests/test_flow.py`, `CHANGELOG.md` and this
change's own directory was touched — task 3.1's empty output is that claim, and task 3.2's single
module is its bound.

**So v0.16 was complete on the claim this version tested.** Adding a flow cost a directory plus one
deliberate pin. The second line in `tests/test_flow.py` was an incidental single-flow assumption that
only a second flow could reveal, which is the thing this version existed to find.

### Two findings that the measurement does not cover

Both are recorded in `## Risks / Trade-offs` with triggers, and neither is visible in a diff:

- **Two flows in one invocation are not seed-matched** — `seeds_for` draws per directory from one
  shared `Random`. The acceptance run passes `--seed` explicitly for exactly this reason.
- **`generate` renders in on-disk order**, so `conjure-v1` goes before `summon-v1` regardless of
  `--flow` order.

Both block the evaluation version and travel with it, which is the version that needs them.

## Risks / Trade-offs

- **The claim is about a diff, and nothing in the gate reads a diff.** → Two acceptance rows are
  `git diff --stat v0.16.0..HEAD` invocations, run by a human and recorded in `tasks.md`.
- **The two-flow path has never been executed by any test.** `tests/test_pipeline_cli.py:57-71`
  `_two_flows` has one consumer, which stops at `_flows_for`; the multi-flow loops, `prepare`'s
  multi-entry return and `report` over two flows are untested end to end. → The metered run is the first
  execution, and it is on the acceptance rather than assumed.
- **Two flows in one invocation draw different seeds.** `seeds_for` draws per `(run, flow, version)`
  directory from one shared `Random` (`generate.py:389-393`, `wiring.py:58`). → **`--seed` is passed
  explicitly in the acceptance and is not optional.** The fix is a seed policy and travels with the
  evaluation version, which is what needs it.
- **`generate` renders in on-disk order, so `conjure-v1` goes first regardless of argument order**
  (`generate.py:208`, `:140`). → Harmless for two flows; recorded, not fixed.
- **A 21-field prompt is ~30% longer than a 16-field one**, and every tag dilutes every other. → Nothing
  measures this for `conjure` and nothing will; stated rather than discovered.
- **`CURATED` is shared by every flow and no flow can declare it.** → Not triggered here, because all
  five new fields are cascade-reachable. Recorded as the first hole in *a flow shares nothing*.

## Migration Plan

None. The change is additive: one new directory and two widened test lines. Rollback is deleting the
directory and reverting the two lines — and the registry is append-only, so a flow that has rendered is
never deleted afterwards.

## Open Questions

None. Nine were opened and closed before this change was cut.
