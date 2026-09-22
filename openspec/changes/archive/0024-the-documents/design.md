# Design — 0024 the documents

**Verdict: `feasible`.** Every decision below was settled against a body read at `main` `b4abe12`, after
`v0.22.1` was tagged and `0023-backlog-paydown` archived. A grilling preceded this change; **three of its
premises were overturned by re-resolving against HEAD rather than against the branch point**, and each
overturn is recorded at the decision it replaces.

## Context

`v0.22.1` was cut code-only and deferred every sentence here. It shipped eighteen fixes and left
seventeen tests bound to nothing but a marker pointing at this change. Separately, the repository
contains ten false claims about itself, six stale numerals in `CLAUDE.md`, wrong counts in every group
README, and no `docs/` at all.

**These are one debt, not two.** A claim in prose and a scenario in a spec are both the repository saying
what it does; one is checked by a reader and the other by the gate, and both are wrong right now.

---

## D1 — Sweep before writing

`docs/arc/` is drafted by reading the repository's own prose. Ten sentences of that prose are false, and
the single most relevant document to `modules.md` — `isekai/README.md`'s edge table — is one of them.
Writing first and correcting after would mean drafting a diagram from a source known to be wrong.

Phases: **sweep → `docs/arc/` → `CLAUDE.md` → spec prose → scenarios → rebind.**

## D2 — No quantities in `docs/`, and none left in the group READMEs either

> **Overturned premise ①.** The grilling opened willing to allow counts if a gate test pinned them. That
> test is the **import-graph gate test this project already refused**, at v0.15's grilling, on a recorded
> argument: *"a declaration the gate asserts against is a snapshot, not a check — it holds no opinion
> about whether a new edge is good, and the repair for a red run is to accept the edge."* Reviving it for
> a diagram revives the flaw.

**The weaker option — a disclaimed count — has already been tried in this repository and failed.**
`isekai/README.md:16-19` states its per-group file counts under *"**These counts are `ls` and nothing
else.** Two of them were wrong before v0.20 touched them … **Count; do not trust the row.**"*

At `b4abe12`, **two are wrong again**: `shared/` reads 4 against 5 files, `boundary/` reads 7 against 6 —
and `boundary/` is wrong in the *opposite direction* from the drift the paragraph describes. The
paragraph has become an account of its own current state.

**So the rule is: no quantity, anywhere this change touches.** A row naming
`atomic_write · field_map · fields · image · vocabulary` is self-counting and cannot rot the way `5` can.
This extends to the test-importer columns, where the audit found **eight wrong counts across five
files** — `foundation/README.md`'s *"fifteen test modules"* (16), `pipeline/README.md`'s *"nine"* (11) and
*"five"* (7), `boundary/README.md`'s *"five"* (6) and *"ten"* (9), `interface/README.md`'s two *"four"*s
(5 and 7), and `evaluation/README.md`'s *"three"* (2).

## D3 — `CLAUDE.md` is two files, not one bloated file

**165 of its 420 lines are description rather than instruction** — `## The path` (106) and `## Layout`'s
inventory (~59). The audit's verdict on the first: *"almost entirely data flow and architecture, with no
agent instruction in it."*

That is the answer to *why is this file huge*: a document that both instructs an agent and describes an
architecture grows forever, because every version adds to the architecture. `## The path` becomes
`docs/arc/data-flow.md`; `## Layout`'s per-group inventory is **deleted rather than moved**, because the
six group READMEs already hold it and moving it would create a seventh copy.

**What stays is what is rule rather than description**, plus a one-paragraph system summary **with a
stated ceiling in the file itself.** The ceiling is not decoration: that paragraph is how `## The path`
grew the first time.

## D4 — `docs/` owns the module graph; the README's edge table goes

Two drawings of one graph is how the existing one acquired three errors:

- **`boundary ──▶ shared` is missing**, and is module-level — `boundary/wd14.py:61`
- **the `shared ──▶ boundary` laziness is annotated backwards** — the prose marks only the `evaluation`
  reach as lazy, but **both** `vocabulary.py:126` and `:127` sit inside `load()`
- **`interface/ui` is collapsed away**, and that edge is lazy-only (`cli.py:254`) — a fact the same
  README treats as load-bearing elsewhere

The group READMEs keep their **file tables**, which are local facts. The **graph** is one drawing, in one
place. `isekai/README.md`'s structural claim survives and moves with it, because it is right and is the
most useful sentence in the file:

> *The module graph has no cycles and never has; the group graph does, and drawing it as a stack would be
> a lie.*

**Measured at HEAD, and unchanged since `bb01f79`:** no module cycles; exactly two module-level
subpackage cycles (`foundation ⇄ shared`, `foundation ⇄ boundary`); exactly three lazy cross-group edges
(`shared → boundary`, `shared → evaluation`, `boundary → evaluation`).

## D5 — `review` is right, and the code already says so

> **Overturned premise ②.** The grilling recorded this as *a defect `v0.22.1` introduced* — a refusal
> whose remedy dead-ends. **Re-resolved at HEAD, that is no longer true.** `v0.22.1`'s converge round 3
> (`review/R7`) reworded the refusal to state the limitation outright:
>
> *"…correct it with `python -m isekai review --flow F --new-version`, which writes a fresh draft beside
> the approved artifact for the command line to edit; **this page keeps showing the input approved and
> read-only either way, because the re-opened state is v0.22.2's** (design.md D5)."*
>
> The refusal is honest. What it is now is **a forward reference to this change**, in shipped code.

The disagreement it defers is between two live requirements:

```
ui/spec.md      "SHALL ... refuse a draft update against [an approved] input"
review/spec.md  "reviewing again appends a new numbered draft from the approved one"
```

**`review` is right.** `--new-version` exists for exactly this case, `review:copy:second-review-appends`
is older and has a test, and the surface is what had no way to show the result. `v0.22.1` closed the
disagreement the other way because that direction needed no spec delta — a constraint this change does
not have.

**The `ui` requirement is rewritten rather than deleted.** An approved input with no later draft is still
read-only and its artifact is still never edited in place. What changes is that an input deliberately
re-opened stops being reported as something it is not.

> ⚠️ **The hazard this creates, and phase 4 must hold it.** A third status splits two counts that agree
> today: `/api/batch["approved"]` is derived from the status string, `Batch.approved_count` reads the
> directory. `ui:batch:approved-count-comes-from-disk` is the scenario that catches the divergence, and
> the new `ui:approval:a-re-opened-input-is-not-counted-approved` is written to pin the same property
> from the other side.

## D6 — The sweep changes claims, not code

Where a claim is false, the claim changes. The named case: `boundary/README.md:4`'s *"nothing outside
this directory opens a socket or spawns a binary"* has **three violations** — `evaluation/labels.py:107`
spawns `git`, `interface/ui/bundle.py:131` spawns `npm`, `interface/ui/app.py:463` binds a port.

Moving those behind the boundary would keep the claim true and is the better repository. **It is not this
change**, and it is filed rather than dropped: a version already opening either module for another reason
should take it. A documentation release that quietly refactors is two changes wearing one name.

**D5's is the only code change here.** It is in scope because shipped code names this version as the one
that resolves it.

## D7 — `spec_exempt` is repaid, not re-borrowed

Seventeen markers carry `spec_exempt("behaviour; the scenario lands in 0024")` — **nearly a fifth of the
repository's ninety-five exemptions.** They group by the capability each scenario belongs to:

| capability | markers | what they cover |
|---|---|---|
| `ui` | 10 | Host/Origin validation (4) · the draft precondition (2) · bundle staleness (3) · panel dedup (1) |
| `cli` | 3 | flow-manifest validation at load |
| `image-generation` | 2 | transient transport · per-flow assembly |
| `run-directory` | 2 | `show`'s injected flows root · the mid-stream refusal |

`review`, `caption` and `tagging` carry **none** — the grilling had assumed seven capabilities and it is
five.

**Done means `grep spec_exempt tests/ | grep 0024` returns nothing.** The debt was made countable
deliberately; its discharge is countable for the same reason.

---

## Open questions

**None blocking.** Two are recorded rather than answered:

1. **A full audit of all 261 scenarios against the code.** This change audits the four capabilities
   `v0.22.1` touched. Two spot-checks during the grilling found two scenarios whose `THEN` was false
   *without looking for them*, which is the argument for the full pass and also the reason it is too
   large to carry here. **Filed.**
2. **Whether the spawns should move behind `boundary/`** rather than the claim being weakened — D6.
   **Filed.**
