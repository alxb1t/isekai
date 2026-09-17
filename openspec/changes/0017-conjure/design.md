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
produces a sheet that looks more complete than it is. *Deferred:* **`eye_shape`** — its four tags
(`tsurime`, `tareme`, `jitome`, `sanpaku`) are reachable only through a curated span, and `CURATED`
(`vocabulary.py:77`) is a module constant shared by every flow that no manifest can declare. Four tags is
the wrong price for the first edit to shared routing.

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
