# Design — 0025 running the flow

**Verdict: `feasible`.** Every decision below was settled against a body read at `main` `7fb3d0b`, after
`v0.22.2` was tagged and `0024-the-documents` archived. **Two of the three asks changed shape under
measurement**, and each is recorded at the decision it replaces.

## Context

The first version in this stabilization whose scope came from running the pipeline rather than reading it.
The operator drove the CLI on real photographs and found three things: the negative prompt was fighting
the product, the environment kept losing the tagger, and the README did not walk him through a run.

None of the three is what it first looked like.

---

## D1 — The negative prompt: one file is read, the other never was

> **Overturned premise ①.** The ask was *"add `lens flare, light particles, dust` and remove
> `censor, nsfw`, in `graph.json` and `flow.json`."* Measured at `7fb3d0b`:
>
> ```
> flow.json     "bad quality, worst quality, sketch, censor, nsfw, lens flare, light particles, dust"
>                                             ▲ remove        ▲ already present, both flows
> graph.json    "bad quality, worst quality, worst detail, sketch, censor, nsfw"
>                                            ▲ only here            ▲ never reaches a render
> ```
>
> **Half the ask was already done, and the other half targeted a string that has never reached an image.**

`generate.py:336` is `patch("negative", text=prompt["negative"])`, and the prompt artifact is assembled
from **`flow.json`**'s fragment. `graph.json`'s node text is overwritten on every render.

**The two have already drifted** — `worst detail` in one, the three tags in the other — and nothing caught
it, because nothing reads the second. This is the class `v0.22 review/R6` recorded for a stale
`filename_prefix`: an inert string in a tracked artifact, right until someone reads it and believes it.

**So `graph.json`'s negative is emptied rather than synchronised.** Two strings that agree today are two
strings that will disagree later. One source of truth removes the question.

⚠️ **The empty string is not a default to fall back on.** If a future path renders without patching the
negative, it renders with none — which is visible in the output rather than silently wrong. That is the
better failure, and it is the reason to prefer empty over a copy.

## D2 — The exception to flow immutability, and the conditions on it

This change edits two frozen flows and re-pins. **That is the second exception ever taken, and the first
was declared non-reusable in writing** — the comment above `PINNED` reads *"The failure message below
gains no 'unless' clause — a test message that explains how to evade itself is one that gets evaded."*

**The operator took it with the rule put to him.** What is recorded here is the argument, so that the next
version asking for the same thing has to meet the same bar rather than cite this one as precedent.

**Why it is defensible here.** The reason for the edit is that the renders are better — a claim that the
output changed. That is precisely what the freeze exists to make visible, and it is being made visible:
in the proposal, in the spec, and in the phase's own commit. A freeze that forbids a recorded, argued
change is not protecting anything; it is just making the change happen somewhere less visible.

**Why the requirement had to move.** Its heading said *"changing any file in it creates a new flow"* and
its SHALL said alteration fails the suite *"rather than changing an existing flow's behaviour."* This
change changes an existing flow's behaviour. **Leaving the requirement as written while doing otherwise
would be the repository lying about itself** — the exact defect `v0.22.2` spent seven phases removing. The
modified requirement keeps the mechanism and narrows the claim to what is true: **nothing changes
silently.**

**The condition that survives, and it is the load-bearing half.** A *divergence* still costs a new
identifier. Two flows exist to be compared over one cohort, and that only works if an identifier means one
configuration. The test is not *did a file change* but *is the old configuration still wanted*:

| | |
|---|---|
| both configurations must exist — a variant, another base, a second generation | **new flow id.** Re-pinning would destroy the comparison |
| the old configuration is abandoned | **re-pin**, and state what moved |

**What re-pinning costs, recorded rather than waved past.** Runs rendered before the edit were produced by
bytes that no longer exist, and **nothing on disk says which side of the edit a run falls on** —
`manifest_digest` has one consumer and it is the suite.

> **A cost I priced wrong at the grilling, corrected here.** I warned that editing the flows would orphan
> every existing run. **False.** No run artifact records `manifest_digest`; orphaning follows a changed
> flow **id**, which this change does not do. The real cost is two lines, a rule, and the run-provenance
> gap above.

## D3 — The dependencies: the gate was removing them

> **Overturned premise ②.** The ask was *"I don't want to run `uv sync --extra tagging` each time."* That
> is a once-per-checkout command, so the interesting question was what removed the packages. The
> environment answered it:
>
> ```
> .venv/    fastapi ✓     onnxruntime ✗     numpy ✗     Pillow ✗
> ```
>
> **`uv sync` makes the environment match exactly what it is told and removes extras it is not told
> about.** The gate's first command is `uv sync --locked`, with no `--extra`. **The gate was uninstalling
> the tagger.**

That is the mechanism, and it matters because the symptom looked like a missing install rather than a
removal — which is why it recurred.

**Required, not a default extra.** `[tool.uv] default-extras` would fix the symptom and keep
`dependencies = []` true, but only inside a test: every real checkout would carry 2 GB of onnxruntime
while the manifest said it needed nothing. **The local tagger runs on every `caption` for every flow** —
`tagging:independence:the-local-tagger-needs-no-manifest-key` — so *"optional"* is false in the plainest
sense, and a config that quietly installs it anyway is less honest than a manifest that declares it.

`ui` is the weaker case — six of seven verbs work without it — and it moves on the operator's decision
that the surface is part of running a flow rather than an add-on to it. `eval` stays optional: it is the
scorer, and an evaluator is not a way to render.

**Pinned exactly**, at what `uv.lock` resolves at `7fb3d0b`: `onnxruntime==1.29.0`, `numpy==2.5.3`,
`Pillow==12.3.0`, `fastapi==0.141.1`, `uvicorn==0.53.0`. The lock pins *this* checkout; the manifest is
what a second machine resolves against, and the tagger's output feeds every sheet.

⚠️ **onnxruntime wheels are platform-specific.** A version resolved on darwin/arm64 may not exist for
CI's runner. If `uv sync --locked` goes red there, that is the cause — and the honest repair is a floor in
the manifest with the lock doing the pinning, not a weakened gate.

## D4 — The `-S` guard is narrowed, not deleted

`dependencies = []` is held by three tests in `tests/test_pipeline_cli.py`: two that import under
`python -S` (`:198`, `:205`) and one at `:214` whose only job is proving the guard would catch a real
third-party import.

**What stays true is the claim the architecture actually relies on**: the **entry point** imports no
third-party package at module scope. `wd14.py`'s `onnxruntime`, `numpy` and `Pillow` imports are
function-local by design, and `interface/ui/__init__.py:45` keeps FastAPI off `python -m isekai`'s import
graph the same way. **That is why `isekai show` works on a checkout that has provisioned nothing**, and it
is worth more than the broader claim it replaces.

**Deleting the guard instead would remove the only thing stopping a module-scope import from appearing in
the entry point's graph**, which is a live hazard the moment the packages are installed by default —
because then nothing fails when someone adds one.

## D5 — `## Quickstart` is rewritten, not joined

**Phase 3 is required by phase 2, not adjacent to it.** Moving the dependencies makes five sentences
false: `README.md:110`, `:164`, `:166`, `CLAUDE.md:275`, and **`docs/arc/modules.md:75`** — written three
commits ago by `v0.22.2` as a rule the module graph holds.

> ⚠️ **This is the third time in three versions that a stabilization release has written prose the next
> one falsifies.** `v0.22.1` left `CLAUDE.md` calling a fixed `Cmd+Z` *"a known live violation"*;
> `v0.22.2` wrote the stdlib rule into a new file this change retires. **It is the cost of splitting
> prose from code, and it is cheaper than the alternative** — but it means a documentation version must
> ship close behind the code version it describes, not two releases later.

**A guide already exists** — `README.md:92-200`. It walks every verb with real commands. What it lacks is
scannability: three paragraphs of explanation sit between step 1's commands and step 2.

**Rewritten in place rather than joined by a second guide.** Two guides to one thing is the failure this
stabilization has spent three versions unwinding, and the newer copy always wins attention while the older
one rots.

**It covers the whole path including the pod**, because that is what *"run a flow"* means — but the step
where it stops being free is marked so it cannot be missed. Everything through `approve` is local and
costs nothing; `generate` needs a pod, a tunnel, credentials and real money. `CLAUDE.md`'s spend guardrail
wants that boundary visible, and a guide that hides it is worse than no guide.

---

## Open questions

**None blocking.** One is recorded:

**Nothing on disk says which side of a re-pin a run falls on.** D2 names this as the cost of re-pinning.
A run's provenance records the graph digest but not the flow's directory digest, so a cohort spanning the
edit cannot be split by it after the fact. **Filed rather than fixed** — it is a run-provenance change,
and this version is three small things the operator found by using the tool.
