# 0021 · the sheet comes from the tagger — design

**Verdict: `feasible`.**

Every phase is free, offline and deterministic except the two marked HUMAN. WD14 is a local ONNX pass,
the authoring script reaches no network, and the acceptance requires no render. **A pod is a halt.**

**Four audits were run against `main` at the cut, and every file:line below was verified against its body.
A citation that does not match the body it names is `design.md` contradicting the code — a halt, not a
divergence to work around.** This repository's record is eleven of eleven module contracts wrong at v0.18
and fourteen premises wrong at v0.20; the grilling that produced this document found **fifteen** wrong in
`roadmap.md § v0.21`, which is why the audits came before the decisions and not after.

---

## Context

The sheet is stage ② of a five-stage pipeline. Today an LLM reads stage ①'s prose and returns a field
structure, and the free-text phrases it emits are mapped onto canonical Danbooru tags by a four-pass
cascade in `isekai/shared/vocabulary.py`. Two sorter implementations exist, `ClaudeSorter` and
`OllamaSorter`, selected per flow by the manifest's `hosted.sorter` key.

v0.20 shipped a second producer for the same photograph: `boundary/wd14.py`, a pinned local ONNX tagger
whose output layer **is** the flow's vocabulary — row N of `selected_tags.csv` names neuron N — so its
tags are canonical by construction rather than by luck. It is advisory: `ui/app.py:136` shows its list
beside the prose and nothing consumes it.

This version makes it the sheet's author. The operator's verdict after v0.20's acceptance was *"the
highest impact is the WD14 danbooru tags."*

**What is measured and what is not.** `notes/v0.19_improvements/ui.md` settled that *sheet fidelity stops
being a metric* — the operator rewrites every sheet to his own taste regardless — so the number that
matters is how much typing the draft saves, and the acceptance is his judgement plus one recorded ratio.

---

## Goals / Non-Goals

**Goals**

- The sheet is filled by a model that cannot invent a tag.
- The operator can see every candidate tag for every identity criterion the flow declares.
- One authored artifact serves both, read in two directions.
- Both sorters and the free-text cascade leave the tree.

**Non-Goals**

- **`caption()` and the WD14 boundary are not touched.** This version changes who fills the sheet, not
  who reads the photograph. `boundary/wd14.py` is byte-identical in the diff, floor included.
- **No flow is re-pinned.** All three flow directories stay byte-identical and `tests/test_flow.py:PINNED`
  passes untouched.
- **No new component, colour, spacing or type step.** The overlay composes what v0.18 and v0.20 ship.
- **No comparison against Qwen.** See D2.
- **No in-field picker, no field-aware ranking, no sentence labels.** Deferred, each with a trigger.

---

## Decisions

### D1 · The brief's numbers were n=3, and at n=8 three of the four Qwen columns halve

**`roadmap.md § v0.21` was measured on three photographs from `.data/v0.19/runs/`.** v0.20's acceptance
batch is eight runs at `.data/v0.20/runs/`, each carrying `captions/`, `wd14/`, `tags/`, `sheets/` and
`review/001.approved.json`, so the re-measurement cost one disk read.

| | n=3 | n=8 | |
|---|---|---|---|
| approved tags | 67 · 22.3/photo | **200 · 25.0/photo** | holds |
| Qwen supplies, of approved | 37 · 55% | **67/200 · 33.5%** | halved |
| Qwen precision | 37/43 · 86% | **67/119 · 56.3%** | worse |
| Qwen deletions | 6 · 2.0/photo | **52 · 6.5/photo** | 3.25× worse |
| suffix routing of approved | 8/67 · 11% | **9/200 · 4.5%** | worse |
| hand-typed that WD14 already had | 13/30 · 43% | **128/133 · 96%** | far better |
| WD14 offers at 0.15 | 33/photo | **35.2/photo** | holds |
| WD14 offers at 0.40 | 22/photo | **20.1/photo** | holds |

**Replaying the n=3 measurement reproduces the brief exactly** — 67 approved, 43 drafted, 37 kept, 6
deleted — so the brief was measured correctly and the batch moved.

**Two of the brief's cells are the same measurement.** At n=3 *and* n=8, **zero** drafted tags survived
into a *different* field than they were drafted in. "Right field" and "precision" therefore read the same
number, and the brief's sentence *"Qwen's real contribution is routing"* is not what the data shows —
Qwen does not mis-route, it mis-identifies. **The case for the table is unchanged and stronger**: the
routing Qwen performs is the routing nothing else can perform, because ten of sixteen fields have no
lexical anchor at all.

**Where the sheet actually lives:** **102 of the 200 approved tags are in `clothes`, `pose` and
`body_shape`**; Qwen supplies 13 of them; none of the three declares a suffix.

### D2 · The acceptance compares the router to nothing, because the only available baseline is circular

**`ui/app.py:136` puts `"wd14": _wd14(batch, held)` on the review page payload, and the panel shipped in
`d13df42` on 2026-09-20 — before the v0.20 sheets were approved.** The v0.19 sheets were approved blind
on 2026-09-19; the v0.20 sheets were approved with WD14's list on screen. So "WD14 supplied 86.5% of the
approved tags", "61.3% precision", "13.6 deletions a photograph" and the 97.5% union are **upper bounds on
a circular measurement**, not a re-measurement of the brief's blind figure.

**So the brief's stated baseline — *"Qwen's measured 86% precision and six deletions"* — is retired on two
counts: it does not exist at n=8 (56.3% and 6.5/photo), and the thing it would be compared against cannot
be measured cleanly from this batch.** At the operator's call, **Qwen is not a baseline at all.** The
acceptance is the router's draft on fresh photographs, judged directly, plus one recorded ratio.

*The clean alternative was rejected as not worth its cost: a blind acceptance with the WD14 panel hidden
would measure precision honestly and would also remove the panel the operator uses to work.*

### D3 · The floor stays 0.15, and the reason in the record changes

**Two findings against `boundary/wd14.py:98`, `FLOOR = 0.15`:**

**The artifact is written post-filter.** Per-run minimum confidences across the eight runs are 0.1502,
0.1509, 0.1516, 0.1562, 0.1577, 0.1601, 0.1645, 0.1733. **Nothing below 0.15 exists on disk**, and
`onnxruntime` is absent from both the system python and `.venv`. **The brief's "19 of 30 at 0.02" is
unmeasurable**, and it is not worth buying: at 0.15 WD14 already holds **96%** of everything the operator
typed by hand.

**And the floor table's direction is false.** Measured over the eight:

| floor | offered/photo | supply of approved | precision |
|---|---|---|---|
| 0.15 | 35.2 | 86.5% | **61.3%** |
| 0.20 | 29.4 | 74.0% | 63.0% |
| 0.30 | 24.8 | 60.5% | 61.1% |
| 0.40 | 20.1 | 49.0% | **60.9%** |
| 0.70 | 12.0 | 28.5% | 59.4% |

**Raising the floor trades recall away one-for-one and buys no precision.** The brief argued *"the operator
chose recall and review"* from a table claiming 33% → 42%; the real table says the lever does not exist.
**0.15 stands because it is the lowest value available and raising it costs recall for nothing** — and
because the table, not the floor, is the filter that matters: a tag that routes to no field never reaches
the sheet.

### D4 · A tag has exactly one `primary` field, and may appear in several groups

**The roadmap's gate check *no tag appears in two field groups* is falsified by the operator's own approved
sheets.** Measured over the eight, 3 of 113 distinct approved tags are filed in more than one field:

```
  navel       -> clothes, pose, body_shape
  collarbone  -> pose, body_shape
  standing    -> framing, pose
```

**And a fourth case is structural rather than statistical.** WD14 offers `lips` at 0.157 on a `summon`
photograph, and the operator filed `lips` and `parted lips` under **`expression`** — while `lips` is a
**declared field** on `conjure` (`flows/conjure-v1/schema.json`). One vocabulary-keyed assignment cannot
serve both flows.

**So the table carries both:** a `primary` field, which is what the router writes to, and any further
groups the tag may be browsed under, which is what the cheatsheet shows. **One table, two indexes** — the
version's own thesis, applied to the one place single assignment breaks. The gate check becomes **every
tag has exactly one primary**, which is decidable the moment the table exists and is the property the
router actually needs.

*The second check the roadmap names survives verbatim: no tag is in both a group and the excluded list.*

### D5 · Only `wd14/` fills the sheet. JoyCaption's list stays advisory

**Measured over the eight:** WD14 alone covers **173/200** of the approved tags; adding JoyCaption's
`tags/` list covers **180/200** — **+7 tags across eight photographs**, for 30–40 free-text tags a
photograph of which **85% are outside the pinned vocabulary** (42 of 282 in vocabulary, corroborating
`app.py:224`'s *"roughly nine in ten outside the vocabulary"*).

**+0.9 tags a photograph does not buy back a dependency on a hosted model.** And it would cost the
provenance claim: the sheet's producer gains `pinned: true`, which is honest with one pinned producer and
a lie with two. **`tags/` is also flow-conditional** — only `summon-open-v1` declares a `hosted` block, so
the list is `null` on the other two flows, and a sheet whose recall depended on it would differ per flow
for a reason no manifest states.

### D6 · The sheet stays `{field: [tag]}`, ordered by the tagger's confidence descending

**No implication collapse** — WD14 emits Danbooru's hierarchy, so one garment arrives four times
(`underwear 0.94 · panties 0.91 · highleg panties 0.80 · white panties 0.64`), all correct, all in the
vocabulary. This is carried deliberately: the operator's approved sheets contain `underwear`, `panties`
**and** `black panties` on the same photograph, so collapsing would delete tags he keeps.

**The ordering is therefore the deletion aid, and it is free.** Confidence descending puts the general
forms above the specific ones in the field, which is the order he deletes in. **A per-tag
`{tag, confidence}` body was rejected**: it would take the sheet to schema version 2, and `review.py`,
`flow.assemble()` and the whole review surface read `fields` as lists of strings.

### D7 · The cheatsheet cuts nothing, and the post-count cutoff is refuted by measurement

`clothes` is ~800 tags from 20 seeds — too many to browse. The roadmap named sub-grouping or a post-count
cutoff and solved neither; `ui.md` § ① called the cutoff *"the curation rule already available for free …
a mechanical rule, not taste."* **Measured against the operator's own approved tags, it is false:**

| cutoff | `clothes` 802 → | approved tags it would hide |
|---|---|---|
| >100,000 | 35 | **50 of 113** |
| >20,000 | 124 | **18 of 113** |
| >10,000 | **197** | **10 of 113** |
| >1,000 | ~780 | 0 |

**The tags he reaches for are in the tail** — `gold bracelet` 2,081 · `train station` 2,180 ·
`looking at phone` 2,971 · `tube dress` 1,274. And the pinned vocabulary's minimum is **611**, so the only
safe cutoff is a no-op.

**So the overlay shows every tag in the group and ships a filter input.** Length stops being the problem
once the list is filterable — `ui.md` § ⑤ already reached this conclusion from the other side
(*"collapsed and filterable, length is the point rather than the problem"*). **The post-count tier from
§ ⑨ is shown and nothing is dropped**, which keeps the long tail visible without deciding for him.

### D8 · The excluded list is defined semantically, and the batch only generates candidates

The list says which absent tags are **decisions rather than gaps**. Deriving it empirically — every WD14
tag above the floor that never reached an approved field — was measured and **rejected**: 43 such tags
exist over the eight, and they conflate two kinds.

```
  never a criterion    realistic ×8 · photorealistic ×8 · artist name · photo background
                       · foreshortening · holding
  wrong about THIS     bra ×3 · dress ×2 · high heels ×2 · thighhighs · sweater · shorts
  photograph           · leotard · pantyhose · fishnets · lace · lace trim
```

**Excluding the second group would silently shrink `clothes` by seven ordinary garments.** So the 43 is a
candidate generator the operator prunes, and the list's definition stays *no criterion can hold this*.

*`realistic` and `photorealistic` are dropped by the router anyway, since they belong to no field. The
list exists to say that those absences are deliberate, and a gate check asserts no tag is in both.*

### D9 · Every one of the 21 declared fields has an entry, and an empty entry is legal

The union of the three flows' schemas is **21** fields — `conjure-v1` is a strict superset of the
sixteen `summon-v1` and `summon-open-v1` declare byte-identically, adding `bangs`, `eyelashes`, `nose`,
`lips` and `facial_hair` in place.

**Two of the 21 are empty in the operator's own ground truth**: over eight photographs `age_band` is
approved **0** times and `marks` **0** times, and `accessories` twice with WD14 covering neither.
`age_band` has no candidates in the vocabulary at all. **`eyelashes` holds four tags in total** —
`eyelashes` 128,622 · `colored eyelashes` 23,255 · `long eyelashes` 4,797 · `thick eyelashes` 1,268.

**So the gate asserts every declared field has an *entry*, not a non-empty one.** An empty group is the
honest answer for a criterion the vocabulary cannot express, and the cheatsheet saying *nothing here* is
better than the cheatsheet omitting the row. *Dropping `age_band` from the schema was rejected as out of
scope: it re-pins three frozen directories.*

### D10 · Nothing this version ships on the surface has a mechanical check, and the version says so

**There are no UI tests in this repository** — no vitest, no playwright, no jsdom, no `*.spec.ts`. The
gate's whole browser half is `scripts/typecheck_ui.sh` → `vue-tsc --noEmit`, whose own header calls itself
*"the only mechanical check it has."* And it type-checks the *source* while the server serves the *build*,
a gap that already shipped a defect silently (`bundle.py:42-57`).

**So the test weight is carried by the parts that can carry it**: `field-map`'s four checks and the router
are pure Python and fully testable, and `/api/fields` is testable in `tests/test_ui_api.py`. **The two
keystrokes and the overlay's behaviour are verified by the operator in a named HUMAN phase**, and
`tasks.md` says so rather than letting a green gate imply otherwise.

**This is also why the `ui` spec delta contains no keyboard scenario.** All 19 of that capability's
existing scenarios are `Layers: unit` and server-side; a scenario nothing can prove is worse than an
honest human phase. *A browser test runner is named for v0.22.1.*

### D11 · `Option+F` ships, and the brief's "three lines" is wrong by an order of magnitude

Three findings against `PhotoOverlay.vue`:

1. **It is not full-screen and never was.** `app.css:591` `.overlay { position: fixed; top: 41px; … }` — it
   deliberately sits below the app header so the run line and the save receipt still read, and
   `.overlay__photo { max-height: calc(100vh - 140px) }`. It is a two-column lens, photo plus caption.
2. **It contains no keyboard handler at all.** Escape closes it from `ReviewApp.vue:271`; arrows step the
   batch from `ReviewApp.vue:274`. `PhotoOverlay.vue:23` declares a `step` emit **it never emits**, and
   `ReviewApp.vue:424` binds it — dead code that reads as the mechanism.
3. **Focus is the actual diff.** Today the opener is a `<button>` (`PhotoFrame.vue:25`), so opening moves
   focus out of the tag field. A keystroke opener does not — and without a focus move,
   `PhotoOverlay.vue:89-90`'s printed *"Editing is suspended while the photo is open — the sheet is behind
   this, untouched"* becomes **false**, `TagInput.vue:88`'s `stopPropagation` **eats Escape**, and `←`/`→`
   **double-fire** (chip selection at `TagInput.vue:101` plus batch step at `ReviewApp.vue:274`).

**It ships anyway, because the focus discipline is bought for `Option+Space` regardless** — the cheatsheet
opens from the same tag field and needs the same round-trip. Real diff: ~15–25 lines across
`ReviewApp.vue`, `TagInput.vue` and `SourcePanel.vue:69`'s `'click to fill window'` string, plus the dead
`step` emit removed.

### D12 · The overlay composes `.overlay`, not the unused `.dialog`

`styles.css:320-336` defines `.dialog-backdrop`, `.dialog`, `.dialog-title`, `.dialog-body` and
`.dialog-actions` — **zero references in any `.vue` file**, and `.dialog` is capped at
`width: min(440px, 100%)`, which is wrong for an 800-row group. `PhotoOverlay` is bespoke: its own
`.overlay*` block at `app.css:586-668` and the only `Teleport` in the app.

**So the cheatsheet reuses `PhotoOverlay`'s ground** — the same `Teleport to="body"`, the same `top: 41px`,
`.overlay__controls` / `.overlay__exit` / `.overlay__foot` for chrome, `.kicker` + `.source__head` for
section heads, **`.row__tags` + `TagChip.vue`** for the grid, `.input` for the filter, `.drop__posts` for
counts, `.mono` for keystrokes. **Not one new component, colour, space or type step** — exactly the reuse
`SourcePanel.vue:89-92` already performs under v0.20's D21.

### D13 · `GET /api/fields`, fetched once when the overlay first opens

**No existing data path can serve `field → tags`.** The vocabulary is a flat `Mapping[str, int]` with no
field dimension; `/api/tags` takes `q` and `limit` only (`app.py:85`); and `TagInput`'s `field` prop is
used solely for `:data-field` re-focus and never reaches the query.

**So one new endpoint**, returning the whole table once as `{field: [{tag, posts}]}`. ~2,126 tags is ~40 KB,
and the overlay's filter is then instant with no round trip per keystroke. *Riding `/api/batch` was
rejected — it taxes every page load for a surface that may never open. `?field=` was rejected — a round
trip per field, and it pre-builds ⑦ which is deferred.*

**The excluded list is not served.** It is a build-time assertion, not a thing the operator browses.

### D14 · Both bindings match `event.code`, and the rule's reason is not a layout switch

**`event.code` appears nowhere in this repository** — `grep -rn "event\.code"` over `ui/`, `isekai/`,
`openspec/` and `tests/` returns zero hits. Every one of the app's two handlers matches `event.key`. **So
this is the first such binding and not the second**, and the brief's stated reason is wrong even on the
only layout the operator cares about:

- **`Option+Space` emits U+00A0 on macOS on every layout**, and an invisible nbsp in a tag field
  reproduces the silent dead end this whole feature exists to remove. `TagInput.vue:92` swallows a space
  only via `event.key === ' ' && fragment === ''`, so U+00A0 falls through every branch into `v-model`.
  Event order works in our favour: the element handler runs before the `window` bubble handler, so a
  `event.code === 'Space' && altKey` branch at window still cancels the insertion.
- **`Option+F` emits `ƒ` on plain ABC.**

**Option is a character-producing modifier on macOS. That is the rule, and it holds on US English alone.**

**`preventDefault` is load-bearing, not hygiene, for a second reason the brief omits**: `Option+Space` can
land while a `<button>` has focus — `BatchRail.vue:41`, `PhotoFrame.vue:25`, and `ReviewApp.vue:292`
focuses `.rail__card--current` on mount — where Space is the native activation key. Without it the
cheatsheet keystroke also re-selects an input or opens the photo overlay.

**`ReviewApp.vue:243` matches `Cmd+Z` on `event.key.toLowerCase() === 'z'`, so undo already does nothing
under a Cyrillic layout — a live violation of the rule this version writes.** At the operator's call it is
**not fixed here**: the focus is macOS English. It goes to the backlog, and the operator has asked for **a
keybinding re-work as its own version**, which is where `useKeyboard()` — specified at
`ui/design/components.md:76` and never built — belongs.

### D15 · The authoring script reaches no network, and Danbooru's implication graph is deferred

**`research/danbooru/tag_examples.py` does not contain the mechanism the roadmap credits it with.** It is
an image fetcher: it calls `/tags.json?search[name]=` (exact) and `/posts.json`, and **there is no
`search[name_matches]` call anywhere in the code** — the wildcard appears in one place in either tree, as
prose in the README. Its five documented rounds are all about fetching safe, well-composed *examples*;
none of them produces a seed number.

**But the route needs no Danbooru at all, which is the decisive finding.** A Danbooru wildcard intersected
with the pinned vocabulary **is** a substring match against the pinned vocabulary. The seven
`hair_silhouette` seeds at `ui.md:575` reproduce **63** tags from `models/wd14/selected_tags.csv` in
milliseconds, offline. **The 240 candidates Danbooru would return are the 74% that get thrown away.**

*One caveat: `selected_tags.csv` is gitignored and provisioned by `scripts/download_models.sh` against the
committed sha256. A CI check over the authored table needs the same fetch every existing vocabulary test
already needs, and it is free.*

**Danbooru's `tag_implications` endpoint is deferred.** It would sub-group `clothes` mechanically —
`white panties` → `panties` → `underwear` → `clothes` — and it is the one thing Danbooru knows that the pin
does not. It is refused here because D7 chose the filter, which makes 800 rows navigable without a
hierarchy, and because a build-time HTTP dependency for a display nicety is not worth it in a version this
size. *Trigger: if the filter proves to be the slow part in use.*

### D16 · The `hair` group is one derived set serving two fields, and the router splits it on a colour test

`hair_colour` and `hair_silhouette` both declare the suffix `hair`, so both derive the **identical 103
tags**. `ui.md` settled *"one flat group, decided 2026-09-20 — the operator is content to browse all 103
together"*, which is right for the cheatsheet and impossible for the router: `long hair` must have one
primary.

**The split is mechanical, and the operator's own sheets prove it separates cleanly:**

```
  hair_colour      brown hair ×5 · blonde hair ×2 · black hair
  hair_silhouette  long hair ×7 · wavy hair ×6 · straight hair ×2 · medium hair
```

**A `hair` tag whose non-suffix words contain a colour word gets `hair_colour` as its primary; every other
gets `hair_silhouette`.** Both fields list all 103 in the cheatsheet, so nothing is hidden from browsing.

### D17 · The builder seeds seven fields and harvests the dead briefing; the operator finishes in one handback

**Only 7 of the claimed 63 seeds exist on disk** (`ui.md:575`, for `hair_silhouette`). The other ~56,
including `clothes`'s 20, are in no file in either tree. **So `2,126 tags` and `900 tags` are findings, not
numbers**, and the roadmap's *"naming ~7 concepts per field instead of listing ~100 tags"* understates the
work: seed expansion is dirty by construction, and the flagship number proves it — **≥6 of the celebrated
63 are not hair tags at all**: `playboy bunny` 82,752 · `reverse bunnysuit` · `nontraditional playboy
bunny` · `male playboy bunny` · `bunny day` · `setsubun`, every one from the seed `bun`. The `scar` →
`scarf` defect is *inside* the number the roadmap quotes.

**So the work is split where the taste boundary actually is.** The builder does the mechanical half: the
script, the hair split, and seeds for the **seven fields the measurement says carry the weight** —
`clothes`, `pose`, `body_shape`, `expression`, `gaze`, `framing`, `background`, the first three holding
102 of the 200 approved tags. It also **harvests `sheet.briefing.md`**, which names roughly **40 example
tags across 10 of the 21 fields** — the only authored group content that exists anywhere, in the file this
version carries dead.

**Then one HUMAN handback**, placed last before the acceptance, in which the operator prunes the groups,
seeds the remaining fields, and prunes the excluded list. **An unfinished group is legal** (D9), and the
acceptance's own sub-claim — *I reached a tag I could not previously name* — is the completeness test.

### D18 · Word-boundary matching is not the fix the roadmap prescribed

The roadmap's remedy for `scar` → `scarf` is *"Word-boundary matching, not `in`."* Measured: `\bscar\b`
takes 44 matches to 15, which is right — and applied to the seven hair seeds it takes **63 → 51** and
sheds real tags with the junk: **`twin braids` 153,036 · `side braids` 6,720 · `low twin braids` 5,536 ·
`multiple braids` 1,868 · `tri braids` 805 · `braided hair rings` 3,917**, all failing `\bbraid\b` on the
plural.

**So a seed is matched on word boundaries against both its own form and its plural**, and the script
prints what each seed pulled in so the operator's pruning pass sees the junk rather than inheriting it.

### D19 · `field-map` is the twelfth capability, and `sheet` stays `sheet`

**There is no rule `L17`, and no `L<n>` numbering scheme exists anywhere in this repository** — the
roadmap's *"L17 says a capability has one owner"* cites nothing. The real rule is **`CLAUDE.md:134-137`**:
the living spec is *"`openspec/specs/<capability>/spec.md` … each a contract with one owner"* — which means
**one spec file owns one contract**, not one module owns one capability. *That sentence is itself stale: it
says "ten capabilities today" and `ls -d openspec/specs/*/` returns eleven since `0020` archived. This
version makes it twelve and corrects the sentence.*

**`sheet`'s eight survivors are all about the artifact's shape and its schema** — stores fields only ·
empty field is legal · names its vocabulary · no tag outside the vocabulary · field order declared once ·
identifier-safe names · schema read from the flow · vocabulary declared by the flow. **The table's own
contract is about none of them**: completeness over the declared fields, one primary per tag, resolution
against the pin, and disjointness from the excluded list. Those are requirements about an artifact, and
they get their own file.

**`sheet` keeps its name.** The artifact is still a sheet, the verb is still a verb
(`cli:flow-selection:every-stage-verb-accepts-it` requires it), and renaming a capability to record that
its author changed would move every key in it for no gain. **The new capability owns the table, not the
filling.**

### D20 · The router is built before anything is deleted, and the retirement is two phases

**The gate forces the spine.** Deleting the sorters before the router exists ends a phase with nothing
able to fill a sheet; so the router lands first, and `sheet()`'s signature change drags the seam's removal
with it — 46 reference lines across ten test files plus `tests/stages.py:48` pass a `FakeSorter` to a
wrapper whose signature moves.

```
  1  field-map: the artifact, the loader, the four checks
  2  the authoring script, the seven seeded fields, the briefing harvest
  3  the router fills the sheet — wd14/, the refusal, the provenance, the seam unwired
  4  retirement one: the sorter bodies and their ten scenarios
  5  retirement two: the free-text cascade
  6  the documents this version makes false
  7  /api/fields, the overlay, and the two keystrokes
  8  HUMAN — author the remaining groups, prune the excluded list
  9  HUMAN — the acceptance
```

**Two retirements rather than one or three.** The sorters and the cascade share only `sheet.py` and orphan
different tests, so they are two revertible units. The spec delta is **not** separable from either — it
lands with the code it describes.

### D21 · An absent `wd14/` is a refusal, and one `CLAUDE.md` rule narrows

`sheet.py:355-365` reads `run.directory(flow, CAPTIONS)` and refuses when `latest()` is `None`. The swap
to `WD14` is **one line**, plus the refusal text. `CAPTIONS` keeps four consumers, all of which survive:
`ui/app.py:127,132` (the source pane, pinned by
`ui:source:the-caption-is-shown-one-sentence-to-a-block`), `ui/batch.py:92`, `run_view.py:49`'s `STAGES`,
and `caption.py:252`. **Neither the prompt assembly nor the evaluator reads `captions/` at all.**

**But `CLAUDE.md:270` says a missing tag artifact is *"an absent aid, never a refusal."*** After this
version `wd14/` is load-bearing and `sheet()` must refuse without it. **The rule is narrowed to the
hosted tagger**, which remains an aid, and the local tagger becomes a prerequisite named in the refusal.
*Writing an all-empty sheet instead was rejected: `sheet:output:empty-field-is-legal` makes it legal and
therefore silent, which is the failure mode this repository keeps paying for.*

**`CLAUDE.md:263` also goes false** — *"prose first because it is the only one anything downstream reads"*.
After this version WD14 is the only one anything downstream reads. The ordering stays as it is; the
sentence is corrected.

### D22 · Two artifacts are carried dead, not one

**`sheet.briefing.md`** stays. `manifest_digest` (`flow.py:437-451`) hashes every regular file's **name and
bytes**, so leaving it in place keeps all three flow digests bit-identical and `tests/test_flow.py:PINNED`
green. Deleting it would move all three, which `CLAUDE.md:196` makes a new flow id and would drag v0.22's
whole flow re-creation forward.

**Two corrections to the brief.** It is **not** *"read by nothing"*: `load_flow` **refuses any flow missing
it** (`flow.py:407`, `SIBLINGS` at `flow.py:59`), so it is stat'd on every flow load. And it **is**
referenced by golden digest constants and by five content-reading tests at
`tests/test_sheet_stage.py:363-430`. Four of the five die — `:381` calls `map_phrase`, and `:406`, `:419`,
`:427` assert sentences in instructions nothing follows. **`:364` is kept**, because *every field name the
briefing mentions exists in the schema* is still a real consistency check.

**And the brief names only one carry when there are two. `Hosted.sorter` is a *required* manifest key** —
declared at `flow.py:234`, read unguarded at `flow.py:429`, asserted by three tests. Removing
`"sorter": "qwen3:8b"` from `flows/summon-open-v1/flow.json` moves that flow's digest and makes it a new
flow. **It stays in the manifest, unread, exactly like the briefing.** *Both have the same trigger: v0.22,
which deletes the flows they belong to.*

### D23 · Fourteen scenarios die, 31 bindings orphan, and nothing in the gate would notice

`openspec/specs/sheet/spec.md` holds **22** scenarios, not the 21 the roadmap states. Fourteen are
REMOVED and they land exactly on the roadmap's estimate:

```
  5  sheet:mapping:*      with the cascade
  5  sheet:selection:*    with the sorters
  3  sheet:seam:* + sheet:failure:*   one requirement, three scenarios
  1  sheet:purity:absence-clause-is-dropped
```

**Eight survive.** The 14 carry **31 `@pytest.mark.spec` bindings**, and **`CLAUDE.md:158` states there is
no spec↔test binding checker in this repository** — so a marker naming a deleted scenario passes the gate
green. **`tasks.md` lists all 14 keys by name as a deletion checklist.** *A checker is ~20 lines and is
named for v0.22.1; it belongs to a different capability than this version's work.*

### D24 · The router is a dict lookup, because `map_phrase` would eat tags from the ground truth

`map_phrase` has **exactly one production caller — `sheet.py:93`, inside `fill()`** — verified across every
file type in the tree. But the roadmap's inference that *"the cascade would reach its first pass and never
the other three"* mis-describes the body twice:

- **The first thing in `map_phrase` is not a pass.** `vocabulary.py:308-310` runs `normalise()` then
  `asserts_absence()`, and returns `[]` on a hit. Sweeping the whole provisioned vocabulary through it
  measures **37 of the 8,106 canonical tags dropped before pass 1 ever runs** — including `no humans`
  113,058 · **`no bra` 93,761** · **`no panties` 87,258** · `no shoes` 77,591 · `otoko no ko` 48,688.
  **`no bra` and `no panties` are both in the operator's own approved sheets.**
- **Passes 3 and 4 are not alternatives** — `_curated_pass` runs whenever 1 and 2 miss, and containment
  then runs on whatever words survive it.

**So the router does not call `map_phrase`. It is `field_map.primary.get(tag)`.** The tags are already
canonical — that is the property the whole version rests on — and 8,069 of 8,106 would have terminated at
pass 1 anyway. `sheet:purity:absence-clause-is-dropped` retires with the guard, and correctly: a canonical
tag stream cannot contain a clause, so the scenario would be unreachable rather than merely unneeded.

### D25 · `normalise()` does not retire, and the roadmap's conclusion from it was half-founded

**`shared/fields.py:19` imports it and `fields.py:64` calls it inside `validate()`** — reached from
`sheet.py:381` **and `review.py:287`, the approval path**, where it enforces the *"written in the
vocabulary's own spelling"* refusal. It is additionally called by `Vocabulary.__contains__`
(`vocabulary.py:160`), `count` (`:172`), **`search` (`:181` — the UI autocomplete, pinned by
`ui:vocabulary:matches-are-ranked-by-post-count`)** and `read_tags` (`:236`).

**`CURATED` retires; `normalise()` does not.** So the roadmap's *"the sentence labels are moot in their
original form, since `normalise()` and `CURATED` retire with the cascade"* rests on a half-false
conjunction: **`normalise()`'s punctuation gap survives this version untouched, in the function that
decides whether a corrected sheet may be approved.** What does survive of that finding is the part that
needs no inference — `1girl`, `solo` and `upper body` have no lexical route to any sentence at any
quality.

**And the dead set is twelve names, not the five the roadmap lists.** Adding to `map_phrase`, `CURATED`,
`CURATED_SPANS`, `_curated_pass`, `_index_of` and `contained_in`: **`Vocabulary.words` (`:188`),
`Vocabulary.by_word` (`:193`), `asserts_absence` (`:144`), `_ABSENCE` (`:64`), `_spans` (`:117`) and
`_in_order` (`:366`)**. None is touched by `search`, `count` or `__contains__`.

### D26 · `tagging`'s rationale is rewritten in place, and it is the largest spec casualty

**Not `sheet`.** `openspec/specs/tagging/spec.md:51-54` grounds the entire unnarrowed-list requirement in:

> *"The whole value of this artifact is recall rather than accuracy: it is what a model offered **before**
> the sorter narrowed it, and the sorter's narrowing is precisely what the operator is trying to see
> behind."*

**There is no sorter after this version, and the WD14 list is now the sheet's source rather than the thing
beside it.** The SHALL is still satisfiable and every scenario and binding still holds — only the
paragraph is false. **It is replaced by a stronger reason: the router is a filter, and the raw list is the
only way the operator sees what it dropped.** `openspec` permits editing a rationale without touching a
key, so nothing moves.

**Two more sentences elsewhere go false and are corrected**, neither needing a scenario change:
`cli/spec.md:234` enumerates *"the reader, the sorter and each tagger"*, and
`image-generation:hosted:flow-declares-its-hosted-models` requires *"a model name for each of the first
two stages"* and *"the loaded flow carries that implementation and both model names"*.
`ui/design/ux-flow.md:71` — *"Out-of-vocabulary tags only arrive from the sorter"* — makes the UI's
out-of-vocabulary refusal kind **unreachable**, which is a document correction and not a code change.

### D27 · The overlay owns focus while it is open, and gives it back exactly

`Option+Space` is pressed **mid-fragment, inside a tag field** — that is the whole trigger, and
`ui.md` § ② states the requirement: *"It must work while a text field has focus."* The overlay needs its
own filter input, so focus must move.

**On open:** remember the field and the fragment, blur the field, focus the filter. **While open:**
`TagInput`'s Escape and arrow branches yield, so `Esc` closes the overlay rather than clearing a fragment
and `←`/`→` do not double-fire. **On close:** restore the field and the fragment byte for byte.

**The overlay stays read-only** — clicking a tag does not insert it, settled at `ui.md` § ②. Inserting
would make a reference surface own a target field and commit into it, which is scope. *Revisit if the
round trip through short-term memory proves to be the slow part.*

### D28 · The in-field picker is deferred, and the finding is that it never shipped

**`ui.md` § ① cites `ui/src/components/TagInput.vue:92` as a shipped field-scoped picker. The code at that
exact line does the opposite — it swallows the key.** The feature lived on a prop named `hint`, and it was
**deleted in `8aa6fb0`, *"feat(ui): rework the keyboard model"*, which is an ancestor of the `v0.18.0`
tag.** It was introduced and removed inside one version. **`CHANGELOG.md:771-776`, inside the `[0.18.0]`
section, still claims it.** Structurally it cannot work either: `ui/app.py:78` sends
`list(batch.flow.schema.names)` — names only — so a suffix has never reached the browser in any version.

**Two consequences.** The *"derived group"* of 103 / 47 / 4 has **zero runtime consumers and never had
one**, so `ui.md`'s *"Space stops being suffix-only without a new binding"* is false — there is no binding
to extend, and building the picker would be building the first one. **And after `map_phrase` dies,
`Field.suffix` has no consumer at all**; its only live read is `sheet.py:93`.

**At the operator's call the picker is deferred and the autocomplete is unchanged.** `CHANGELOG.md:771-776`
is corrected, and `Field.suffix` is named dead in the proposal's Impact — **the key stays in all three
frozen schemas**, because editing them means new flow ids.

### D29 · Three items the roadmap's list of retirements omits

Walking the import graph out from `isekai/pipeline/sheet.py` found eight omissions; `Hosted.sorter` (D22)
and the cross-capability spec damage (D26) are covered above. Three more are code:

- **`BUDGETS["sheet"] = 3`** at `run.py:152`. A deterministic router has no transient failure, so the
  honest value is **1** — which is what `"wd14": 1` already records for the other local producer.
- **`sheet.py` imports nine names from `boundary/claude_cli.py`** (`:46-56`). After `ClaudeSorter` goes,
  `caption.py` is the sole `pipeline/` importer of `claude_cli`, which changes the call-graph sentence at
  `CLAUDE.md:88-90`.
- **`SORTER_REMEDY`** (`sheet.py:163`, one caller at `:280`) is not on the roadmap's list and dies with
  the rest. And **nothing** has to change for CLI flags, env vars or settings keys — none exist
  (`os.environ` appears zero times in `isekai/`), no `--sorter` flag was ever added, and
  **`DEFAULT_IMPLEMENTATION` survives** because the readers and hosted taggers still resolve through it.


### D30 · The seven seed lists were authored and verified at the cut, and three of the brief's sizings were wrong

**Added after the cut, on the question of whether `mf-build` could run this confidently.** Sub-task 2.4
originally said *"seed the seven criteria"* and named no seeds, which is ~200 words of taste inside a
builder phase and a halt under *a task ambiguous enough that two readings give different work*. So the
lists were authored and then measured. Three findings came out of measuring them:

**① Plurals are not enough — the matcher needs `-s/-es/-ing/-ed`.** D18 showed `\bbraid\b` losing
`twin braids`; with plural handling alone, **12 of the operator's 113 approved tags are unreachable** —
`pulling` from `pull`, `licking` from `lick`, `lifted by self` from `lift`. With stem morphology and the
`also`-group rule below, it is **0 of 113**. Seeds are therefore written as **stems**.

**② The seven groups are 2,829 tags and `clothes` alone is 1,411.** The brief said *"`clothes` is 900 tags
from 20 seeds"* and *"63 seeds reach 2,126 tags — 26% of the whole vocabulary"*. **Seven criteria exceed
the figure claimed for twenty-one.** Measured against the pinned 8,106: `clothes` 1,411 · `pose` 791 ·
`background` 235 · `body_shape` 196 · `expression` 132 · `framing` 40 · `gaze` 24. This makes D7's
decision to cut nothing **more** consequential and does not change it: a `>10,000` cutoff still hides 10
of the 113 tags he approved.

**③ 265 tags are matched by more than one of the seven, and no precedence order is right.** Hand-deciding
265 primaries inside a builder phase is not a build, so the rule is ordered: **the operator's own approved
sheets decide first** — 17 of the 265 — then a declared precedence order settles the remaining 248, then
phase 8 overrides individual tags. **Step 1 leads because no ordering reproduces his filing:** he puts
`bare shoulders` in `clothes` (4×) where the seeds offer `body_shape` or `clothes`, `open mouth` in
`expression` where they offer `clothes` or `expression`, `clothes lift` in `clothes` where they offer
`clothes` or `pose`, and `navel` in **all three** of `pose`, `clothes` and `body_shape`. A tag he approved
and then rendered is render-tested, which is the argument `ui.md` § ⑥ already makes for mining his
corrections — applied here to the one decision the table cannot derive.

**The losing criteria keep the tag in `also`**, which is also why eight of the twelve originally-unreachable
approved tags need no seed: `collarbone`, `thighs`, `ass` and `breasts out` reach `pose` through `also`,
and `standing` reaches `framing` the same way.

**Two further defects in the cut's own `tasks.md`, found in the same pass and fixed:** 6.4 said to correct
`CLAUDE.md`'s capability count to **twelve**, which contradicts that paragraph's own rule — the count is
the number on disk, which is **eleven**, and twelve arrives when `mf-release` archives this change. And
1.3/1.4 left it ambiguous whether the four checks are raised by the loader or only asserted by tests; the
spec scenarios say *"loading it is refused"*, so **the loader raises and the tests prove it**. `shared/`
may import `foundation/` for the coverage check — `shared/fields.py:17` already imports `Schema` from
`foundation.flow`, so it is not a new edge. And `revision` is the table's **own monotonic integer**,
declared in the file, because an authored artifact has no upstream revision to name.

---

## Risks / Trade-offs

| risk | mitigation |
|---|---|
| **The authored table is taste, and the builder writes seven fields of it** | The builder's half is mechanical and prints what each seed pulled in; the operator's pass is a named phase, and D9 makes an unfinished group legal rather than a red gate |
| **The acceptance has no baseline**, so a bad result is a judgement and not a number | D2 is deliberate — the only available baseline is circular. The one recorded ratio is what v0.22 reads |
| **`clothes` at ~800 rows may be unusable even filtered** | D7's filter is the affordance `ui.md` § ⑤ already argued for. If it fails, D15's implication graph is the named next move |
| **31 orphaned bindings, and no checker** | Listed by name in `tasks.md`. `CLAUDE.md:158` already declares the gap |
| **Two keystrokes with no mechanical check** | D10 states it in `tasks.md` and puts them in a HUMAN phase rather than behind a green gate that proves nothing |
| **`age_band`, `marks` and `eyelashes` may be inexpressible** | Recorded rather than solved: a field with four possible values no tagger can see is a field the schema may not be able to express, and this version's authoring pass is what would say so |

## Migration Plan

**None.** Every verb, flag, artifact shape, manifest key and committed flow digest is unchanged, and the
sheet artifact keeps schema version 1. Existing runs remain readable: a sheet written by a sorter records
`implementation: ollama` and a `briefing` digest, and a sheet written by the router records
`implementation: wd14`, `pinned: true`, both model digests and a `field_map` record. **Nothing rewrites an
existing artifact**, and `show` reports both.

## Open Questions

**None blocking.** Four items are deferred with triggers, and all four are recorded in the proposal:
Danbooru's `tag_implications` graph (D15) · the in-field picker (D28) · the keybinding re-work and
`Cmd+Z` (D14) · a spec↔test binding checker and a browser test runner, both v0.22.1 (D10, D23).
