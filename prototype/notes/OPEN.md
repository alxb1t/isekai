# OPEN — the questions that must be settled before the architecture is written

**Round 5's first task (N42), opened and CLOSED 2026-09-13.** Eleven questions, each one an unknown that
would change the design if it were answered late. **Twenty-two laws came out of them; two defects were
found; one claim in the record was corrected.** The summary is at the end of this file. They are worked **one at a time**, and a question is closed by a
decision recorded here — with the evidence it was decided on and what it now constrains — not by being
agreed in a thread.

> **This file is the gate on N43–N48.** `PRODUCT.md`, `MIGRATION.md` and `ROADMAP.md` are written
> against the decisions below, and each of them cites the question number that licenses it.

**A question is never closed by preference alone.** Where evidence exists on disk it is cited; where it
does not, the decision says so plainly and names what would falsify it. That is the same discipline
`FINDINGS.md` is under, applied to design rather than to measurement.

---

## The register

| # | question | status |
|---|---|---|
| **Q1** | the stdlib-only rule meets a five-layer pipeline | **CLOSED** 2026-09-13 — shape B, two laws |
| **Q2** | "one path, never two" meets a product that emits many images | **CLOSED** 2026-09-13 — L3, L4, layer renamed |
| **Q3** | the pipeline spans two machines — where does the seam go | **CLOSED** 2026-09-13 — L5, L6, L7 |
| **Q4** | the human pause makes the orchestrator stateful | **CLOSED** 2026-09-13 — L11–L14 |
| **Q10** | the flow contract — what a flow requires, and where it is declared | **CLOSED** 2026-09-13 — L8, L9, L10 |
| **Q5** | `main`'s evaluator asks a different question from the prototype's | **CLOSED** 2026-09-13 — L15, L16; **amended during N43** |
| **Q6** | six capabilities are specified on `main`; the prototype rewrites two | **CLOSED** 2026-09-13 — L17, L18 |
| **Q7** | licences — what this product becomes | **CLOSED** 2026-09-13 — L19; P7 parked |
| **Q8** | where the weights live, and what pins them | **CLOSED** 2026-09-13 — L20–L22; one defect |
| **Q9** | the product's actual input — a phone snapshot — has never been tested | **CLOSED** 2026-09-13 — measurement in flight |
| **Q11** | how do we learn a better version of a pinned model exists | **CLOSED** 2026-09-13 — schema now, watcher as P8 |

---

## Q1 · The stdlib-only rule meets a five-layer pipeline

**Status: CLOSED 2026-09-13.** Shape **B**, two front ends over one orchestrator, laws **L1** and **L2**.

### The rule, and how it is actually enforced

`../CLAUDE.md`: *"The runtime is stdlib-only — the ComfyUI transport is `urllib`, and nothing in
`convert.py`'s import graph may need a wheel."*

It is not an aspiration. Verified on disk 2026-09-13:

- `pyproject.toml` declares `dependencies = []`.
- `tests/test_evaluate.py:750` imports `convert` in a subprocess under **`python -S`**, which leaves no
  `site-packages` on `sys.path` at all.
- `tests/test_evaluate.py:769` is the falsifiability guard on that guard: it asserts `-S` really does
  refuse `import pytest`, so the test above cannot pass for the wrong reason.

### Two escape hatches already exist in-tree, and they are different from each other

| posture | who uses it | how it works |
|---|---|---|
| **off the import graph** | `provision.py` | never imported by `convert.py`; free to do anything |
| **on the graph, stdlib source, lazy third-party** | `evaluate.py` + `eval_backends.py` | every model behind a `Protocol`; `_require()` does `import_module` at call time and raises `Refusal` naming `uv sync --extra eval` if absent. CI never installs the extra |

### The tension, stated precisely

The rule binds an **import graph**, and a facade exists to admit implementations nobody has chosen yet.
Four of the five layers are stdlib by nature — they are HTTP clients to a local server:

| layer | what it needs | posture |
|---|---|---|
| ① VLM | HTTP to Ollama | `urllib` — **pure stdlib** |
| ② LLM | HTTP to Ollama | `urllib` — **pure stdlib** |
| ③ REVIEW | a UI | **off the graph**, its own entry point |
| ④ GENERATION | HTTP to ComfyUI | `urllib` — **already is**, via `ComfyTransport` |
| ⑤ EVAL | torch, onnxruntime | **lazy import behind a `Protocol`** — the `eval_backends` posture |

So the rule survives. **What needed deciding is what it constrains about a facade** — because a VLM
facade whose second implementation is a `transformers` pipeline breaks the rule on the day someone
writes it, unless the contract forbids it in advance.

### Decided 2026-09-13 — shape **B**, amended by the operator

**`convert.py` stays the one advertised surface and also grows per-stage subcommands.** And the
operator's amendment, which is the part that matters: **the UI is a second front end, not a stage.** It
uploads the photograph, monitors the run, hosts the review step, and triggers the orchestrator.

```
   CLI  convert.py photo.jpg        UI  upload · monitor · review · trigger
   stdlib, on the guarded graph         off the graph — free to need wheels
        │                                        │
        └────────────────┬───────────────────────┘
                         ▼
                   ORCHESTRATOR          stdlib source, lazy third-party only
                         │               imports no front end, ever
          ┌────┬─────────┼─────────┬────────┐
         ①    ②         ③        ④       ⑤
                         ▼
                 runs/<photo-id>/     ← the state both front ends read
```

**Two laws come out of it. L2 is what makes the UI free.**

> **L1 · A facade may admit a wheel-needing implementation only through the `eval_backends` posture** —
> stdlib source, a `Protocol`, `import_module` at call time, and a `Refusal` naming the extra. A facade
> that cannot meet that lives off `convert.py`'s import graph and gets its own entry point.
>
> **L2 · The import-graph rule is directional, and that is the whole reason the UI can be anything.**
> A front end may import the orchestrator; **the orchestrator may never import a front end.** So the UI
> is free to use a web framework, a TUI toolkit or nothing at all, and `convert.py`'s `-S` test stays
> green regardless — it walks a graph the UI is not on.

**L1 is the only genuinely new rule in Q1.** Everything else is an existing rule applied, or an existing
in-tree posture named.

### Three consequences, handed forward rather than decided here

1. **Status must be progressive, not terminal.** *"Monitor the steps"* means the UI reads the run while
   a stage is still running. Terminal artifacts alone cannot express *"stage ④ is 6 renders into 10"*,
   so the run directory carries a status the orchestrator updates as it goes. **→ Q4, and `PRODUCT.md`
   §run-directory (N44).**
2. **The UI should invoke the orchestrator the same way the CLI does** — out of process — so there is
   exactly one way the pipeline runs and the UI is not a privileged caller. In-process is an
   optimisation available later, and taking it early would make the UI a second path in the one place
   the repository's rules care most. **→ Q2, Q4.**
3. **A layer whose best implementation has no server** — a VLM available only as a `transformers`
   checkpoint — lands on L1's posture (b), not on a new exception. Named so it is not re-litigated.

### What would falsify this

**If the review UI turns out to need to *drive* a stage rather than trigger a run** — re-running ② with
a different temperature from a button, say — then the UI is importing layer internals and L2's direction
is not enough on its own. The answer would be that the orchestrator exposes those as its own commands,
not that the UI reaches past it.

---
## Q2 · "One path, never two" meets a product that emits many images

**Status: CLOSED 2026-09-13.** The rule is **amended**, deliberately, and the amendment is stated below
as **L3**. Flow variation is settled by **L4**. The layer is **renamed**.

### The rule as it stood, and what it was actually for

`../CLAUDE.md`: *"There is one path. A version may replace it; it may not add a second. Four selectable
models were how the product was **found**; carrying three dead ones was the cost of not deciding."*

**Its purpose is not output count. It is: do not carry undecided alternatives.** That distinction is
what the rest of this decision turns on.

### Half 1 — flows `A` and `D` do not engage the rule

Three facts, verified on disk 2026-09-13:

- **`D` is `A`'s graph with two nodes deleted.** `prototype/ablation.py:100` drops InstantID and OpenPose
  from the same base graph; `prototype/real_photo.py:165` is `build(base, flow)` over one `GRAPH` file.
  The prototype already made this choice and recorded why: *"keeping them makes this arm one deletion
  from the others rather than a different graph."*
- **Both are produced every run.** Neither is selectable-instead-of, neither is dead.
- **They diverge inside stage ④, behind its facade.** Stages ①②③⑤ see one path.

**One concrete blocker, and it is a spec edit rather than a code tweak.** `isekai/pipeline.py`'s
provenance record calls `find_node(class_type="ApplyInstantIDAdvanced")` under an **exactly-one**
contract — and `D`'s graph has deleted that node. `ablation.py` says outright that it could not use
`pipeline.run` for this reason, and refused to weaken the contract for a prototype. **The version that
lands `D` must change that contract.** → `MIGRATION.md` (N47).

### Half 2 — the expansion, and it is much larger than two flows

The operator's own ideas note (his notebook, outside this repository) carries **eleven parked paths, and
seven of them are generation flows**: portal, photoreal fantasy, cartoon, pixel-art, grade, cosplay,
region passes. **Two is not the number. The layer is a registry.**

### Decided — L3 replaces the one-path bullet

> **L3 · There is one pipeline. Each layer is a facade with a selector, and a selectable implementation
> is one that has been measured.** An implementation enters a facade's registry by passing a prototype
> round and the evaluation bar; it is removed by the version that retires it. **Generation flows and
> evaluation methods may be selected in plurality** — many flows means many images, many methods means a
> bracketed number. **Reading layers select exactly one per run.**

**Why this is not a weakening.** The original rule existed because four selectable models were carried
and three were dead. **L3's entry gate makes a dead implementation impossible by construction** — it was
the operator's own condition, stated before the law was drafted: *"each flow before hitting the main
branch should go to a prototype session testing how it works and passing the evaluation, and after that
we decide if we want to add the flow."* That is a stronger guarantee than "one path" ever was, because
"one" was a count and this is a standard.

| layer | the selector picks | plurality | what many means |
|---|---|:-:|---|
| ① VLM | an implementation | no | same artifact, different means |
| ② LLM | an implementation | no | same artifact, different means |
| ③ REVIEW | a front end | no | one human, one sheet |
| ④ GENERATION | a **flow** | **yes** | many output images — a product feature |
| ⑤ EVALUATION | an encoder / method | **yes** | a bracketed number — F46's `9/17 … 14/17` |

### Decided — L4, variation is seed-only

> **L4 · A variation draws a new sampler seed and changes no dial.** A flow's dials *are* the flow:
> settled against its publisher's own recommendations and confirmed by measurement (F25, F26, F35, F39).
> Jittering them does not produce a variant of the flow, it produces an untested flow — which L3
> forbids from being selectable.

**Most of this already exists on `main` and is directly reusable.** `--variations` and `--seed` are CLI
flags today, and **`isekai/mutate.py`'s `draw_seed` is already the seed-only operation**, deliberately
separate from `mutate`'s six-dial jitter. L4 says the product calls `draw_seed` and not `mutate`.
**`mutate` therefore becomes dead code under L4** unless a flow opts into dial jitter — and 44 scenarios
of `workflow-mutation` are specified on `main` against it. → Q6, `MIGRATION.md` (N47).

### Decided — the layer is renamed

**"Diffusion" is already wrong and will be visibly wrong the day the second flow lands.** The grade path
performs no redraw at all; the portal path is segmentation and compositing. The layer is
**④ GENERATE — the image-generation layer**, capability `image-generation`, and *flow* is the word for
what it selects.

### The facade's shape, as agreed

```
  generate(photo, sheet, [
      Request(flow="A", count=1),        # default: one flow, one image
      Request(flow="D", count=3),        # one flow, three seeds, same dials
  ]) ──▶ [Output(flow, seed, path, provenance), ...]
```

### One consequence handed forward, and it is not small

**The evaluation bar is per-flow, so a flow's definition must carry its own bar.** The ideas note says
of the pixel-art path that *"identity weakens by design"*, and the grade path preserves identity
trivially because nothing is redrawn. A single identity threshold across the registry would reject the
first and rubber-stamp the second. **A flow enters the registry with its bar, or L3's gate is not
checkable.** → Q5, and `PRODUCT.md` §evaluation (N46).

---
## Q3 · The pipeline spans two machines — where does the seam go

**Status: CLOSED 2026-09-13.** Session-scoped facade (**L5**), batch by default (**L6**),
provider-agnostic by seam and not by registry (**L7**).

### The shape, and why the cost sits exactly on the seam

```
  ① VLM      ② LLM      ③ REVIEW     ④ GENERATE     ⑤ EVAL
  local      local      local        ┏━ rented ━┓   local
  Ollama     Ollama     human        ┃ ComfyUI  ┃   torch/onnx
                                     ┗━━━━━━━━━━┛
                                      SSH tunnel → localhost:8188
                                      (the HTTP proxy is 1010-blocked · F33)
```

**One seam, and the money is on it.** `archive/GPU.md`: a **boot costs $0.036**, a **render costs
$0.0044**. One photograph at two flows is **$0.0088 of work behind $0.036 of boot — 80% overhead** —
plus two to four minutes before the first pixel. The repository's own conclusion was already written:
*"fewer, larger sessions is worth more than any cheaper card available to us."*

**So "the pod is hidden behind the facade" and "a boot per photograph" cannot both be true.**

### Decided — L5, L6, L7

> **L5 · The generation facade is session-scoped, and teardown is structural.**
> `generation.session()` is a context manager: a local flow's session is a no-op, a rented flow's
> session acquires an endpoint and releases it in `finally`. **Teardown stops being discipline and
> becomes control flow.** `infra/up.sh` already bounds its own wait and tears itself down, so the
> posture is in-tree rather than invented here.
>
> **L6 · A run is a batch.** ①②③ run over N photographs locally; one session renders every queued
> sheet; ⑤ scores locally afterwards. **The run directory is therefore a queue as well as a state.**
> → Q4, and `PRODUCT.md` §run-directory (N44).
>
> **L7 · The generation layer depends on an endpoint, never on a provider.** Two operations —
> *acquire a reachable ComfyUI endpoint*, *release it* — and RunPod is one implementation of them.
> **`ComfyTransport` is already provider-neutral**: it speaks HTTP to a host and a port and knows
> nothing about who rents the machine. That is the evidence this is cheap rather than speculative.

**L7 is a seam and deliberately not a registry.** `../CLAUDE.md`'s own rule binds here: *a parameter is
a seam only if something else is actually passed through it.* One provider exists today.
**State the boundary so a second provider is an implementation rather than a refactor; ship one.**
Writing a provider registry now would be exactly the generality the one-path rule was written against.

### What was considered and parked rather than rejected

**Serverless endpoints** would delete the teardown problem entirely, and **a local ComfyUI** would delete
the machine seam entirely. Both are **internals of the generation layer** under L5 — neither changes any
contract above it, which is why neither blocks the architecture. Both are recorded in
[`PARKED.md`](PARKED.md) as **P1** and **P2**, each needing a prototype round before it could be
selectable under **L3**.

**And the boot/teardown ratio is an open optimisation, not a solved problem.** L6 is a *mitigation*:
batching amortises the boot, it does not remove it. Recorded as **P3**.

### Spend, and where the ceiling lives

**The UI's trigger button is a billable act**, and `../CLAUDE.md`'s 60 min / $0.75 ceiling binds *agents*
rather than the product. **Decided: the ceiling stays in the operator's head for now** and the
orchestrator carries no billing logic. The question is real and is recorded as **P4** rather than left
implicit — an unwritten limit is the thing that produced three orphaned pods and ~$0.26 of unwatched
billing in round 3.

---

## Q10 · The flow contract — what a flow requires, and where it is declared

**Status: CLOSED 2026-09-13.** Laws **L8**, **L9**, **L10**.

### The problem, and it is deeper than "different flows need different inputs"

| flow | needs from upstream | register |
|---|---|---|
| `A` | photograph + sheet | booru tags |
| `D` | sheet | booru tags |
| cartoon · pixel-art | photograph + sheet | booru tags |
| grade | **photograph only — no sheet** | none |
| portal | photograph + **a segmentation mask** | none |
| **photoreal fantasy** | photograph + sheet | **prose, not tags** |

**The last row is the one that bites.** F45 proved prose is dead **for Illustrious** — the base reads it
and renders it in the wrong register. For a photoreal SDXL base, prose is *right* and booru tags are
wrong. **So the sheet was never flow-neutral**, and stages ② and ③ are Illustrious-coupled by
*evidence*, not by accident:

- **N40** — constraining the LLM to the 8,106-tag enum is worth **+0.283, a 9.6x improvement**
- **N41.1** — review autocomplete **must show post counts**, because `narrow waist` (9,411) renders an
  exaggerated waist and `medium breasts` (770,389) renders ordinary

That is Danbooru-specific knowledge living in two upstream layers, and a photoreal flow wants none of it.

### Decided — L8, L9, L10

> **L8 · A flow declares; it does not instruct.** A flow's manifest carries exactly four things —
> **required inputs**, **the schema and vocabulary its sheet is filled from**, **its dials**, and
> **its evaluation bar**. Upstream layers read the manifest and never learn that flows exist.
> **The manifest declares, it never computes**: logic a flow needs is code inside the flow, or the
> manifest becomes a second program written in configuration.
>
> **L9 · One sheet per flow, and a sheet stores fields only.** Sheets for flows sharing a schema and
> vocabulary start identical and **diverge when the human edits them** — which is the operator's stated
> reason for wanting them separate: *"in different flows I might want to add more details with the tags
> or remove tags."* **The assembled prompt is never stored in a sheet.** And the efficiency rule that
> follows: **stage ② is invoked once per distinct (schema, vocabulary) pair**, its result written to
> every flow that shares one. Four Illustrious flows cost one LLM call.
>
> **L10 · Prompt assembly belongs to the flow, runs before the session, and writes an artifact.**
> A flow exposes two operations: `assemble(sheet) → prompt`, pure and local, and
> `render(prompt, photo, seed) → image`, which needs the session.

### Why assembly is not a sixth layer, though it was proposed as one

**The assembled prompt is the flow's identity, exactly as its dials are.** WAI's quality ladder at the
front is **+0.013, measured (F34)**, and WAI's negative was render-tested. Swapping the assembler would
not produce a variant of the flow — it would produce an untested flow, which **L3** forbids from being
selectable. **So assembly falls under L4's logic and belongs to the flow.**

**And a `prompt_assembly` layer would be the one component that must know every flow by name.** Every
other layer reads the manifest and stays flow-blind; a layer that *"knows how to assemble the prompt for
each flow"* is a dispatcher keyed on flow id — the shape `../CLAUDE.md` already rules on: *a one-entry
registry is a dispatch mechanism with nothing to dispatch.* It would reintroduce precisely the coupling
this question removed, and be a no-op for the grade flow, which has no prompt at all.

### Two things L10 buys that are worth more than the tidiness

**Assembly runs before the pod boots.** Under **L6** a run is a batch, so assembling every prompt first
means a malformed sheet, an empty required field or a bad vocabulary reference is caught **for free** —
rather than after $0.036 of boot. **Assemble the whole batch, inspect it, then spend.**

**And `assemble` is a pure function**, so the whole of prompt construction is unit-testable offline. That
is the same property that keeps this repository's suite green without a GPU.

```
   assemble(sheet) ──▶ prompts/<flow>.json     pure · local · free · no GPU
        │                                       ▲ inspectable, diffable, recorded
        ▼
   ┌─ session() ────────────────────────────┐   ← the rented machine starts HERE
   │  render(prompt, photo, seed) ──▶ .png  │
   └────────────────────────────────────────┘
```

### The run directory that falls out

```
  runs/<photo-id>/
    caption.json                 ① — one, flow-neutral
    sheets/<flow>.json           ② → ③ — one per flow, fields only
    prompts/<flow>.json          ④a — assembled, before the session
    outputs/<flow>/<seed>.png    ④b — in the session
    eval/<flow>/<seed>.json      ⑤
```

→ **N44 owns the detail**; this is the shape the decision constrains it to.

### What it breaks, stated plainly

**Today's sheet format embeds the assembled prompt**, and `sheet.py build` regenerates it — the footgun
recorded in `CONFIGURATION.md` §6b, where the operator naturally edited the prompt block and `build` would
have silently overwritten it. **L9 removes that class of error structurally rather than by warning**,
and satisfies N41's third requirement — *the table is the only editable surface* — as a property of the
architecture. The cost is that every existing sheet on disk is in the old format. → `MIGRATION.md` (N47).

---
## Q4 · The human pause makes the orchestrator stateful

**Status: CLOSED 2026-09-13.** Laws **L11**, **L12**, **L13**, **L14**.

### The shape, after L6 made a run a batch

```
  ①──▶②──▶  ⏸ HUMAN ⏸  ──▶④a──▶ ┏ session ┓ ──▶⑤
  automatic   minutes?          assemble  ┃ render  ┃   automatic, local, free
              days?             free      ┗━━━━━━━━━┛
                                           $0.036 boot + $0.0044/render
```

A run is N photographs × M flows, it stops in the middle for a person, and a UI watches it and can
restart it. **So "where are we" has to be reconstructable from disk alone** — `../CLAUDE.md`'s own
guardrail *state lives on disk*, now binding the product rather than only an agent.

### Decided — L11 to L14

> **L11 · The artifacts are the state. `status.json` is a hint and is never read to make a decision.**
> Resume is *"find the first missing artifact"* — there is no state machine to corrupt and nothing to
> keep in sync. `status.json` carries in-flight progress for the UI only (*"render 6 of 20"*), and
> losing it costs nothing.
>
> **L12 · Every stage's output is append-only and numbered; the highest number is active.**
> **REFINED during N45 as L12a — see `PRODUCT.md` §5: for an artifact with an approval concept the
> active version is the highest *approved* one, or a fresh draft would silently demote a reviewed sheet.** No pointer
> file, nothing to keep in sync. **A sheet is never edited in place**: approving writes a new version
> and the previous one stays.
>
> **L13 · A reviewed sheet is never overwritten without an explicit force, and approval is explicit.**
> Re-running ② over an edited sheet destroys **the 0.35** — the single most valuable artifact in the
> pipeline. In-tree precedent: `sheet.py adopt` *"never touches anything but the table"*, and
> `CONFIGURATION.md` §6b's untried fix was to make `build` **refuse** on divergence. It refuses.
> **Saving is not approving** — a sheet must be parkable half-edited, because L9's whole point is that
> sheets diverge under human editing.
>
> **L14 · A batch does not halt on one failure, and ⑤ is its own pass.** One photograph's caption
> failing must not cost the other nineteen their session; failures are recorded per item and reported
> at the end. **⑤ runs separately from ④** so the rented machine is released the instant the last
> render lands — ⑤ is local and free, and must never hold a metered session open.

### The versioning scheme, and one number per flow

```
  runs/<photo-id>/
    caption/001.json                    ① — flow-neutral, versioned
    sheets/<flow>/001.json              ② draft
                  002.json  ← active    ③ approved. Highest number wins.
    prompts/<flow>/002.json             ④a — numbered BY the sheet it came from
    outputs/<flow>/002/<seed>.png       ④b
    eval/<flow>/002/<seed>.json         ⑤
```

**One version number per flow, and it is the sheet's.** A prompt is a pure function of (sheet, flow), so
it inherits the sheet's number rather than carrying its own; outputs and evals inherit it too. The
caption's version is recorded in the sheet's provenance, so the chain is traceable without a second
numbering scheme.

**Outputs must carry the version, not only the seed.** A run is never finished, so the same
`(flow, seed)` can be rendered against sheet 001 and sheet 002; flat paths would silently overwrite the
first, which is exactly the append-only violation L12 exists to prevent.

### What append-only buys, and the operator saw it before the note was written

**The review step's value stops being one experiment and becomes a standing measurement.**

```
   eval/A/001/…   rendered from the LLM's draft
   eval/A/002/…   rendered from the sheet the operator edited
                  ────────────────────────────────────────────
                  the difference IS the 0.35
```

F44 measured that gap once — **0.568 unreviewed against 0.917 reviewed**, on five subjects. Under L12
every run that re-renders after an edit produces the number again, on real data, for free.

**And the wider consequence the operator named: the run directory is an experiment harness.** Change the
VLM, change the LLM, change the flow — each lands as a new caption, a new sheet, a new output, and every
one is evaluated. **This is the prototype's own method, productised**: `real_photo.py`'s
`ARMS = {"1_a": ("A", "full"), "2_d": ("D", "full")}` plus `contact_sheet.py` plus `criteria_eval.py`,
done by hand once per round, is exactly what an append-only run directory *is*.

**It makes L3's entry gate executable rather than procedural.** *"A flow enters by passing a prototype
round and the evaluation bar"* stops being a process someone remembers and becomes something the tool
does.

**The path is a sufficient identifier only because L3 holds.** A flow id never silently changes
behaviour, because a changed implementation is a new one; VLM and LLM choices are captured transitively,
since they move the caption number, which moves the sheet number. **Provenance must record the graph
digest to prove L3 held rather than assume it.**

### One thing this does NOT license, and it is promoted to Q5

**Cross-setup comparison is sound at cohort level and unsound at single-photograph level.**

```
   UNSOUND   one photograph, six setups, rank the six scores
             ← round 1's disease: the least-stylized arm wins by construction

   SOUND     one cohort of N photographs; run setup X over all N → 14/17
                                          run setup Y over all N → 11/17
             ← compare HIT RATES. Every candidate is equally stylized,
               so stylization cannot buy a point
```

`IDENTITY.md` §5: *absolute similarity is low, and only order survives.* **So the evaluation layer's
unit is a cohort, not an image** — per-image evaluation can report axes, it cannot report identity.
**→ Q5.** The comparison *feature* is parked as **P5**; the *property* that makes it possible is free
and is decided here.

---
## Q5 · The evaluator asks a different question from the one the product needs

**Status: CLOSED 2026-09-13.** Laws **L15**, **L16**. **P6 promoted from parked to scheduled.**

### Three questions, and the project has been conflating them

| | question | method | status |
|---|---|---|---|
| **identification** | *which of N photographs did this render come from?* | N-way, needs a **cohort** | **built and validated** — F37 5/6 · F40 8/10 · F41 **14/17 at chance 5.9%** |
| **verification** | *is this render the same person as this photograph?* | same/different, needs a **threshold** | **not built** — gated on P6's data |
| **attribute recall** | *does the render show what the sheet said?* | WD14 on the render | **built** — `criteria_eval.py`, 0.917 reviewed against 0.568 unreviewed |

**The product's question — "how much identity was preserved from the original photo?", asked per image —
is the verification one, and nothing answers it.**

### Why no rescaling fixes this

```
   ONE photograph, ONE render  ──▶  cosine 0.62
                                    ▲
                            "62% of what?" There is no zero point across
                            photograph → drawing. IDENTITY.md §5: absolute
                            similarity is low, and only ORDER survives.
```

**`main` already refuses to paper over this, correctly.** `isekai/evaluate.py`'s own docstring: *"This
module ranks and diffs. It does not grade, and it never will… A fidelity percentage is not available,
and this says so rather than shipping a rescaled number that would be read as one."* **That refusal is
right, and it is also why the product's headline question has had no answer.**

### Decided — B now, C as the real answer, A rejected

| | approach | verdict |
|---|---|---|
| **A** | the facade ships a **fixed reference cohort** — score against the user's photograph plus K pinned strangers | **rejected.** It buys a number by shipping strangers' faces — a licensing and privacy cost — and what it returns is still a *rank* wearing a score's clothes |
| **B** | **per-run cohort only** — identity is reported when a run carries enough photographs, and refused otherwise | **adopted now.** Zero new machinery; `Refusal` already exists and is exactly this |
| **C** | **build verification** — calibrate a threshold on P6's data, then report same/different with a confidence | **the real answer, scheduled behind P6** |

> **L15 · Identity is a cohort measurement. Below the cohort size it is refused, never estimated.**
> The refusal is `Refusal`, which `isekai/evaluate.py` already defines and uses. **In the interactive
> single-photograph case the identity panel says so** — *"identity requires a cohort"* — rather than
> showing a number. That is a visible product limitation and it is the honest one.
>
> **L16 · Per-image evaluation reports every axis it can, with identity explicitly absent.**
> Attribute recall against the sheet, pose PCK, and the two style axes are all per-image and all
> available. **Identity is named as withheld, never silently omitted** — an axis that quietly
> disappears reads as an axis that passed.

### The entanglement caveat travels with the number

**`glintr100` is the encoder InstantID optimises against (F46), so `A`'s identification result is an
upper bound; SFace, independent, gives 9/17 where `glintr100` gives 14/17 on the same crops.** Under
**L3** plurality *is* the measurement for the evaluation layer, so **the cohort report carries the
bracket `9/17 … 14/17`** rather than one encoder's figure.

### Q2's carried consequence, closed here

**The per-flow evaluation bar is consistent with L15.** A flow declares its bar under **L8**, and since
identity is a cohort property, a flow's identity bar is a cohort-level threshold — which is what makes
the pixel-art path's *"identity weakens by design"* expressible as a lower bar rather than as an
exemption, and stops the grade path's trivially-perfect identity from rubber-stamping anything.

### P6 is now the gate on the product's headline claim

**Scheduled, not parked.** **C cannot be built without it**, and the hole it fills is that the project
has exactly one same-person-across-photographs pair — `prototype/real_photo.py:123` — so **n=1**. Until
that set exists, F41's 14/17 cannot distinguish *"the render matches this person"* from *"the render
matches this photograph"*, and **full-body framing costing identity in three independent sets is the
evidence that says the distinction is real.** → `ROADMAP.md` (N48).

---
### AMENDED 2026-09-13, during N43 — the identity number moves to a published benchmark

**The operator's reframe, and it simplifies L15 rather than contradicting it.** Evaluation is not a
per-user product feature. It is **the proof**, and the proof belongs in the public repository:

```
  the PROOF     a synthetic cohort, published, reproducible by anyone who clones
  the PRODUCT   your photograph in, images out — no identity number is shown
  the PRIVATE   real cohorts (N42's phone set, N30's seventeen) — measured, never published
```

**So L15's awkward consequence disappears.** The interactive single-photograph case no longer needs to
say *"identity requires a cohort"*, because **the product does not claim a per-image identity number at
all.** The claim lives in the benchmark, where the cohort exists by construction.

**One premise in the operator's statement is corrected, and the correction strengthens it.** He said
cohorts are only possible with synthetic photographs. **N42 disproved that on the same day** — ten
Instagram phone photographs of four real people, scoring **10/10 person-level**. Real cohorts work.
**The real reason the published benchmark must be synthetic is privacy:** `prototype/inputs/real/` is
gitignored by design (D14), and photographs of real people cannot ship in a public portfolio
repository. That is a stronger reason than impossibility, and it is the one to write down.

**What does not change.** P5's comparison harness and P6's verification still require cohorts. **Both
are operator tools, not user features**, which is consistent with the split above rather than an
exception to it.

---

## Q6 · Six capabilities are specified on `main`; the prototype rewrites two

**Status: CLOSED 2026-09-13.** Laws **L17**, **L18**.

### The inventory, taken 2026-09-13 — 152 scenarios across six capabilities

| capability | scenarios | fate under L1–L16 |
|---|---:|---|
| `comfy-transport` | 5 | **survives whole.** L7 wants provider-neutrality and it is already neutral — HTTP to a host and a port |
| `model-provisioning` | 22 | **survives, extends** — Q8 adds locally-hosted weights |
| `evaluation` | 28 | **survives, modified** — L15/L16 add the cohort rule and the named-withholding rule |
| `cli` | 30 | **survives, extends** — shape B adds per-stage subcommands |
| `workflow-injection` | 23 | **mostly dies.** *"Latent initialisation from the photo"* and *"The positive prompt is graph configuration"* are both **false** under the from-noise flow |
| `workflow-mutation` | 44 | **mostly dies.** Six of its eight requirements are dial jitter, which **L4** forbids |

**≈60 scenarios contradicted, ≈92 survive — and the survivors are the expensive half.** Transport,
provisioning, evaluation and CLI parsing are the parts that took versions to get right. **That is most
of why the next version is affordable at all**, and it is the strongest argument in `MIGRATION.md` (N47).

### Decided — L17, L18

> **L17 · One capability per layer.** The living spec is restructured from six capabilities to roughly
> nine: `cli`, `orchestration`, `caption`, `sheet`, `review`, `image-generation`, `comfy-transport`,
> `evaluation`, `model-provisioning`. `workflow-injection` and `workflow-mutation` are **replaced**, not
> renamed — a capability called `workflow-injection` that contained requirements about captions and
> sheets would be a name that lies.
>
> **L18 · The old flow is deleted, not deprecated, and `mutate`'s dial jitter goes with it.** Only the
> path this prototype produced remains on `main`. There is no transition version in which both exist —
> **L3** says one configured implementation, and a deprecated flow is a dead option carried, which is
> the exact failure the original one-path rule was written against.

### Why deleting the old flow costs nothing measurable

**`main`'s shipped path is the architecture round 1 rejected.** It is img2img — the photograph seeded
into the latent at `denoise < 1` — and **F24 established that taking the photograph *out* of the latent
is what removed the blur.** Round 1's `notile-d045` was that same architecture tuned, and the verdict
was *"rejected — too soft… median linework 0.0030 across ten portraits, ~10x below its own inputs."*

**So this is not a working path being traded for an unproven one.** It is a measured-inferior
architecture being replaced by a measured-better one, which is precisely what *"a version may replace
it"* was written to license.

### The one thing L18 does not settle, and it belongs to N48

**Deleting the old flow does not require the whole new pipeline to exist in the same version.** A
version could delete the old path and land the generation layer with flow `A` alone, with the sheet
supplied by hand while ①②③ are still being built. **There is then a window where `convert.py photo.jpg`
is not end-to-end** — and whether that window is acceptable is a **roadmap shaping** decision, not a
capability one. → `ROADMAP.md` (N48).

---
## Q7 · Licences — what this product becomes

**Status: CLOSED 2026-09-13.** Law **L19**. The commercial question is parked as **P7**.

### JoyCaption is not the only one, and that reframes the question

`scripts/eval_licences.md`, read 2026-09-06, already records **four non-commercial artifacts** as
deviations. JoyCaption makes five, across two layers:

| artifact | layer | licence | binds when |
|---|---|---|---|
| **JoyCaption** | ① VLM | Apache-2.0 **code**, weights undeclared, base is **Llama-3.1** | attribution and AUP always |
| **`glintr100`** | ⑤ EVAL | InsightFace *library* MIT, **weights non-commercial research** | any commercial use |
| **StyleID** | ⑤ EVAL | non-commercial research | any commercial use |
| **SegFormer parser** | ⑤ EVAL | NVIDIA SCL — *"non-commercially… research or evaluation purposes only"* | any commercial use |
| **FFHQ-derived** | ⑤ EVAL | non-commercial; *"do not use for biometric human recognition"* | any commercial use |

**So *"does this ship?"* was never a JoyCaption question.** It is a product-definition question that four
other artifacts were already waiting on.

### The operator's answer, 2026-09-13

**Primarily a personal tool**, possibly **hosted non-commercially** later, and **a public GitHub
repository as a portfolio project** — open source, anyone may clone it and run it on their own machine.
**No commercial use now.** Attribution to JoyCaption is accepted.

> **L19 · The repository is Apache-2.0, public, and distributes no model weights. A manifest points; it
> does not ship.** Every deviation above is therefore inert: pointing at a non-commercial artifact is
> not distributing it, and `eval_licences.md` already reasons exactly this way — *"This repository is
> Apache-2.0, it is public, and it distributes no model weights."* **A clone downloads the weights
> itself, under whatever licence that artifact carries, from its own publisher.** L19 holds for exactly
> as long as the project stays non-commercial, and **P7** is what re-opens it.

**One concrete action, and it is cheap:** a public repository with Llama-3.1-derived weights in its
stack carries **"Built with Llama"** attribution in its README. → `ROADMAP.md` (N48).

### A correction to the record, made here rather than by editing a note

**`ARCHITECTURE.md` §3 says JoyCaption is *"not cleared for anything that ships."* That overstates its
own evidence.** The weights are downloaded at provision time and never redistributed, so a hosted
service would not trigger redistribution terms at all; what binds is **attribution** and the
**acceptable-use policy**, and neither is hard. The 700M-MAU clause is not a realistic concern for this
project.

**Recorded as a new statement rather than as an edit**, because this repository's rule is that a claim
is never quietly softened to match a later reading — the same discipline `FINDINGS.md` is under. **And
stated with its limit: this is not legal advice, and neither was the sentence it corrects.**

---

## Q8 · Where the weights live, and what pins them

**Status: CLOSED 2026-09-13.** Laws **L20**, **L21**, **L22**. **One defect found.**

### The inventory, taken 2026-09-13

| artifact | manifest | pinned by |
|---|---|---|
| pod graph models | `scripts/models.json` | revision + digest, re-derivable byte-identical |
| evaluator models | `scripts/eval_models.json` | same, plus `eval_licences.md` |
| JoyCaption, 5.40 GiB | `prototype/styles/joycaption_models.json` | revision + digest + four licence layers |
| SFace · WD14 · upscaler | `prototype/styles/*.json` | revision + digest |
| **Qwen3-8B, 5.2 GB** | **none** | **`ollama pull qwen3:8b` — a moving tag** |

### The defect

**Stage ② — the layer worth +0.283, a 9.6x improvement — resolves through a tag that upstream can
repoint at any time**, silently changing what the router emits. `model-provisioning`'s own requirement
says *"Every source is pinned to an immutable revision and a digest"*, and **Qwen violates it**.

**The fix has a worked precedent in-tree.** JoyCaption is *also* hosted on Ollama and *is* pinned,
because its GGUF was fetched by pinned revision and verified by digest, and `ollama create` built the
Ollama model from that verified file. **Hosting through Ollama is not the same as resolving through
Ollama.** The same treatment closes Qwen.

### Decided — L20, L21, L22

> **L20 · A manifest belongs to an implementation, not to a layer.** Each selectable implementation —
> a VLM, an LLM, a flow, an encoder — declares its own artifacts. Adding a flow or swapping a reader
> then touches exactly one file, which is what **L3** already implies by making the implementation the
> unit. **Any destination appearing in two manifests must agree byte for byte** — the generalisation of
> the test that already guards `glintr100` and the two DWPose artifacts across the current pair.
>
> **L21 · Every manifest is re-derivable byte-identically, by one shared deriver parameterised by
> manifest.** The byte-identical rule is what makes a manifest trustworthy rather than merely present.
> **One deriver, not one script per file** — `derive_manifest.py` and `derive_eval_manifest.py` are
> already two near-copies, and five would drift.
>
> **L22 · Every model is pinned to an immutable revision and a digest, with no exception for a hosted
> runtime.** A model reached through a server is pinned at the bytes that were fetched, not at the tag
> the server resolves.

---

## Q11 · How do we learn that a better version of a pinned model exists?

**Raised by the operator during Q8, 2026-09-13. Status: CLOSED 2026-09-13** — the mechanism is parked as
**P8**; **the manifest schema accommodates it now.**

### The tension is real and it is inherent to pinning

**Pinning buys reproducibility and costs awareness.** A pinned revision cannot move, which is the point
— and it also means the project can sit on a superseded model indefinitely without anything saying so.
Three of the ranked open items are *"try a newer/other model"*, so this is not hypothetical.

### Decided — the mechanism is deferred, the schema is not

> **Each artifact records the channel to watch alongside the revision it is pinned to.** The pin is what
> is used; the channel is what would be compared against.

**Why the schema decision is taken now and not with the mechanism.** Adding a field to every manifest
later means **re-deriving every manifest** — and under **L21** those files are byte-identical outputs,
so the churn is visible in every diff and touches artifacts nobody is changing. **It is nearly free now
and annoying later.** This is the same reasoning as `decisions §4 probe`: the cheap act goes first.

### And the mechanism is cheaper than it sounds

**`derive_manifest.py` already re-derives every revision and digest.** Pointed at the *watch channel*
instead of the *pinned revision*, its existing output is a drift report — *"this artifact's channel now
resolves to a different revision than the one you pinned"*. **The watcher is close to a flag on a script
that already exists**, which is why P8 is worth doing and why it is still not worth doing before the
product runs.

**The bar it must respect: a watcher reports, it never updates.** An automatic bump would defeat
pinning entirely, and under **L3** a new revision is a new implementation that must pass a prototype
round and the evaluation bar before it is selectable.

---
## Q9 · The product's actual input has never been tested

**Status: CLOSED 2026-09-13** as a *decision about how to answer it*. **The measurement is in flight**
— the phone set is being rendered as this is written, and its result lands in `FINDINGS.md`, not here.

### What had never been tested

```
  tested across four rounds          NEVER tested
  ┌──────────────────────────┐      ┌───────────────────────────┐
  │ 10 synthetic portraits   │      │ a phone snapshot           │
  │ 10 held-out synthetic    │      │  · unflattering light      │
  │ 10 pose studies          │      │  · motion blur, JPEG noise │
  │ 17 real, professionally  │      │  · off-angle, mirrors      │
  │    shot or generated     │      │  · face small in frame     │
  └──────────────────────────┘      └───────────────────────────┘
```

**Q9 is unlike Q1–Q8.** They were design questions settleable from evidence already on disk. **This one
needed data**, and on 2026-09-13 the operator gathered it: **ten phone photographs of four people**, at
`prototype/inputs/real/phone/` — 10 MB total, sourced from Instagram as the one place phone-camera
photographs of real people could be found.

### Decided

> **Q9 gates the *claims*, not the *architecture*.** Nothing in **L1–L22** changes based on the answer —
> a phone photograph is a photograph. What changes is what may be *said*: every identity number in four
> rounds is measured on studio or synthetic input, and until this run lands that limit belongs in the
> README rather than in a footnote.

> **Multiple people in one frame is OUT OF SCOPE.** The operator's decision, 2026-09-13. `1girl` is gone
> and `solo` is the Danbooru mode selector; **InstantID takes one embedding**, and nothing in the
> pipeline handles two faces. Recorded as a deliberate limit rather than an unnoticed gap.

### The run, and why it is worth more than Q9

**Ten photographs of four people is the first same-person-across-photographs data this project has
had.** `prototype/real_photo.py:123` currently declares exactly one such pair — **n=1**. So this set
**partially closes P6**, which Q5 had promoted to scheduled an hour earlier: it can ask whether the
identity number measures *a person* or *a photograph*, at group sizes of two and three rather than P6's
proposed five.

**The bar, stated before the render, as this repository requires.** **Stage ③ is skipped by the
operator's decision** — the sheets go straight from the reader to the render. F44 puts the unreviewed
path at **0.568 attribute recall against a reviewed sheet's 0.917**, so **attribute numbers will be low
and that is expected, not a failure.** Identity is the axis this run is for, and **F45 established that
identity is carried by the legs, not the prompt** — a bad sheet degrades attributes rather than likeness.

### ~~One defect found while writing this~~ — WITHDRAWN 2026-09-13, it was not a defect

**The claim was: `isekai/workflow.py`'s header parser returns dimensions only, so a rotated phone JPEG
would be scaled from unrotated dimensions. That is wrong, and the code says so.**
`isekai/workflow.py:315` transposes on `_EXIF_TRANSPOSING_ORIENTATIONS` for **both** codecs, under the
comment *"the one statement of what the loader does with the tag, for every codec"* — `_exif_orientation`
and `_tiff_orientation` are right there in the same file.

**Withdrawn rather than deleted**, and the cause is worth more than the claim was: **it was asserted
from a function's return signature without reading its body.** `image_dimensions` returns
`tuple[int, int]`, which looks orientation-free and is not. **A signature is not an implementation** —
and the twenty phone photographs this run rendered would have exposed it immediately had it been real.

---

## N42 closed — eleven questions, twenty-two laws

**2026-09-13.** Every question in the register is settled. The laws they produced are the input to
**N43–N48**, and each of those tasks cites the law that licenses it.

| | law | from |
|---|---|---|
| **L1** | a facade admits a wheel-needing implementation only through the `eval_backends` posture | Q1 |
| **L2** | the import-graph rule is directional — a front end may import the orchestrator, never the reverse | Q1 |
| **L3** | one pipeline; each layer is a facade with a selector; **a selectable implementation is a measured one** | Q2 |
| **L4** | a variation draws a new seed and changes no dial | Q2 |
| **L5** | the generation facade is session-scoped; **teardown is control flow, not discipline** | Q3 |
| **L6** | a run is a batch | Q3 |
| **L7** | the generation layer depends on an endpoint, never on a provider | Q3 |
| **L8** | a flow declares and does not instruct — inputs, schema+vocabulary, dials, bar | Q10 |
| **L9** | one sheet per flow; a sheet stores fields only, never the assembled prompt | Q10 |
| **L10** | prompt assembly belongs to the flow, runs before the session, writes an artifact | Q10 |
| **L11** | the artifacts are the state; `status.json` is a hint and is never read to decide | Q4 |
| **L12** | every stage's output is append-only and numbered; highest wins | Q4 |
| **L13** | a reviewed sheet is never overwritten without force; **saving is not approving** | Q4 |
| **L14** | a batch does not halt on one failure; ⑤ is its own pass | Q4 |
| **L15** | identity is a cohort measurement — below cohort size it is refused, never estimated | Q5 |
| **L16** | per-image evaluation reports every axis it can, **with identity named as withheld** | Q5 |
| **L17** | one capability per layer | Q6 |
| **L18** | the old flow is deleted, not deprecated | Q6 |
| **L19** | the repository is Apache-2.0, public, and distributes no weights — a manifest points | Q7 |
| **L20** | a manifest belongs to an implementation, not a layer | Q8 |
| **L21** | every manifest is re-derivable byte-identically, by **one** shared deriver | Q8 |
| **L22** | every model is pinned to a revision and a digest — **no exception for a hosted runtime** | Q8 |

**One defect was found on the way, and one was claimed and withdrawn:**

1. **Qwen3-8B is unpinned** — `ollama pull qwen3:8b` is a moving tag, in violation of
   `model-provisioning`'s own requirement, on the layer worth 9.6x.
2. ~~**EXIF orientation is unhandled**~~ — **withdrawn the same day; it was never a defect.** See Q9.

**And two claims in the record were corrected:** N42's own EXIF claim, above, and `ARCHITECTURE.md` §3's *"not cleared for anything that
ships"* overstates its own evidence (Q7).

**Parked, with reasons, in [`PARKED.md`](PARKED.md):** P1 serverless · P2 local ComfyUI · P3 the
boot/teardown cost · P4 spend awareness · P5 the comparison feature · **P6 promoted to scheduled** ·
P7 the commercial licence audit · P8 the model-update watcher.
