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

Every verb takes `--flow`, required and repeatable, because the flow supplies the
briefing a stage reads, the schema it fills against and the directory it writes
into. `ui`'s `--flow` is the exception: required and exactly one, because the
surface shows a single schema's fields in a fixed order and a second flow would
be a second page.

## What a reader needs first

**`caption` writes prose, the local tag list and the hosted tag list in one
invocation, in that order — and the order is the failure isolation.** The batch
loop catches a refusal per *input*, not per stage, so whatever fails takes the
artifacts behind it in that input with it. Prose goes first because it is what a
human reads before anything else. The local WD14 tagger goes second because it is
deterministic and fails only on a missing or corrupt file. The hosted tagger goes
last because it is the one with a port, a timeout and a retry budget. A failure
in prose still costs the artifacts behind it — that is the trade this ordering
was chosen for, not an oversight in it. It is still a single verb: there is no
`isekai tags`.

**The sheet is built from the WD14 list, not from the prose.** The prose is a
reading aid with no machine consumer downstream. Which is why a missing *hosted*
tag list is an absent aid and never a refusal — the model may simply not be
running — while a missing *local* tag list is a refusal naming `caption`. An
all-empty sheet is legal and therefore silent, and that is the failure mode this
arrangement keeps paying for.

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

## What costs money, and what does not

Everything before `generate` is free and local. Prompt assembly happens for the
whole batch *before* an endpoint is acquired, so a malformed sheet costs nothing
rather than a boot. Only the render reaches the rented GPU.

`caption` reaches a model too, but a local one: Ollama over HTTP to this machine.
It costs a warm model and no money.
