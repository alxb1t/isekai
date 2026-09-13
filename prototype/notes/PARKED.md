# PARKED — raised during round 5, deliberately not settled now

**Opened 2026-09-13, during N42's question-by-question walk.** The discussion keeps producing things
that are real, worth doing, and **not blockers for the architecture**. This is where they go, so that
deferring one is a recorded act rather than a thing that quietly stops being mentioned.

> **This file is not a backlog and not a roadmap.** `ROADMAP.md` (N48) holds the versions that will be
> built; the operator's own notebook holds the product backlog. **This holds what round 5 raised and
> round 5 will not answer** — research to run, prototypes to spike, optimisations found but not taken,
> and questions whose answer is currently *"a human, for now"*.

**Each entry states four things**, because an entry missing any of them is one nobody can pick up:
**what it is**, **why it was parked**, **what would make it worth doing**, and **what it would change if
it won**. An entry that turns out to block something is promoted into [`OPEN.md`](OPEN.md) as a
question; an entry that gets scheduled is promoted into `ROADMAP.md` and struck through here.

---

## P1 · Serverless GPU endpoints

**What.** Run generation on a serverless endpoint — RunPod's or another provider's — instead of a pod
that must be created, waited for and torn down.

**Why parked.** It is an **internal of the generation layer** under **L5**: the facade exposes
`session()`, and whether that session boots a pod or submits to an endpoint changes no contract above
it. So it cannot block the architecture, and designing around it before it is measured would be
speculative.

**What would make it worth doing.** The boot/teardown ratio (**P3**). A serverless endpoint would
**delete the teardown problem entirely** — there is nothing to leave running, so the class of failure
that produced three orphaned pods and ~$0.26 of unwatched billing in round 3 stops existing.

**What it would change if it won.** **L5's `finally` becomes unnecessary and L6's batching becomes
optional**, because the boot would no longer be a fixed cost to amortise. It would also remove
`infra/up.sh` and `infra/down.sh` from the product's critical path.

**The unknown, stated honestly.** **Cold start on a 10+ GB image has never been measured here.** The
RunPod MCP's own guidance warns of first-job cold starts "of minutes". If a cold start costs more than a
pod boot, the idea is worse than what it replaces — and that is exactly the number the spike exists to
get. Needs a prototype round and an **L3** entry gate before it could ever be selectable.

---

## P2 · ComfyUI running locally

**What.** Run the generation layer on the operator's own machine rather than on rented hardware.

**Why parked.** Same reason as **P1** — an internal of the generation layer, changing no contract above
it.

**What would make it worth doing.** It **deletes the machine seam entirely**: no boot, no teardown, no
tunnel, no provider, no spend ceiling, and the whole of **Q3** collapses into "everything runs here".
It would also make iteration free, which is what a prototype round costs most.

**What it would change if it won.** **L5, L6 and L7 all become vestigial** for the default flow — they
would still hold for any flow that needs hardware the machine does not have.

**The unknowns, and there are two.** **Capacity:** 16 GiB against SDXL + InstantID + a ControlNet stack
+ a hires pass, with JoyCaption's 5.40 GiB and Qwen3-8B's 5.2 GB already resident for stages ①②.
**Portability:** the shipped image pins **cu128 PyTorch for Blackwell (sm_120)** — a local Mac is a
different accelerator entirely, so this is not "the same image, elsewhere", it is a second
implementation with its own verification.

---

## P3 · The boot/teardown cost is unsolved, and batching only hides it

**What.** A boot is **$0.036** and a render is **$0.0044** — **a boot is eight renders.**
`../notes/CONFIGURATION.md` §6 records the conclusion that follows: fewer, larger sessions beat any cheaper
card available.

**Why parked.** **L6 mitigates it and does not fix it.** Batching amortises a fixed cost across more
work; the fixed cost is still there, and on a single-photograph run it is still 80% of the bill. That is
acceptable now and worth returning to.

**What would make it worth doing.** Any usage pattern where batching is not available — a UI user who
uploads one photograph and waits, which is precisely the product's own interactive case.

**What it would change if it won.** The interactive latency, which is the part of this that is not about
money: **two to four minutes before the first pixel** is the real cost of a boot, and no amount of
batching helps the person waiting.

**Candidate directions, none measured:** **P1**'s serverless endpoints · **P2**'s local ComfyUI · a
warm pod held across runs with an idle ceiling · a smaller/faster boot image. **The first two are
already parked separately; this entry exists so the *problem* is tracked rather than only its
candidate answers.**

---

## P4 · The orchestrator does not know what it is spending

**What.** Under **L5** the UI's trigger button acquires rented hardware, which makes it a **billable
act**. Nothing in the product knows or bounds that.

**Why parked.** **The operator's decision, 2026-09-13: the ceiling stays in his head for now**, and the
orchestrator carries no billing logic. Explicitly out of scope for the first versions.

**What would make it worth doing.** Anyone other than the operator triggering a run; or a run large
enough that its cost is not obvious in advance — which **L6**'s batching makes more likely, not less.

**What it would change if it won.** The orchestrator would gain a concept it currently does not have —
**an estimate before it spends and a total after** — and a refusal path. That is a real feature with
real spec surface, not a log line.

**Why it is written down rather than left implicit.** `../CLAUDE.md`'s 60 min / $0.75 ceiling binds
*agents*, not the product. **An unwritten limit is exactly what produced three orphaned pods in round
3**, and the lesson recorded there was that the rule which names nobody is the rule nobody follows.

---
## P5 · The comparison feature — pick a setup in the UI, rank the results

**What.** The operator's realisation during Q4: because **L12** makes every stage append-only and **⑤**
scores every output, the run directory is already an experiment harness. The *feature* on top of it is a
UI that lets you choose VLM, LLM and flows per run and then **compare the scored outputs against each
other** to find which configuration wins.

**Why parked.** **The property is free; the feature is a product.** The property — append-only
artifacts, per-setup evaluation, comparable paths — falls out of **L9** and **L12** at no cost and is
decided in `OPEN.md` Q4. The comparison view, the arm bookkeeping and the ranking are a second product
on top of the first, and building them into v1 would delay photograph→image indefinitely.

**What would make it worth doing.** **L3's entry gate.** *"A flow enters by passing a prototype round
and the evaluation bar"* is currently a process a human remembers. This feature is what makes it
something the tool performs — at which point adding a flow stops needing a hand-written runner and a
throwaway contact sheet.

**What it would change if it won.** **Prototype rounds would happen inside the product** rather than in
`prototype/`'s scripts. `real_photo.py`, `ablation.py`, `contact_sheet.py` and the hand-built
`evaluations/<date>/report.md` are the manual version of exactly this.

**The constraint it must respect, and it is not negotiable.** **Comparison is sound at cohort level and
unsound at single-photograph level** (`OPEN.md` Q4, Q5). A UI that ranks six renders of *one* photograph
by score reproduces round 1's disease, where the least-stylized arm wins by construction. **The feature
ranks setups over a cohort, or it is wrong.**

---

## ~~P6~~ · A same-person, multi-photograph set — **SCHEDULED 2026-09-13, no longer parked**

> **Promoted out of this file by `OPEN.md` Q5.** It is the gate on approach **C**, which is the only
> path to the per-image identity number the product's headline question asks for. It goes to
> `ROADMAP.md` (N48); the entry is kept below because its reasoning is the case for scheduling it.

**What.** A set of **5 photographs of one subject and 5 of different subjects**, so the identity
machinery can be asked a **verification** question rather than only an identification one: does the
encoder cluster *the person*, or is it matching the source photograph's framing, lighting and pose?

**Why parked.** Blocked on data the operator has to gather, like the phone-camera set. **No GPU for the
scoring; renders are needed**, so it is cheap but not free.

**What would make it worth doing — and this is the strongest case in this file.** The project has
**exactly one** same-person-across-photographs pair today: `prototype/real_photo.py:123`,
`SAME_PERSON = (("face_4", "ful_height_1"),)`. **That is n=1.** So F41's **14/17** cannot currently
distinguish *"the render matches this person"* from *"the render matches this photograph"*.

**What it would change if it won — or lost.** It converts the headline identity result from a
photograph-level claim into a person-level one, which is what the product actually claims. **And if it
loses, that is the more valuable outcome**: it would say the pipeline reproduces a *photograph*, not a
*person*, and every identity number in four rounds would need re-reading in that light.

**The evidence that says this is worth checking rather than assumed.** **Full-body framing costs
identity, reproduced in three independent sets** — `00059` in round 2, `15_01`/`16_01` in N29,
`full_height_4`/`male_full_height` in N30. A property of the *photograph*, measurably changing the
identity number, on a subject who did not change.

---
## P7 · The commercial licence audit

**What.** If this project ever becomes a paid service, **four evaluation artifacts must be replaced**
and one base model's terms must be read: `glintr100`, StyleID, the SegFormer clothes parser and the
FFHQ-derived artifact are all non-commercial-research; WAI-illustrious-SDXL's own terms are **not yet
recorded anywhere in this repository**.

**Why parked.** **The operator's decision, 2026-09-13: no commercial use now.** The project is a
personal tool, possibly hosted non-commercially, in a public Apache-2.0 repository that distributes no
weights — under which every deviation is inert (`OPEN.md` **L19**).

**What would make it worth doing.** Money, in any form — a paid tier, a sponsorship that makes the
service commercial, or a client. **The trigger is the business model changing, not a date.**

**What it would change if it won.** **Two of the five are already half-solved by the architecture.**
Under **L3** an implementation is swappable and measured, and the permissive replacements partly exist:
**SFace is Apache-2.0 and already in the stack** as the independent encoder, and `eval_licences.md`
already states the guardrail — *"a model whose licence is restrictive may not be the sole carrier of an
axis."* The parser and StyleID have no identified replacement.

**And one thing that must not be assumed.** **WAI-illustrious-SDXL's licence is not in
`eval_licences.md`**, because that file covers the *evaluator*. The generator's own terms have never
been read into this repository. **That is a gap, not a clearance.**

---

## P8 · A watcher that reports when a pinned model has a newer version

**What.** Something that tells the operator a pinned artifact's upstream has moved — so that pinning
buys reproducibility without costing awareness.

**Why parked.** **The mechanism is deferred; the schema is not.** `OPEN.md` **Q11** takes the manifest
decision now — each artifact records the channel to watch alongside the revision it is pinned to —
because adding that field later would mean re-deriving every byte-identical manifest for artifacts
nobody is changing.

**What would make it worth doing.** **Three of the ranked open items are already "try a newer or other
model"** — a better VLM, per-field enums, an independent recognizer. The project will keep asking this
question, and answering it by hand means noticing by accident.

**What it would change if it won — and it is cheaper than it sounds.** **`derive_manifest.py` already
re-derives every revision and digest.** Pointed at the *watch channel* instead of the *pinned revision*,
its existing output **is** the drift report. The watcher is close to a flag on a script that exists.

**The bar it must respect.** **A watcher reports; it never updates.** An automatic bump would defeat
pinning entirely, and under **L3** a new revision is a new implementation that must pass a prototype
round and the evaluation bar before it is selectable.

---
