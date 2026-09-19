# Design — v0.18, the review UI

**Verdict: `feasible`.**

Two caveats, both priced rather than deferred. **The page ships the over-budget state untreated**: once
the count is taken over the assembled prompt, every real sheet clears 77 — measured 60–111 before the
~19 tokens of prefix and trailer — so the header's normal reading is `93 / 77` with the bar clamped and
no design behind it beyond a colour. And **the refusal surface is deferred**, so a `Refusal` reaching
the browser lands in one header line rather than a walkable queue.

See [`proposal.md`](proposal.md) for why.

## Context

```
  the pipeline, and where v0.18 sits
  ─────────────────────────────────────────────────────────────────────
  ①  caption    photo   → prose             claude binary   money
  ②  sheet      prose   → draft sheet       claude binary   money
  ③  review     draft   → approved sheet    a person        ◀── v0.18
  ④  generate   sheet   → renders           a rented GPU    money
  ─────────────────────────────────────────────────────────────────────
  ③ is the only stage that talks to nothing outside: no model, no
  network, no GPU. `wiring` builds a seam for ①②④ and none for ③.
  That is why the review UI is a small version, and why it was the
  right first page.
```

**What exists and does not reach a human.** `Vocabulary.search()` — substring over the whole tag, ranked
`(-count, tag)` — has one caller and it is a `spec_exempt` test. `assemble()` builds the exact positive
string the encoder reads. `Vocabulary.counts` holds the post counts that predict how hard a tag lands.

**What the record got wrong, and it was checked.** Ten module contracts have now been read against a
body and ten were wrong. The two that shaped this change: `wiring()` does not return a schema, and
`estimate_tokens` takes `(Mapping, Schema)` rather than a string — so the count the design session
specified did not typecheck, and three incompatible definitions of "tokens" were in play at once.

**How these decisions were reached.** A design session on 2026-09-17 produced the handoff imported at
`ui/design/` — eleven frames, six states, a keyboard model and a token sheet. A design review on
2026-09-18 worked out how it integrates, and an adversarial review on 2026-09-19 re-verified every claim
against a body rather than against a document: it settled fourteen decisions, overturned six of the
earlier ones and closed every open question. **This file is that record.** Nothing outside this
repository is needed to build the change.

## Goals / Non-Goals

**Goals.**

- A sheet is corrected on a surface that knows the vocabulary — canonical spelling, post count and token
  cost, none of which a text editor gives you.
- Both front ends reach the pipeline the same way, so neither is privileged and neither is a client of
  the other.
- Every refusal the batch can produce lands in the terminal before a URL is printed.
- The version stays small enough to read: two pipeline functions, one extraction, one guard fix, two
  refusal strings, one verb.

**Non-Goals.**

- Measuring anything. v0.19 scores; this version only makes correcting cheap.
- Covering ①②④. The verb that starts the server is a verb forever, so growth is additive.
- Replacing `$EDITOR`. `review` and `approve` stay fully working verbs — deleting the hand path would
  make ③ a single point of failure for the whole pipeline.
- Spending money **from the browser**. No control on the page reaches a model or a GPU; the one metered
  phase in this change is the acceptance run, driven from a terminal and gated on the operator.

## Decisions

### D1 — The UI is a sibling of the CLI, not a client of it

**Chosen:** both front ends call `wiring` and the stage functions directly. No subprocesses.

**This overturns the architecture record**, which settled on 2026-09-16 that the server would invoke
verbs as `python -m isekai <verb>` — on a page that says of itself that nothing below its contract
*"has been attacked."*

**The tell was in the design itself:** it called `review()` in-process at startup and `approve()`
through a subprocess. That line is arbitrary; both are verbs, and `cli.py`'s approve handler is
*resolve wiring, call `approve()`, print*.

**Alternatives considered.** The subprocess was claimed to buy three things. *It re-reads from disk, so
an unlanded autosave cannot be approved* — **false**, `approve()` reads `NNN.draft.json` itself either
way. *It is the same code path a human gets* — true, and equally true of a direct call. *It is the only
route, so the UI cannot be privileged* — not the only route without a test, and D11's grep is the
cheaper test.

**What it cost:** argv serialization, `--runs` forwarding, exit codes, and scraping stderr prose instead
of catching a `Refusal` — which matters, because `approve()` returns `(path, warnings)`.

**Consequence, accepted and recorded:** the structural guarantee that the UI cannot write its own
artifact is gone, and D11 replaces it with a cheaper one.

### D2 — Scope is ③ alone, seven of the design's eleven frames

**Chosen:** 1a, 2a, 2b, 3a, 4a, 6a, 7a, 7b. Out: 5a (refused), 4b (over budget), and everything the
design's own *Out of scope* lists.

**Closed by two independent statements** — the design handoff is ③-only and so is the operator's
workflow. Nothing in the browser spends money, which is a property of the scope rather than a guard.

**Consequence:** `P4`'s cost trigger — *anyone other than the operator triggering a run* — is untripped
**by construction**, and fires the day the UI grows a generate button. So do pool theme B and v0.21.

### D3 — The batch lives in server memory, and nothing orchestrates

**Chosen:** the batch is the invocation's argument list, held in memory. The directory is the only
state.

Nothing on disk says ten photographs belong together: `Run` is one input and the layout has no batch
object. Writing one down would be a new artifact in a layout whose own rules call a shape change a hand
migration. A restart loses the rail; one retyped command restores it; the sheets survive independently.

**Consequence:** the header line loses its date. `run 2026-09-17 · 3 inputs` has no source — a run id is
`<12 hex>_<slug>` — so it reads `summon-v1 · 3 inputs · 0 approved`. The approved count is read from
disk, so it stays true if something is approved elsewhere.

**An orchestrator was refused** because the stage order is a constant, and a component whose only
behaviour is a constant is a dispatch mechanism with nothing to dispatch. It would also be a second
thing that knows what is done, beside a directory that cannot lie.

### D4 — `TokenBudget`: one rule, three numbers

**Chosen:** a new public function in `review.py` returning `TokenBudget(total, per_field, overhead)`,
with `total` taken over `assemble(fields, schema.names, flow)[0]`.

**Three incompatible numbers were in play**, and the session that wrote the design never compared them:

```
  1a's sheet — 22 tags, 30 words
  ┌──────────────────────────────────────────────────────────────┐
  │ the design      words only                             30    │ drawn; the per-row
  │                                                              │ column sums to it
  │ the repo body   + separators + BOS/EOS                 53    │ approve()'s warning
  │ what ships      + prefix(9) + trailer(8) + 2 joins     72    │ what the encoder reads
  └──────────────────────────────────────────────────────────────┘
```

The rows sum into the total and `overhead` is the remainder, so the design's three numbers — the total,
the per-row column and `heaviest:` — reconcile instead of disagreeing.

**Alternatives considered.** *Let the UI count* — rejected: it puts a second copy of the tokenizer rule
in TypeScript, the exact duplication removed when `GET /api/tags?q=` replaced shipping 8,106 tags.
*Change `estimate_tokens` to take a string* — rejected: `approve()` would have to assemble, and it is
passed a `Schema` and never a `Flow`, so that is a signature change across 26 test call sites for a
warning on a deprecated path.

**Consequence, accepted and recorded:** `approve()`'s CLI warning still says **74** where the truth is
**93**. The surface that *is* the review path shows the right number.

**Risk:** `flow.py:393` is `fields.get(name, ())`, so a field absent from a mid-edit draft contributes
nothing rather than raising. Verified, because the budget is recomputed per keystroke.

### D5 — Approval is terminal in the browser

**Chosen:** once an input is approved its fields go read-only. The footer states the fact and names the
file. No control, no exit affordance.

**The design says the opposite three times** — 6a's *"Editing stays open. Changing anything returns this
input to edited"*, README's *"No separate 'approved then edited' state"*, and *"Nothing locks."* **All
three are overturned, because there is nothing on disk for them to write into:**

```
  approve()   ──▶ 001.approved.json      review.py:228
              ──▶ draft.unlink()         review.py:229   the draft ceases to exist
  next start  ──▶ review() → None        review.py:106   an approved input gets no draft
  a POST      ──▶ Refusal                review.py:222   approved is never replaced
```

**Alternatives considered.** *The first edit calls `review(new_version=True)`* — it works, and it spends
a version number on a stray keypress with no Save control and no confirm step to attribute it.
*Teach `save_draft()` to create* — gives it two jobs and puts it back in competition with `review()`.

**And the escape hatch does not exist yet, which is why none is offered.** *Generate a second sheet and
compare* needs three parts and the repo has one: `sheet --new-version` works; `review --new-version`
copies the **approved artifact** and never reads the new sheet (`review.py:116`, stated as the
requirement `review:copy:second-review-appends`); and `generate` resolves `approved[-1]`, so two
approved sheets still render one. Taking the middle part alone would cost a `MODIFIED` delta against a
requirement with a written rationale and buy nothing.

### D6 — 5a is deferred on cost, and the deferral is paid for twice

**Chosen:** no refusal queue, no `findings()`, no `POST /api/validate`, no suggestion buttons.

**The honest reason is cost, not unreachability.** `validate()` raises on the *first* problem;
5a's queue shows six at once across four kinds. That is a `findings()` function and a `Finding` type in
`shared/fields.py` — the largest diff the version would have had — and v0.18 does not open that file.

**Two things pay for it.**

**A `Refusal` gets somewhere to land.** The design supplies its own rule for states it specified and
deliberately did not draw: *"a header-level line stating the fact and naming the file — blunt, no modal,
and it must never imply the operator's work was lost."* One header line, the `Refusal` string verbatim.
That is applying the handoff, not inventing design.

**`save_draft()` refuses a changed field set.** Two lines at the one write point, no `Schema` parameter,
no `shared/fields.py`. It turns *missing field* and *unknown field* from a claim about an unbuilt UI
into a property of the write path. The other two kinds rest on the autocomplete committing only what
`search()` returned, which the vocabulary's load-time normalisation underwrites.

**Consequence:** the cost of being wrong is bounded — a refused approve leaves the draft untouched, so
the failure is confusing prose, never lost work.

### D7 — The empties gate is cut entirely, affordance included

**Chosen:** empty rows show the italic word `empty` and a hollow gutter ring. Nothing else mentions
them.

Removed: the `Mark N empty fields intentional` button, `Approve refuses an unmarked empty field.`,
`6 empty fields still unmarked.`, the `empty-claimed` row state, 6a's `cleared on purpose`, and 6a's
filled gutter dot for approved empties.

**Alternatives considered.** *Keep the block, client-side* — the design explicitly sanctions it
(*"the client may pre-empt obvious refusals"*) and it would have kept every string in three frames true.
*Keep the affordance without the block* — a control that marks something nothing reads is a control with
no consequence, and a dead control is worse than an absent one; the same argument cut the ② toggle's
pill.

**Consequence, accepted and recorded:** the design's *"empty-on-purpose becomes a recorded act"* goes —
it was always a claim about disk nothing here would write — and so does the attention aid that catches
*the sorter dropped `eye_colour` and I didn't notice*. The hollow ring still marks it; nothing insists.
**And the UI stops being stricter than the verb**, which closes a deferred row.

### D8 — `ui` is the tenth capability, not a section of `review`

**Chosen:** a new capability. `Source: isekai/interface/ui/ · Tests: tests/test_ui.py`.

**`cli` is already a capability for a front end**, with `isekai/__main__.py`, `cli.py`, `wiring.py` and
`run_view.py` as its source. The UI is the second front end and the precedent is exact.

**Alternatives considered.** *Under `review`* — its source line would gain a second module, against
`CLAUDE.md`'s *"nine capabilities, each a contract with one owner"*, and a gloss about correcting a
filled sheet would have to cover a port, a bundle and npm. Every `review:` key thereafter would need
reading twice to know whether it concerned the artifact or the server.

**The scenarios this adds are about serving** — the refusal order, one flow per invocation, the batch in
memory, the bundle, the invariant. None is an answer to *what is a valid sheet*.

**And the UI is expected to grow** until it runs the whole pipeline beside the CLI. Filing that under a
capability named for stage ③ would be wrong within two versions.

### D9 — The nine `## Purpose` lines land in phase 1, before the `ui` delta is authored

**Chosen:** add the heading to all nine living specs first.

**Measured, in a throwaway copy of `openspec/`:** two lines under `# Capability: \`review\`` turns
`✗ Spec must have a Purpose section` into `✓ Specification 'review' is valid`, and `requirements 0` into
`requirements 6`. No prose is written — the paragraph is already in every file; the fold that created
them kept the text and dropped the heading.

**The damage is larger than the hand-fold hazard it was filed under.** All nine report `requirements 0`,
so every `openspec` query against the living spec has been answering from an empty parse of 174 keys.

**And the fold rule itself is the bug, which is why order matters:**

```
  today       specs/ui/spec.md  ## Purpose     ──fold──▶  # Capability: `ui`
                                <prose>                    <prose>          heading dropped
                                ## ADDED                   **Source:** …    ⇒ requirements 0
                                                           ## Requirements

  after D9    specs/ui/spec.md  ## Purpose     ──fold──▶  # Capability: `ui`
                                <prose>                    ## Purpose       nothing dropped
                                ## ADDED                   <prose>          ⇒ valid
                                                           **Source:** …
                                                           ## Requirements
```

v0.18 is the first change since the rule was set to add a capability, and it folds four deltas at once.

**Consequence:** this changes no requirement, so it carries no delta of its own. `openspec validate` is
deliberately not in `make gate`, so the benefit is that the tooling stops lying, not that a gate goes
green.

### D10 — `security/S1` travels with the extraction that exposes it

**Chosen:** `_check_run_root` compares by `(st_dev, st_ino)` over `resolved` and its parents.

**Reproduced on the operator's machine:**

```
  REPOSITORY : /Users/alexey/Developer/AI_Engineering/isekai
  probe      : /users/alexey/Developer/AI_Engineering/isekai/runs    ← lowercase u
  resolve()  : /users/alexey/Developer/AI_Engineering/isekai/runs    ← case not folded
  samefile   : True                                                   ← it IS the working tree
  GUARD      : PASSED — a run root inside the tree, outside .data
```

`wiring.py:81` is `resolved.is_relative_to(REPOSITORY)`, a byte-wise prefix test. APFS opens the
differently-cased spelling, the refusal never fires, and a directory holding a copy of a personal
photograph lands somewhere `.gitignore` does not cover.

**Why it belongs here.** v0.18's one forced pipeline-side change is extracting the argv-free half of
`wiring()` so a server cannot skip this guard — *"a security property, not a convenience."* **Extracting
a guard to make it unskippable while leaving it broken on one axis ships a hardening that does not
hold, in the same module.**

**`os.path.normcase` will not close it** — it is a no-op on darwin. Traversal, symlinks, `..` segments,
relative paths and non-existent roots were all checked and are sound; case is the only failing axis.

**Risk:** the test is platform-dependent. CI is Linux, where the lowercased path genuinely does not
exist, so the case scenario probes the filesystem and skips where it is absent. The identity property
itself is asserted unconditionally.

### D11 — The invariant is one grep, and it is not the test v0.15 refused

**Chosen:** `envelope(`, `artifact_name(` and `write_json(` must not appear under
`isekai/interface/ui/`. `tests/test_ui.py`, stdlib only, in the main suite, bound to a scenario.

**The invariant:** *the UI server never constructs an artifact body or an artifact filename; it passes
field values to pipeline functions and they own the envelope and the name.* It replaces the structural
guarantee D1 removed.

**The notes flagged this as the same class as the AST import test v0.15 refused.** It is not. That
refusal had two clauses and **neither reaches this test**: *"a snapshot has no opinion about a new
edge"* — an import-graph snapshot records what is, so a new edge updates it and stays green, whereas a
fixed list of three forbidden names has exactly one opinion; and *"the errors it would catch live in
this record, which nothing in the repository reads"* — this one's failure is a server constructing
`002.approved.json` itself, which is code, with an artifact written around `approve()`'s `validate()` as
its consequence. **They differ in kind, not in narrowness.** The import test stays refused.

**Acceptance instead of a comment:** the docstring must say the test is a **tripwire, not a proof** —
`import artifact_name as name_it` walks past it and a hand-built f-string is invisible to it. A check
that overstates itself is worse than none.

**Why it earns its place:** `verifications.md` §3 measures what happens to an unenforced structural rule
in this repository. *"Modules connect through artifacts, not calls"* was **false six times** before
v0.15 and v0.16 closed it.

### D12 — The bundle is built on demand, and there are four ignored roots rather than one

**Chosen:** `ui/dist/` and `ui/node_modules/` are gitignored at the repo root and built on demand.

A committed bundle churns git on every build, because Vite emits hashed filenames.

**This falsifies a claim `CLAUDE.md` states as structural** — *"under one ignored root it is structurally
true instead, because there is nothing generated outside it to get wrong."* `models/` is the precedent
for the repair: the same paragraph already names a second untracked root and says how it fails
differently.

```
  .data/            captured or generated · loss is the loss of work
  models/           fetched from a pinned manifest · loss costs a byte-identical re-download
  ui/dist/          built from tracked source · loss costs a deterministic rebuild
  ui/node_modules/  fetched from npm · loss costs an `npm install`
```

**Not under `.data/`:** that root's failure mode is loss of work and `rm -rf .data` is an ordinary
cleanup. A rebuildable bundle in there muddles the boundary the paragraph exists to keep sharp.

- **The line is drawn at the network.** `vite build` runs automatically; a missing `ui/node_modules/`
  **refuses, naming `npm install`.** A build is local and free; `npm install` pulls arbitrary packages.
- **node is the repo's second system dependency, not its first.** `claude_cli.py:112` already runs the
  `claude` binary and `require_binary()` at `:118` is the refusal shape to copy.
- **Inter is vendored.** `styles.css:2` is a Google Fonts `@import`, which would make a private
  localhost tool reach a third party on every load and render in the wrong typeface offline. Four woff2
  weights land in `ui/src/assets/fonts/`. `ui/design/` is read-only, so the app takes a copy of the
  sheet regardless.

### D13 — What gets repaired, and the rule that decided it

**Chosen rule:** **repair what is inside a file this version is forced to open and made more
load-bearing; do not go into files it never touches.**

| | | |
|---|---|---|
| `security/S1` | **in** | the defect is in the function being extracted, and it falsifies the extraction's stated reason |
| `review.py:112` | **in** | names `python -m isekai sheet`, which exits 2 — and startup calls `review()` per input, so *you forgot to run `isekai sheet`* is this version's likeliest message |
| `review.py:224` | **in** | names the stage-first `review/<flow>/` that v0.16 deleted, in the same file |
| `review/R10` | **out** | `generate.py:453`'s unbounded poll. v0.18 never opens `generate.py` and puts no generate button in front of it |
| `generate.py:213`, `claude_cli.py:164`, `generate.py:180` | **out** | the same class as `review.py:112`, in files this change does not touch. **The real fix is the class**: `tests/test_resume.py:331` matches a remedy substring and never parses it — run each through `build_parser()` and the requirement stops being honour-system. v0.18.1 |

### D14 — The grilling outranks the notes, and the notes outrank the mockups

**Chosen:**

```
  this design.md   ▶   ui/design/
  the decisions        a reference to build against
```

The handoff says *"where this document gives an exact px value or an exact string, it is deliberate"*,
and taken at face value it instructs a builder to build the ② toggle and the caption highlight. **The
frame-delta table below is what overrides it, and nothing else does.** Everything not in that table
stays binding at full fidelity.

**The handoff is imported into this repository at `ui/design/`**, minus a 9.9 MB self-contained HTML
copy and the unbundled markup behind it, so the build never reaches outside the tree for a reference.
It is read-only: a design is corrected by re-running a session and replacing the folder.

## The API

**Six endpoints, and the flow is in none of their paths.** The batch has exactly one flow and
`/api/batch` names it; putting it in the URL would be designing for a hypothetical. A URL here is a
contract between a server and a Vue app in the same repository, so widening it later is a
find-and-replace.

```
  GET  /api/batch                 flow · schema · vocabulary size · inputs (w×h, status)
  GET  /api/tags?q=wav&limit=5    ──▶ vocabulary.search() + counts + rare   { matches, total }
  GET  /api/inputs/{id}           caption · sheet · draft · approved · TokenBudget · readonly
  GET  /api/inputs/{id}/photo     the bytes, whole — image.py reads headers, not pixels
  PUT  /api/inputs/{id}/draft     ──▶ review.save_draft()        WRITE
  POST /api/inputs/{id}/approve   ──▶ review.approve() → (path, warnings)   WRITE
```

**Two collapses, each deleting something.** The schema folds into `/api/batch`, because it is constant
for the batch and a second endpoint would serve one unchanging payload. And `GET /api/tags?q=` replaces
the design's `GET /api/vocabulary`, which had the client hold all 8,106 tags and rank them locally —
that deletes a 250 KB transfer and a second copy of the ranking rule, and `total` is the true match
count so the dropdown's footer can say how narrow the fragment got.

**What approval does to three of them** (D5): `GET /api/inputs/{id}` fills the form from `approved` when
`draft` is null and marks the input read-only; `PUT …/draft` refuses; the page offers no route to
`POST …/approve` once approved, and a stale tab reaching it meets `review.py:222`.

**Three write functions, all of stage ③'s** — `review()` at startup, `save_draft()` on autosave,
`approve()` on the button. That is the entire write surface, and D11's grep is what keeps it at three.

| the server owns | the pipeline owns |
|---|---|
| HTTP routing and status codes | what a valid sheet is |
| the batch: which inputs, in memory | the artifact envelope and filename |
| joining caption, sheet, draft, approved and budget into one payload | when approval is legal |
| the `rare` threshold — `posts < 2000`, which exists nowhere in the repository | prompt assembly and what a token costs |
| serving photograph bytes and the built bundle | anything that changes what the pipeline *means* |
| turning a `Refusal` into a response | |

## Frame deltas — read this before matching a screenshot

Ten deltas, every one a decision rather than a defect. The PNGs remain the reference for layout,
spacing, type, colour and behaviour.

| # | in the frames | what ships | frames |
|---|---|---|---|
| 1 | `Show ② draft` pill, 26×14px, header right | cut; the ON state is never drawn anywhere | 1a 2a 4a |
| 2 | `run 2026-09-17 · 3 inputs · 0 approved` | `summon-v1 · 3 inputs · 0 approved` — a run id carries no date | all |
| 3 | `runs/2026-09-17/sheets/00003.draft.json`, `00003.sheet.json` | `<flow>/review/001.draft.json`, `001.approved.json` | 1a 2a 3a 4a 6a |
| 4 | caption phrases tinted on focus; `dashed = no field claimed this text` | cut — `sheet.py:81` discards the phrases and the briefing forbids substring provenance | 1a 2a 3a 4a |
| 5 | `Mark 6 empty fields intentional`, `Approve refuses an unmarked empty field.`, `6 empty fields still unmarked.` | cut, D7 | 1a 2a |
| 6 | 6a: `all marked intentional`, `cleared on purpose`, filled gutter dot | `10 filled · 6 empty`; empties stay `empty` and hollow | 6a |
| 7 | 6a: `Editing stays open. Changing anything returns this input to edited…` | read-only; a line stating the fact and naming the file, D5 | 6a |
| 8 | `30 / 77`, `36 / 77`, `28 / 77` | `TokenBudget` counts prefix and trailer, so real sheets sit **above** 77; the bar clamps, the total takes `--color-accent` | 1a 2a 4a |
| 9 | 7b: `sheets written to runs/2026-09-17/`, `00003.sheet.json` | `<run>/<flow>/review/`, `NNN.approved.json` | 7b |
| 10 | 2a/2b's dropdown rows and counts | **not reproducible.** Measured: `blonde` returns two tags, not four — **`platinum blonde hair` is absent from the prediction set** — and `wav` returns `waving`, `waves` and `microwave` alongside the wavy ones. 2a and 2b are layout and behaviour references, never content references | 2a 2b |

**One figure the handoff apologised for is exact:** `models/wd14/selected_tags.csv` holds precisely
**8,106** category-0 tags.

## Build reference

**Component tree**, names from `components.md` — keep them or the docs drift. `RefusalQueue.vue` is gone
with D6; `useRun` becomes `useBatch` because *run* already means one input directory.

```
  ReviewApp.vue
  ├── AppHeader.vue        run line · receipts · the refusal line (D6)
  ├── BatchRail.vue        thumbnails · status marks · legend · the run entry
  │   └── StatusMark.vue   filled | hollow | dashed | half   (square went with 5a)
  ├── SourcePanel.vue      owns the 492/620px width rule
  │   ├── PhotoFrame.vue   .lighten img; click opens the overlay
  │   └── CaptionPanel.vue paragraphs only — no highlight, no dashed runs (delta 4)
  ├── SheetForm.vue
  │   ├── SheetHeader.vue
  │   │   └── TokenBudget.vue   total · bar · heaviest · clamp above 77
  │   ├── FieldRow.vue     ×N in schema order, never re-sorted
  │   │   ├── StatusMark.vue · TagChip.vue · TagInput.vue · TagAutocomplete.vue
  │   └── ApproveBar.vue   Approve, or the "Approved HH:MM:SS" fact (no empties action)
  ├── PhotoOverlay.vue     3a, teleported to body
  ├── RunManifest.vue      7b
  └── LoadingSkeleton.vue  7a
```

```ts
// FieldRow — the empty-claimed state went with D7
defineProps<{
  fieldKey: string          // rendered verbatim, monospace
  tags: string[]
  tokens: number            // this field's share of TokenBudget.per_field
  state: 'filled' | 'empty' | 'pending'
  readonly: boolean         // true once the input is approved (D5)
  focused: boolean
}>()

// TagAutocomplete
defineProps<{ fragment: string; matches: VocabEntry[]; total: number }>()
// VocabEntry = { tag: string; posts: number; rare: boolean }   rare = posts < 2000
```

**Build order**, from `components.md`, with its screenshot targets corrected for scope:

1. **Shell and tokens** — `styles.css`, `AppHeader`, `BatchRail`, `StatusMark` against a fixture.
   Getting the four marks right first makes every later state expressible.
2. **`SheetForm`, read-only** — rows from a fixture, schema order, chips, per-row tokens,
   `TokenBudget`. This is most of the pixels. ① and ② match `screens/01`.
3. **`useVocabulary` + `TagAutocomplete`** — keyboard only. **This is the piece that decides whether
   the tool is fast.** Matches `screens/02`, `03` for layout and behaviour, not for content.
4. **Editing** — `TagInput`, chip selection, add/remove/replace, `useSheet` with undo and autosave.
5. **Approve** — `ApproveBar`, `useApproval`, the approved state, its second receipt, read-only.
   Matches `screens/08`. **Not `screens/07`** — that is 5a.
6. **`PhotoOverlay`**, then **`LoadingSkeleton`** and **`RunManifest`**.

**Three things that are easy to get wrong**, verbatim from `components.md`:

1. **The dropdown must overlay, never displace.** Absolutely positioned under its row at `top: 30px`.
   If rows below it move, the operator loses their place while typing.
2. **Approve has no enabled twin and no Save button anywhere.** The two receipts are the only thing that
   talks about saving. If a Save control appears, the design has been broken.
3. **The per-row token number** is this field's share of `TokenBudget.per_field`, so the rows sum into
   the total and `overhead` is the remainder.

**Two design-system rules that are easy to break.** The accent is a **line and a mark, never a flood** —
primary buttons are a 1px accent border on transparent. And **status is shape-coded, not colour-coded**:
there is one accent and no error colour, so never substitute colour for a mark and never add a red.
`--color-neutral-600` is 4.08:1 on the ground and is **not available for text** — only hairline borders
and the chip ×.

**The keyboard model** is `ux-flow.md`'s, less the two bindings that went with 5a (`⌃↓`, `⌥⏎`):

```
  Tab / Shift+Tab        next / previous field, schema order
  Alt+← / Alt+→          previous / next input in the batch
  ← / →                  move chip selection within the focused field
  any character          opens the autocomplete on the first keystroke
  ↑ / ↓                  move the selection; row 1 preselected
  Enter                  commit; the caret stays in the field, fragment cleared
  Esc                    close the dropdown · Esc again clears the fragment
  Backspace (empty)      remove the last chip · with a chip selected, remove that chip
  type on a selected chip, then Enter   REPLACES it — the commonest edit in the job
  Cmd/Ctrl+Z / Shift+Z   undo / redo, per edit, crossing fields, cleared on input change
  Cmd/Ctrl+Enter         approve
  Esc (no dropdown)      close the photo overlay
```

**A fragment that matches nothing shows no rows and cannot be committed.** There is no path to free text
in a chip, and that is what underwrites D6's two remaining refusal kinds.

## Risks / Trade-offs

| risk | mitigation |
|---|---|
| **The over-budget header is the normal reading and has no design** | the clamp-and-accent rule is stated in delta 8 and is one line of CSS. 4b is the first row of the deferred list, and v0.19 draws it |
| **A `Refusal` in the browser has one line and no queue** | D6's header line carries the string verbatim, per the handoff's own rule for undesigned states. `save_draft()`'s field-set guard removes two of the four kinds structurally |
| **A stale tab `PUT`s into an approved input** | `save_draft()` refuses; the same header line shows it. Same class as the draft-vanished race |
| **The `-S` guard goes red for a reason nobody connects to the UI** | the `ui` handler imports FastAPI **inside the function**, and the phase that adds it states the reason in a comment at the import |
| **`image_dimensions()` calls `sys.exit()`** — a `BaseException` inside a request handler would take a worker down | it is called **only at startup**, phase 1. A second consumer inside the server is the trigger to fix it properly |
| **Nothing verifies `ui/dist/` matches `ui/src/`** | accepted; a sixth gate command would need a toolchain CI does not have. Deferred with its trigger |
| **The case-sensitivity test cannot run on CI** | the identity property is asserted unconditionally; only the case scenario probes the filesystem and skips |

## Migration Plan

**None required.** No artifact shape changes, no signature changes, no renames. Every existing verb
behaves exactly as it did, `review` and `approve` included — they are deprecated as *guidance*, never as
code, because deleting the hand path would make ③ a single point of failure for the whole pipeline.

Operators gain one system dependency: **node**, for `isekai ui` only. A missing one refuses and names
the fix, as `require_binary()` already does for the `claude` binary.

## Open Questions

**None.** Fourteen were settled in the 2026-09-19 grilling and every one is a decision above.

Deferred, each with what it blocks:

- **5a and the refusal surface** — needs `findings()` in `shared/fields.py`. **Blocks: a walkable
  refusal queue, the invalid chip, suggestion buttons.**
- **4b, the over-budget treatment** — **Blocks: nothing. It is the soonest thing on the list, because
  over-budget is now the normal case.**
- **The second-sheet path** — needs `review()` preferring a newer sheet, `generate` selecting a version,
  and the scoring that makes a comparison mean anything. **Blocks: correcting an approved sheet, and
  comparing two sorters on one photograph.**
- **A per-field tag cheatsheet**, asked for during the build and deferred on **data rather than on
  effort**: the overlay is small, and nothing in this repository is a machine-readable list of the tags
  that suit a field. Measured while building the autocomplete — the schema's `suffix` covers 6 fields
  of 16; the field name is noise (`age` reaches `cleavage` and `bandages`, `gaze` and `framing` reach
  nothing); and `sheet.briefing.md` does name good tags per field but as prose written for a model to
  read. So the change is a **new tracked artifact per flow**, and `flows/<id>/` is five flat files and
  immutable with a digest covering every regular file in it, committed at `tests/test_flow.py:30` — a
  sixth file is a new flow, not a variant. **Blocks: nothing.** Its own trigger is v0.19: scoring is
  what could answer *most suited* by measurement instead of by taste, so curating the list before it
  would be guessing.
- **The remedy-parsing check** — **Blocks: `cli:refusals:refusal-names-the-remedy` being enforced rather
  than honour-system.** v0.18.1.
- **Pool theme B and v0.21's `session()`**, and `review/R10` with them — **Blocks: a generate button in
  the browser.** Pulling them forward is a scheduling decision, not a detail.
