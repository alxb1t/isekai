# The data flow

A photograph goes in and an anime image of the same person comes out. Between
them are the staged verbs, each one a command an operator runs, each one writing
numbered artifacts into a run directory that another verb reads.

**Nothing here is implicit.** No stage reads another's output by calling it; each
is handed a path inside a run and hands back a numbered file. No stage imports
another. That is what makes a run resumable from disk and a failure survivable by
its neighbours.

## The verbs

```
  photograph
      │
      ▼
  ① caption ──▶ captions/  prose, for a human to read
              ──▶ wd14/      scored tags, from a local ONNX session
              ──▶ tags/      raw tags, from the hosted model
      │
      ▼
  ② sheet  ── reads wd14/ ──▶ sheets/   the flow's fields, filled
      │
      ▼
  ③ review ── reads sheets/ ──▶ review/NNN.draft.json
     approve ── reads the draft ──▶ review/NNN.approved.json
      │           (or `ui`, the same stage in a browser)
      ▼
  ④ generate ── reads the approved sheet ──▶ prompts/   assembled, offline
              ── then renders each prompt ──▶ outputs/   on a rented GPU
```

Beside them, `show` reads a run's artifacts, versions and producers and decides
nothing — it writes no file and reaches no model.

Every stage verb takes `--flow`, required and repeatable, because the flow
supplies the briefing a stage reads, the schema it fills against and the
directory it writes into. `show` and `ui`, which are not stage verbs, each
differ, and in different directions: `show` takes no `--flow` at all, because it
reports every flow the run already holds and so names none by design; `ui`'s is
required and exactly one, because the surface shows a single schema's fields in a
fixed order and a second flow would be a second page.

## What a reader needs first

**`caption` writes prose, the local tag list and the hosted tag list in one
invocation, in that order.** The batch loop catches a refusal per *input*, not per
stage, so whatever fails takes the artifacts behind it in that input with it.

The order was chosen to isolate failures when the sheet was built from prose. The
sheet reads the WD14 list now, so a prose refusal — Ollama unreachable — stops the
sheet's input too ([D1](decisions.md#d1--stage--is-one-verb)).

The local WD14 tagger goes second because it is deterministic and fails only on a
missing or corrupt file. The hosted tagger goes last because it is the tagger with
a port, a timeout and a retry budget. It is still a single verb: there is no
`isekai tags`.

**The sheet is built from the WD14 list, not from the prose.** The prose is a
reading aid with no machine consumer downstream. Which is why a missing *hosted*
tag list is an absent aid and never a refusal — its own call failed after the
prose and the WD14 list were written — while a missing *local* tag list is a
refusal naming `caption`. An all-empty sheet is legal and therefore silent, and
that is the failure mode this arrangement keeps paying for.

Neither tag list is narrowed on the way out: no canonicalisation, no vocabulary
filtering, no re-ordering but by confidence. Narrowing is stage ②'s job, and
seeing behind it is what these artifacts are for.

## The run directory

```
  runs/<input-id>/<flow-id>/
      captions/   ① prose
      wd14/       ① the local tagger's scored list
      tags/       ① the hosted tagger's raw list
      sheets/     ② the flow's fields, filled from wd14/
      review/     ③ NNN.draft.json, then NNN.approved.json
      prompts/    ④ the assembled prompt, written before any endpoint is acquired
      outputs/    ④ the rendered image
```

**Input above, flow below.** Above the split is what every flow shares, and the
only thing every flow shares is the input itself — the run holds a *copy of the
photograph*, which is what makes it reconstructable from disk. Below the split is
one subtree per flow, so adding a flow adds a subtree and no flow can read
another's artifacts. Nesting stage-first would scatter a new flow across every
stage directory instead.

The names above are `run.py`'s, not each stage's: the run owns the layout. Inside
a directory an artifact is `NNN.json`, with `NNN.draft.json` and
`NNN.approved.json` where a stage has that concept — `approved` is a filename
label, not a directory of its own.

## How identity is carried

Identity is carried by mechanisms, not by a sentence someone types into a prompt. Each axis is a leg
of the graph, and each leg's strength is a **dial the flow's manifest declares** — the values live in
`flows/<id>/flow.json` and are not repeated here, because a value written twice is a value that can
disagree with itself.

| axis | carried by | its dials |
|---|---|---|
| Face | InstantID + InsightFace — face embedding and keypoints | `ip_weight`, `identity_cn_strength` |
| Composition | **from noise** — `EmptyLatentImage` at full `denoise` | — |
| Pose | a ControlNet on OpenPose, off `DWPreprocessor` | `openpose_strength` |
| Detail | a hires pass — `RealESRGAN_x4plus_anime_6B` upscale, then a second sampler | `hires_scale`, `hires_denoise` |
| Register | the prompts, **assembled per run** from an approved sheet | the manifest's prefix, trailer and negative |

**Composition comes from noise, and that is settled.** Taking the photograph out of the latent is what
removed the blur; img2img is a closed avenue here.

**Register is the one a human touches.** The manifest carries a prefix, a trailer and the negative;
the subject's own canonical tags come from the sheet a human corrected. That correction is the single
largest measured gain in this pipeline, which is why only an approved artifact is ever rendered.

Before any node reads the photograph, an `ImageScale` node puts it on one working resolution computed
by `isekai/shared/image.py` from the photograph's own JPEG or PNG header: aspect preserved, short side
fixed, both dimensions on the grid the sampler needs, and refused past the aspect limit rather than
clamped. No node available here can derive that. A header the reader cannot parse refuses *that
photograph*, rather than defaulting or ending the batch. `clip_skip` is declared in the manifest
rather than committed to the graph file, because the published samples for this base all generate at
a clip skip their prose never states.

**`models/wd14/` is one artifact split in two**, and both halves are pinned in
`scripts/vocabulary.json`. Row N of `selected_tags.csv` names output neuron N of `model.onnx`, so a
pair from mismatched revisions mislabels every tag — silently, because the vector still has the right
length and every name in it is still a real tag. Both digests are verified before the first inference.
A WD14 artifact records `pinned: true`, and a sheet built from it carries that across; the reader and
the hosted tagger record `false`, and `python -m isekai show` marks theirs *unpinned*.

## What costs money, and what does not

Everything before `generate` is free and local. Prompt assembly happens for the
whole batch *before* an endpoint is acquired, so a malformed sheet costs nothing
rather than a boot. Only the render reaches the rented GPU.

`caption` reaches a model too, but a local one: Ollama over HTTP to this machine.
It costs a warm model and no money.
