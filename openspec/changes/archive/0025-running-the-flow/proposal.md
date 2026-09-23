---
version: v0.22.3
---

## Why

**All three items in this change were found by driving the CLI, not by reading the repository.** It is the
first version in this stabilization whose scope came from use rather than from a backlog, and each item
turned out to be something other than what it first looked like.

**① The negative prompt carries two tags that fight the product.** `censor, nsfw` sit in a negative whose
job — per the base model's publisher — is quality. The operator measured the difference by eye across real
renders: removing them produces better images. The positive prompt is what decides content; the negative
should say nothing about it.

**② Two flow files disagree about the negative, and only one is read.** `flow.json` carries
`lens flare, light particles, dust`; `graph.json` carries `worst detail` and neither of the other three.
`generate.py:336` patches `flow.json`'s fragment over `graph.json`'s node on every render, so **the
`graph.json` string has never reached an image.** The drift went unnoticed because nothing reads it — the
same class as the stale `filename_prefix` this repository recorded at `v0.22 review/R6`.

**③ The gate was uninstalling a dependency the pipeline needs.** The operator reported being asked to run
`uv sync --extra tagging` repeatedly. That is a once-per-checkout command, so something was removing the
packages, and the environment showed it: `fastapi` present, `onnxruntime`, `numpy` and `Pillow` absent.
**`uv sync` makes the environment match exactly what it is told, and removes extras it is not told
about** — and the gate's first command is `uv sync --locked`, with no `--extra`. The local tagger runs on
every `caption` for every flow, which makes *"optional"* false in the plainest sense.

## What changes

**Three phases.** The first is one edit and carries the description the operator asked for. The second and
third are one act split in two: moving the dependencies makes five sentences false, and the file they are
densest in is also the file that should teach someone how to run this.

1. **The negative prompt becomes quality-only.** `censor, nsfw` leaves both flows' `flow.json`.
   `graph.json`'s negative becomes an empty string — **a deletion rather than a sync**, so there is one
   source of truth instead of two that happen to agree today. Two `PINNED` digests are recomputed.

2. **`tagging` and `ui` become required dependencies, pinned exactly.** `eval` stays optional — it is the
   scorer, not the pipeline. `dependencies = []` goes, and the `-S` guard that held it is **narrowed
   rather than deleted**.

3. **`## Quickstart` is rewritten as the guide to running a flow**, photo to image, pod included — with
   the step where it stops being free marked so it cannot be missed.

## Impact

> ⚠️ **This edits a frozen flow, and that is the second exception ever taken to the rule.** The first was
> declared non-reusable in writing: `tests/test_flow.py`'s failure message says a changed prompt fragment
> *"means a new flow identifier"*, and the comment above `PINNED` says *"a test message that explains how
> to evade itself is one that gets evaded."*
>
> **The operator took the exception with the rule put to him**, and it is recorded here rather than
> arriving as a quiet re-pin. **What makes it defensible is exactly what makes it an exception**: the
> reason for the edit is that the output changed, which is the thing the freeze exists to make visible.
> `design.md` D2 carries the argument and the conditions under which it must not be taken again.

**What the edit does not cost.** `manifest_digest` has exactly one consumer — `tests/test_flow.py`'s
`PINNED`. No run artifact records it and nothing on disk validates against it, so **no existing run is
orphaned**. Orphaning follows a changed flow *id*, which this change does not do.

**`dependencies = []` is retired, and it is load-bearing in five places** — `pyproject.toml:5`,
`README.md`, `isekai/README.md`, `CLAUDE.md:275`, and **`docs/arc/modules.md:75`, written three commits
ago by `v0.22.2`** as a rule the module graph holds. The narrower claim survives and is what the
architecture actually relies on: **the entry point imports no third-party package at module scope**, which
is why `isekai show` works on a checkout that has provisioned nothing.

**One metered phase.** `v0.22.1` and `v0.22.2` both cost nothing; this one needs a pod session, because a
negative prompt is judged by looking at what it renders. Budget one sitting, both flows.

**A small spec delta** — one modified requirement in `image-generation`, because a flow's prompt fragments
are now described in a way that admits an empty negative on the graph side.
