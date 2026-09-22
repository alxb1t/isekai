---
version: v0.22.2
---

## Why

**`v0.22.1` was cut code-only and deferred every sentence to this version.** It fixed eighteen defects and
left seventeen tests carrying `@pytest.mark.spec_exempt("behaviour; the scenario lands in 0024")` — a
marker whose documented meaning is *genuinely structural*, borrowed for one version on the explicit
condition that this one repays it. **That debt is nearly a fifth of the repository's ninety-five
exemptions**, and `grep spec_exempt tests/ | grep 0024` is the worklist it left behind.

**The repository also says things about itself that are not true.** Measured at `b4abe12`:

- **Ten false self-claims** in tracked prose — a flow described as *"two tracked files"* when it is four;
  `boundary/README.md`'s *"nothing outside this directory opens a socket or spawns a binary"* against
  three live violations; `sheet.py`'s *"the sixteen fields"* against a second flow that declares 21.
- **Six stale numerals in `CLAUDE.md`** — *"change all four"* when three copies of the gate exist;
  five stage directories when `run.py` declares seven; *"every `__init__.py` holds no code"* against a
  53-line one; and a change-id formula with **no patch case**, which the id of the change that shipped
  `v0.22.1` already contradicts.
- **Wrong counts in every group README.** `isekai/README.md` says `shared/` holds 4 modules (it holds 5)
  and `boundary/` holds 7 (it holds 6) — **under a heading that reads *"Count; do not trust the row."***
  Eight further test-module counts are wrong across five files.

**The disclaimer experiment has already run, and it failed.** That heading was written after two counts
went wrong at v0.20; two are wrong again now, one of them in the opposite direction. A disclaimer does not
stop a number from rotting — it only records that someone expected it to.

**And there is no `docs/`.** Nothing in the repository depicts the module graph, the subpackage graph or
the stage data flow. `README.md` carries three good ASCII diagrams and all three are about deployment
topology. The nearest thing to a module graph is `isekai/README.md`'s edge table, which has **three
errors**: a module-level `boundary ──▶ shared` missing entirely, the `shared ──▶ boundary` laziness
annotated backwards, and `interface/ui` collapsed away.

## What changes

**Six phases, sweep first** — everything written in phases 2 and 3 is drafted by reading the repository's
own prose, so the prose is corrected before anything is drafted from it.

1. **The sweep.** The ten false claims, the six `CLAUDE.md` numerals, and **every quantity stripped from
   every group README** — replaced by the names it counted. A row naming `atomic_write · field_map ·
   fields · image · vocabulary` is self-counting; `5` is not.
2. **`docs/arc/`, two files.** `modules.md` — the subpackage graph, its two honest cycles and its three
   lazy edges. `data-flow.md` — the seven verbs, what each stage reads and writes, and the run-directory
   layout. **Prose, short sentences, ASCII, and no quantities.**
3. **`CLAUDE.md` becomes agent operating instructions.** **165 of its 420 lines are description rather
   than instruction** — `## The path` is, in an audit's words, *"almost entirely data flow and
   architecture, with no agent instruction in it."* That leaves; what it held that is *rule* rather than
   *description* stays.
4. **The spec catches up with the code.** The `ui` requirement that assumes an approved input can never
   have a draft is rewritten, and the four capabilities `v0.22.1` touched are audited against the tree.
5. **Seventeen scenarios**, for behaviour `v0.22.1` shipped bound to nothing.
6. **The seventeen tests are rebound**, `spec_exempt` → `spec`.

**One code change, and it is the only one.** `put_draft` refuses every update to an approved input, which
makes `review --flow F --new-version` produce a draft the surface will not edit. The refusal says so
honestly — *"this page keeps showing the input approved and read-only either way, because the re-opened
state is v0.22.2's"* — so **the code names this version as the one that resolves it.** `review` is right:
`--new-version` exists for exactly this, and `review:copy:second-review-appends` is the older and tested
contract. The gate becomes *approved **and no newer draft***.

## Impact

**No flow changes, no render changes, no metered cost.** The flow directories are untouched,
`manifest_digest` does not move, and no phase contacts a pod.

**Two behaviour changes reach the operator**, both from the one code change: an approved input that has
been re-opened with `--new-version` becomes editable again on the surface, and the rail reports it as
re-opened rather than approved.

> ⚠️ **Adding a third rail status splits two counts that agree today.** `/api/batch["approved"]` is
> derived from the status string; `Batch.approved_count` reads the directory. They diverge the moment a
> status exists that means *"has an approved artifact but is not approved."*
> `ui:batch:approved-count-comes-from-disk` is the scenario that catches it, and phase 4 must keep it
> true.

**This change carries a spec delta**, unlike its predecessor: **nineteen new scenarios and one modified
requirement** across `ui`, `image-generation`, `cli` and `run-directory`. Seventeen sit in `ADDED` blocks
and repay the seventeen markers one for one; **two more are new inside the `MODIFIED` block** — the
re-opened state, which no marker covers because `v0.22.1` did not build it. The block also restates the
two existing `ui:approval:*` keys unchanged, as a `MODIFIED` requirement must.

> ⚠️ **`openspec archive` cannot run end-to-end on this repository**, so the fold at release is done by
> hand. `v0.14 review/R11` exists because a hand-fold went wrong once, and this is the largest delta since
> `v0.18`. **Hand `tasks.md`'s fold note to `mf-release` before it folds.**

**Out of scope, on evidence.** The `.minions/minions.toml` → `Makefile` move is **not an isekai change**:
three MinionsFactory skills read that file and `mf-converge` **halts** on its absence. The framing that it
mirrors the `Makefile` is backwards — the `Makefile`'s own header says it mirrors *the array*. And a full
audit of all 261 scenarios is a version of its own; this one audits the four capabilities `v0.22.1`
touched, which is where a false scenario is most likely and least excusable.
