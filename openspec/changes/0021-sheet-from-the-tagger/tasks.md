# Tasks — 0021 the sheet comes from the tagger

## Progress

- [x] 1 — `field-map`: the artifact, the loader, and the four checks
- [x] 2 — The authoring script: seven seeded criteria and the dead briefing's own examples
- [x] 3 — The router fills the sheet, and the sorter seam is unwired
- [x] 4 — Retirement one: the sorter bodies and their ten scenarios
- [x] 5 — Retirement two: the free-text mapping cascade
- [x] 6 — The documents this version makes false
- [x] 7 — `/api/fields`, the cheatsheet overlay, and the two keystrokes
- [ ] 8 — ⚠️ **HUMAN · FREE** — author the remaining groups and prune the excluded list
- [ ] 9 — ⚠️ **HUMAN · FREE** — the acceptance, on fresh photographs

## The per-phase ritual

1. **Run each sub-task's stated verification — run it, never summarize it. Paste real output.**
2. **Gate green before the commit** — `make gate`, the commands in `.minions/minions.toml`'s `gate` array,
   in order. **Never weaken the gate to pass**; halt and say so.
3. A `CHANGELOG.md` entry under `## [Unreleased]`, appended in that phase's own commit.
4. The phase's box ticked in `## Progress` above, in that phase's own commit.
5. **One commit per phase**, staged **by name**, carrying `Change: 0021-sheet-from-the-tagger` contiguous
   with the `Co-Authored-By:` line.
6. **Every new test carries a binding** — `@pytest.mark.spec("<key>")` naming the scenario it proves, or
   `@pytest.mark.spec_exempt("<reason>")` if it is genuinely structural.

## Who builds which phase — read this before taking the first unticked box

**Seven of the nine phases are the builder's, and they are free, offline and deterministic.** There are no
discovery phases: four audits were run at the grilling and their results are in `design.md` D1–D29. Do not
re-run them to confirm; if a body disagrees with one, that is a halt.

```
  1 - 7     BUILDER    free, offline, deterministic. All the code
  8         HUMAN      the operator's taste. Author groups, prune the excluded list. HALT
  9         HUMAN      the acceptance. Fresh photographs, his judgement. HALT
```

**Three things that are a HALT, not a judgement call**

1. **If any file:line citation in `design.md` does not match the body it names**, that is `design.md`
   contradicting the code — a finding, not a divergence to work around. Every citation was verified against
   `main` at the cut; a mismatch means the tree has moved since.
2. **`design.md` is authoritative and the builder does not amend it.** Where the build disagrees with a
   decision it settled, stop and state the disagreement.
3. **If a phase appears to need a pod, or a network call, that is a halt.** WD14 is a local ONNX pass, the
   authoring script reads one local file, and the acceptance requires no render. **No phase spends money.**

**One thing this change has that v0.20 did not: two of its deliverables have no mechanical check at all.**
`design.md` D10 — there is no browser test runner in this repository, and `scripts/typecheck_ui.sh` →
`vue-tsc --noEmit` is the gate's whole browser half. **`Option+Space`, `Option+F` and the overlay's
behaviour will be green on the gate and proven only in phase 9.** Do not read a green gate on phase 7 as
evidence the keystrokes work.

---

## 1 — `field-map`: the artifact, the loader, and the four checks

**Acceptance:** the table exists with an entry for all 21 declared criteria, the loader refuses each of the
four ways it can be wrong, and the suite proves all four against the provisioned vocabulary.

- [ ] 1.1 `scripts/field_map.json` — the authored table, **committed**, beside `scripts/vocabulary.json`.
  Shape: `{name, revision, fields: {<field>: {primary: [tag, …], also: [tag, …]}}, excluded: [tag, …]}`.
  **All 21 criteria carry an entry in this phase**, populated only from what derivation gives for free (see
  1.2); the eleven with no suffix are present and empty until phase 2. `design.md` D9.
- [ ] 1.2 Populate the ten suffix-carrying criteria mechanically, **including the hair split** — a `hair`
  tag whose non-suffix words contain a colour word takes `hair_colour` as its primary, every other takes
  `hair_silhouette`, and **both fields list all 103 under `also`** so nothing is hidden from browsing.
  `design.md` D16. The rule that reproduces the record's group sizes is *tag equals the suffix, or ends in
  `" " + suffix`* — **not** substring, which gives `hair` 265 rather than 103.
- [ ] 1.3 `isekai/shared/field_map.py` — the loader, beside `vocabulary.py` because both `pipeline/` and
  `interface/` import from `shared/`. It exposes the table, the derived `field → tags` grouping, and
  `primary_of(tag) -> str | None`. **The reverse index is computed, never stored.**

  **`revision` is the table's own integer, declared in the file and bumped by whoever edits it.** Unlike
  `scripts/vocabulary.json`'s entries there is no upstream revision to name — the table is authored here —
  so `revision` is a monotonic counter and `sha256` is the digest of the file's bytes. **Phase 1 ships
  `revision: 1`; phase 2 bumps it to 2; phase 8 bumps it again.** That is what makes
  `sheet:output:sheet-names-its-field-map` worth recording: two sheets routed by different revisions are
  distinguishable from the record alone.
- [ ] 1.4 The four checks. **All four are raised by the loader, and each is proven by a test with a `spec`
  binding** — the spec scenarios say *"loading it is refused"*, so a check that lived only in a test would
  not implement them. `shared/` may import `foundation/` for this: `shared/fields.py:17` already imports
  `Schema` from `foundation.flow`, so reading the tracked flows' schemas for the coverage check is
  layering-legal and not a new edge. **Take the field list from the flows' `Schema` objects, not from a
  constant** — a hardcoded 21 would pass while a flow's schema moved underneath it.
  - every tag resolves in the pinned vocabulary → `field-map:integrity:a-tag-outside-the-vocabulary-is-refused`
  - every tag has exactly one primary → `field-map:membership:every-tag-has-exactly-one-primary`
  - the excluded list and the union of every group are disjoint → `field-map:excluded:no-tag-is-in-both`
  - every field any tracked flow declares has an entry → `field-map:coverage:every-declared-field-has-an-entry`
- [ ] 1.5 A test asserting the committed table passes all four against the **provisioned** vocabulary, naming
  its revision → `field-map:integrity:the-check-runs-against-the-pin`. The vocabulary is gitignored and
  fetched by `scripts/download_models.sh` against the committed sha256, which is the same dependency every
  existing vocabulary test already has.
- [ ] 1.6 **Verify:**
  ```
  uv run pytest tests/test_field_map.py -v
  uv run python -c "from isekai.shared.field_map import load; m = load(); print(len(m.fields), sum(len(g.primary) for g in m.fields.values()))"
  ```
  Paste both. The field count must be **21**.

---

## 2 — The authoring script: seven seeded criteria and the dead briefing's own examples

**Acceptance:** `clothes`, `pose`, `body_shape`, `expression`, `gaze`, `framing` and `background` carry
authored groups; the script is reproducible offline; and what each seed pulled in is printed so phase 8's
pruning sees the junk rather than inheriting it.

- [ ] 2.1 `scripts/derive_field_map.py` — **stdlib only, no network.** It reads
  `models/wd14/selected_tags.csv` and a seed list per criterion, and prints the expansion. `design.md` D15:
  a Danbooru wildcard intersected with the pin **is** a substring match against the pin, so the route needs
  no Danbooru at all. **If this script appears to need an HTTP call, that is a halt.**
- [ ] 2.2 Matching is **word-boundary against the seed and its plural**, not `in`. `design.md` D18: `\bscar\b`
  correctly takes 44 matches to 15, but `\bbraid\b` alone loses `twin braids` (153,036), `side braids`,
  `low twin braids`, `multiple braids`, `tri braids` and `braided hair rings`.
- [ ] 2.3 **Reproduce the record's one verifiable number first, as a test — and expect 57, not 63.**
  The seven seeds at `notes/v0.19_improvements/ui.md:575` are `ponytail braid bun bangs twintails updo
  hime_cut`. **`hime_cut` is ONE seed, not two** — splitting it yields a bare `cut` that pulls in the whole
  `cutout` family, which is a 32-tag error and was made once already while measuring this.

  | matcher | matched | new beyond the derived 103 |
  |---|---|---|
  | substring — **the record's route** | 66 | **63** |
  | word-boundary only | 51 | 51 |
  | **word-boundary + morphology — 2.2's rule** | **59** | **57** |

  **63 is the substring number and 2.2 forbids substring, so the test asserts 57.** The difference is
  exactly **six tags, and every one is junk**: `playboy bunny` 82,752 · `reverse bunnysuit` 4,453 ·
  `nontraditional playboy bunny` 2,537 · `setsubun` 2,302 · `male playboy bunny` 1,902 · `bunny day` 1,064
  — all from `bun`, and **`\bbun\b` does not match `bunny` or `setsubun`**. Nothing else changes: the rule
  adds zero tags the record's route had and drops nothing but those six.

  **So the matcher removes the defect the roadmap flagged and could not solve, and keeps the eight tags a
  bare word boundary would have lost** — `twin braids` 153,036 · `side braids` 6,720 · `low twin braids`
  5,536 · `braided hair rings` 3,917 · `multiple braids` 1,868 · `low-braided long hair` 1,044 ·
  `braiding hair` 807 · `tri braids` 805. **Assert all three numbers — 59, 57 and the six-tag
  difference — so a later change to the matcher cannot move them silently.**

- [ ] 2.4 Seed the seven criteria the measurement says carry the weight. **`clothes`, `pose` and
  `body_shape` hold 102 of the 200 approved tags between them and none declares a suffix.** **Use the
  lists below verbatim** — they were authored at the cut and **verified: every one of the operator's 113
  approved tags is reachable**, 0 unreachable. Do not invent a different set; 2.7's report is what phase 8
  prunes, and a builder-invented list makes that pass unreviewable against the cut.

  **The matcher needs `-s/-es/-ing/-ed`, not only plurals.** `design.md` D18 already showed `\bbraid\b`
  losing `twin braids`; measured again here, plurals alone leave **12 of 113 approved tags unreachable** —
  `pulling` from `pull`, `licking` from `lick`, `lifted by self` from `lift`. Handle the drop-`e` and
  final-consonant-doubling cases (`expose` → `exposing`, `stop` → `stopping`). **Seeds are therefore
  written as stems** — `stand`, `expose`, `look` — not as inflected words.

  **`clothes`** — `shirt blouse dress skirt shorts pants trousers jeans sweater cardigan jacket coat
  hoodie vest robe kimono uniform swimsuit bikini leotard bodysuit lingerie bra panties underwear thong
  pantyhose thighhighs stockings socks garter footwear shoes boots heels sandals gloves sleeves collar
  belt apron cape corset camisole top tank crop fishnet lace strap hem` · and the exposure and
  state-of-dress half, which a garment-only list misses entirely: `bare cleavage midriff navel expose
  lift pull open unbutton unzip see-through sheer torn wet shoulder` *(singular `shoulder`, so
  `off shoulder` is reached as well as `bare shoulders`)*

  **`pose`** — `stand sit kneel lie lying squat crouch lean walk run jump stretch arm hand leg knee foot
  toes finger head tilt bend cross spread raise hold hug touch cover support bed side back front lift
  pull` · plus the explicit tags no safe seed reaches: `from behind`, `from side`, `from above`,
  `from below`

  **`body_shape`** — `breasts hips waist thighs stomach abs shoulder collarbone navel nipples ass butt
  muscular slim curvy plump petite build body`

  **`expression`** — `smile grin smirk frown pout blush laugh cry tears sad angry surprised embarrass
  serious expressionless mouth lips tongue teeth lick wink sweat sigh yawn closed`

  **`gaze`** — `look gaze glance stare` · plus `eye contact`

  **`framing`** — `shot portrait close-up crop focus selfie view angle foreshortening` · plus
  `out of frame`, `upper body`, `full body`, `lower body`

  **`background`** — `background indoors outdoors sky cloud sun moon night day forest beach ocean city
  cityscape street room bedroom bathroom kitchen office wall window door floor ceiling bed pillow curtain
  chair table tree grass water rain snow station building interior exterior`

  **The script takes two inputs per criterion, not one:** a stem list it expands, and an optional list of
  explicit tags added verbatim. A tag reachable only by a stem that would pull in hundreds — `from`, `no`,
  `body` — belongs in the second list.

- [ ] 2.4a **The seven groups are 2,829 tags and `clothes` alone is 1,411 — both larger than the brief
  said.** Measured at the cut against the pinned 8,106: `clothes` **1,411** · `pose` **791** ·
  `background` **235** · `body_shape` **196** · `expression` **132** · `framing` **40** · `gaze` **24**.
  The brief's *"`clothes` is 900 tags from 20 seeds"* and *"63 seeds reach 2,126 tags"* both **understate
  it** — seven criteria alone exceed the figure claimed for twenty-one. **This makes `design.md` D7's
  no-cut decision more consequential, not less**, and it is the right call anyway: a `>10,000` cutoff
  hides 10 of the 113 tags the operator approved. Record the real sizes in the phase's `CHANGELOG` entry.

- [ ] 2.4b **265 tags are matched by more than one of the seven, and no single precedence order is right.**
  Each needs one primary (`design.md` D4), and hand-deciding 265 inside a builder phase is not a build.
  **The rule, in this order:**
  1. **If the operator has filed the tag in an approved sheet, his filing decides its primary** — the
     field he used most often, ties broken by step 2. That covers **17** of the 265, and it is the
     strongest signal available: a tag he approved and then rendered is render-tested, which no ordering
     is. Read `.data/v0.20/runs/*/summon-open-v1/review/*.approved.json`; the script is operator tooling
     and its output is committed, so reading a gitignored directory is fine.
  2. **Otherwise this precedence order decides** — written once in `derive_field_map.py`, printed in the
     report, and **not chosen by the builder**:

     ```
     gaze > clothes > pose > body_shape > expression > framing > background
     ```

     It settles the remaining **248** mechanically. **It is a tie-break and not a claim to be right**:
     measured against the 17 collisions he has actually filed, **11 is the ceiling for any of the 5,040
     possible orders, and 210 of them reach it** — so this one was picked from the winners rather than
     reasoned to. Rule 1 overrides all 17 regardless, which is the point; the order only ever decides the
     248 he has never filed, where there is nothing to be right or wrong against. **The report must print
     the 248 grouped by which criteria collided**, so phase 8 scans clusters rather than a flat list.
  3. **Phase 8 overrides individual tags.** The override list lives in the table, not in the script.

  **Do not try to find an order that matches the ground truth — there isn't one.** Measured: he files
  `bare shoulders` under `clothes` (4×) while the seeds say `body_shape` or `clothes`; `open mouth` under
  `expression` while the seeds say `clothes` or `expression`; `clothes lift` under `clothes` while the
  seeds say `clothes` or `pose`; and `navel` under all three of `pose`, `clothes` and `body_shape`. **That
  is why step 1 exists and why it comes first.**

  **Every tag that loses a collision goes into the winning criterion's `primary` and the losing ones'
  `also`** — so `navel` still appears under `clothes`, `pose` and `body_shape` in the cheatsheet, and
  routes to exactly one. This is also why eight of the twelve originally-unreachable approved tags needed
  no seed of their own: `collarbone`, `thighs`, `ass` and `breasts out` reach `pose` through `also`, and
  `standing` reaches `framing` the same way.

- [ ] 2.5 **Harvest `flows/*/sheet.briefing.md`.** It names roughly **40 example tags across 10 of the 21
  criteria** — `bangs` 6, `framing` 8, `gaze` 4, `lips` 4, `facial_hair` 4, `count` 4, `nose` 3,
  `eyebrows` 3, `skin_ancestry` 3, `eyelashes` 2 — and it is the **only authored group content that exists
  anywhere in either tree.** It is also the file this version carries dead (`design.md` D22), so harvest it
  now.
- [ ] 2.6 Re-run 1.4's four checks over the grown table. **Collisions are expected and are the point** — two
  seed sets already collide on `reverse bunnysuit`, `braided hair rings` and `ribbon braid`. Each is one
  primary decision; make it, and record any that is not obvious in the commit message.
- [ ] 2.7 **Verify:**
  ```
  uv run python scripts/derive_field_map.py --report
  uv run pytest tests/test_field_map.py -v
  ```
  Paste both, including the per-seed expansion report. **One of the tests must assert the reachability
  claim in 2.4** — every tag in every approved sheet on disk resolves into the group of the field it was
  approved in, whether as a `primary` or an `also`. It was 0 unreachable at the cut; if it is not 0 after
  the build, the seed lists moved and that is a halt.

---

## 3 — The router fills the sheet, and the sorter seam is unwired

**Acceptance:** `isekai sheet` fills a sheet from `wd14/` with no language model reached, refuses when that
artifact is absent, and records the table it routed by. The sorter seam no longer exists in `wiring` or the
CLI, and the suite is green without a `FakeSorter` being passed anywhere.

- [ ] 3.1 The router in `isekai/pipeline/sheet.py`: for each tag, `field_map.primary_of(tag)`; drop it if the
  result is `None` **or if the acting flow's schema does not declare that field**; preserve the tagger's
  order inside each field. **It is a dictionary lookup and it does not call `map_phrase`** — `design.md` D24:
  `map_phrase`'s first act is an absence guard that drops **37 of 8,106 canonical tags before any pass
  runs**, including `no bra` and `no panties`, **both of which are in the operator's own approved sheets**.
- [ ] 3.2 `sheet.py:355` — `run.directory(flow, CAPTIONS)` becomes `WD14`. **One line, plus the refusal text
  at `:358-361`**, which must name `caption` as the verb that produces it. `design.md` D21.
- [ ] 3.3 `sheet()`'s signature: `sorter` and `briefing_path` both go. That removes the only consumer of
  `flow.sheet_briefing_path` (`flow.py:282`) and the only reason `sheet()` calls `instructions_record()`
  (`:392`), so **the sheet's producer loses its `briefing` key** and gains `implementation: wd14`,
  `pinned: true`, both WD14 digests, and `field_map: {name, revision, sha256}` beside `vocabulary`.
- [ ] 3.4 `isekai/foundation/run.py:152` — `BUDGETS["sheet"]` **3 → 1**. `design.md` D29: a deterministic
  router has no transient failure, which is what `"wd14": 1` already records for the other local producer.
- [ ] 3.5 Unwire the seam, because the gate forces it with 3.3: `wiring.py` loses `Wiring.sorter` (`:64`),
  `_claude_sorter` (`:99`), `_ollama_sorter` (`:121`), `SORTERS` (`:160`), `sorter_for` (`:202`), the
  `sorter=sorter_for` binding (`:331`) and its `sheet` import (`:32`); `cli.py:443` loses
  `_seam(wired.sorter, "sorter", "fills the sheet")`. **`DEFAULT_IMPLEMENTATION` (`:91`) and `_named_by`
  (`:104`) survive** — the readers and hosted taggers still resolve through them.
- [ ] 3.6 **The 46 reference lines.** `tests/stages.py:57`'s `sheet()` wrapper binds `flow` and
  `briefing_path` for ~70 call sites, and `tests/stages.py:48` types the wrapper against `sheet_stage.Sorter`.
  Ten test files pass a `FakeSorter`: `test_generate.py` (7), `test_pipeline_cli.py` (2),
  `test_resume.py` (4), `test_review.py` (3), `test_run_directory.py` (2), `test_run_view.py` (2),
  `test_sheet_stage.py` (20), `test_tagging.py` (2), `test_ui.py` (2), `test_ui_api.py` (2). **All of them
  now need a `wd14/` artifact on disk instead** — give `tests/stages.py` one helper that writes one, and
  change 46 lines rather than inventing 46 fixtures.
- [ ] 3.7 Tests for the six new and moved `sheet` scenarios, and the four `field-map:routing:*` ones. In
  particular: `sheet:output:the-stage-reads-the-tag-list` needs a run with **both** a caption and a wd14
  artifact, and must assert the caption file is not opened.
- [ ] 3.8 **Prove `caption()` and `boundary/wd14.py` did not move.**
  ```
  git diff main -- isekai/pipeline/caption.py isekai/boundary/wd14.py
  ```
  Must be **empty**. Paste it.
- [ ] 3.9 **Prove no flow was re-pinned.**
  ```
  git diff main -- flows/
  uv run pytest tests/test_flow.py -v
  ```
  The diff must be empty and `PINNED` must pass. Paste both.
- [ ] 3.10 **Verify:**
  ```
  uv run pytest tests/test_sheet_stage.py tests/test_field_map.py tests/test_resume.py -v
  uv run python -m isekai show --flow summon-open-v1
  ```

---

## 4 — Retirement one: the sorter bodies and their ten scenarios

**Acceptance:** nothing named `Sorter` exists in the tree, `sheet.py` imports nothing from `claude_cli`, and
the five `sheet:selection:*` and three `sheet:seam:*`/`sheet:failure:*` scenarios' tests are gone with their
bindings.

- [ ] 4.1 Delete from `isekai/pipeline/sheet.py`: `Sorting` (`:108`), `Sorter` (`:117`), `FakeSorter`
  (`:125`), `ClaudeSorter` (`:201`), `OllamaSorter` (`:232`), `output_shape` (`:166`), `sorter_prompt`
  (`:188`), `answers_from` (`:292`), `SORTER_OPTIONS` (`:153`), `SORTER_REMEDY` (`:163`) — and **the nine
  names imported from `boundary/claude_cli.py` at `:46-56`**, which leaves `caption.py` the sole `pipeline/`
  importer of that module. `design.md` D29.
- [ ] 4.2 Delete the tests bound to the eight scenarios this phase retires, and **their bindings with them**.
  `CLAUDE.md:158` states there is no spec↔test binding checker, so **a marker naming a deleted scenario
  passes the gate green.** Grep for each key by name:
  ```
  sheet:selection:the-flow-names-the-implementation
  sheet:selection:unknown-implementation-is-refused
  sheet:selection:structure-is-required-of-every-implementation
  sheet:selection:answer-in-the-body-is-read
  sheet:selection:truncation-is-permanent-and-named
  sheet:seam:offline-double-satisfies-the-interface
  sheet:seam:structure-constrained-content-free
  sheet:failure:structural-mismatch-is-permanent
  ```
- [ ] 4.3 **Two `caption:` scenarios have tests that assert the sorter, and the scenarios themselves are
  unchanged** — the tests are what move. `test_pipeline_cli.py:424` asserts `set(SORTERS) == set(READERS)`
  (also `:426`, `:428`, `:438`, `:450`), bound to
  `caption:selection:the-flow-names-the-implementation`; and `test_isolation.py:94` and `:109`, bound to
  `caption:selection:no-path-reaches-another-implementation`, drive stages ① **and** ② through `_stage()`.
  **Narrow them to the reader. Do not delete `test_isolation.py`** — it is v0.19's falsification proof and
  v0.22 retires it deliberately, not this version by accident.
- [ ] 4.4 **`hosted.sorter` stays in every manifest, unread.** `design.md` D22 — it is a *required* key
  (`flow.py:234`, read unguarded at `:429`) and three tests assert it (`test_flow.py:565, 577, 704`).
  Removing `"sorter": "qwen3:8b"` from `flows/summon-open-v1/flow.json` moves that flow's digest, which
  `CLAUDE.md:196` makes a new flow. **Leave the dataclass field and the reader in place.**
- [ ] 4.5 **Verify:**
  ```
  git grep -n "Sorter\|SORTER\|sorter_for\|output_shape\|answers_from" -- isekai/ tests/ | grep -v "hosted\|Hosted"
  uv run pytest -q
  ```
  The grep must return nothing outside the manifest's `hosted.sorter` plumbing. Paste both.

---

## 5 — Retirement two: the free-text mapping cascade

**Acceptance:** twelve names leave `isekai/shared/vocabulary.py`, `normalise()` stays, and the sheet's
spelling refusal on the approval path is unchanged.

- [ ] 5.1 Delete from `isekai/shared/vocabulary.py`: `map_phrase` (`:289`), `CURATED` (`:83`, exactly 30
  entries), `CURATED_SPANS` (`:141`), `_curated_pass` (`:334`), `_index_of` (`:356`), `contained_in`
  (`:207`), `Vocabulary.words` (`:188`), `Vocabulary.by_word` (`:193`), `asserts_absence` (`:144`),
  `_ABSENCE` (`:64`), `_spans` (`:117`), `_in_order` (`:366`). **Twelve, not the five the roadmap listed** —
  `design.md` D25.
- [ ] 5.2 **`normalise()` (`:135`) is NOT deleted, and this is a halt if it looks otherwise.** It is called by
  `Vocabulary.__contains__` (`:160`), `count` (`:172`), `search` (`:181` — the UI autocomplete, pinned by
  `ui:vocabulary:matches-are-ranked-by-post-count`) and `read_tags` (`:236`), **and by
  `isekai/shared/fields.py:64` inside `validate()`, reached from `review.py:287` on the approval path.**
- [ ] 5.3 `sheet.py:73` loses its `map_phrase` import and `sheet.py:93` its call inside `fill()`. `fill()`'s
  other callers are `test_sheet_schema.py:180, 191, 202, 211` — those four tests go.
- [ ] 5.4 Delete the cascade's tests in `tests/test_vocabulary.py`: **16 test functions / 21 collected items**,
  everything under the `# --- the cascade ---` banner at `:81` through `:227`, plus the two `CURATED`-table
  tests at `:216` and `:227`. **Six functions survive** — `:38` `read_tags` categories, `:47`
  underscores-and-`normalise`, `:53` `count`, `:61` `search`, `:71` identity, `:239` the provisioned pin.
  Delete the bindings for these six keys with them:
  ```
  sheet:mapping:exact-match-wins-first
  sheet:mapping:suffix-completes-a-bare-value
  sheet:mapping:curated-pass-consumes-and-continues
  sheet:mapping:containment-requires-every-word
  sheet:mapping:no-match-emits-nothing
  sheet:purity:absence-clause-is-dropped
  ```
- [ ] 5.5 **The five briefing tests at `tests/test_sheet_stage.py:363-430`.** Delete four: `:381` (calls
  `map_phrase`), `:406`, `:419`, `:427` (assert sentences in instructions nothing follows). **Keep `:364`** —
  *every field name the briefing mentions exists in the schema* is still a real consistency check.
  `design.md` D22.
- [ ] 5.6 **`Field.suffix` now has no consumer at all.** Its only live read was `sheet.py:93`; the only other
  reference is `test_sheet_stage.py:395`. **The key stays in all three frozen `schema.json` files** — editing
  them means new flow ids. `design.md` D28. Name it dead in the commit message.
- [ ] 5.7 **Verify:**
  ```
  git grep -n "map_phrase\|CURATED\|contained_in\|asserts_absence\|by_word" -- isekai/ tests/ ui/ scripts/
  git grep -n "normalise" -- isekai/
  uv run pytest tests/test_vocabulary.py tests/test_sheet_schema.py tests/test_review.py -v
  ```
  The first grep must return nothing. The second must show `fields.py`, `vocabulary.py` and nothing deleted.

---

## 6 — The documents this version makes false

**Acceptance:** every sentence the audits found false is corrected, and the `event.code` rule exists.

- [ ] 6.1 **`CLAUDE.md` — the `event.code` rule, with the corrected reason.** `design.md` D14: `event.code`
  appears **nowhere** in this repository, so this is the **first** such binding and not the second, and the
  reason is **not** a layout switch — macOS `Option+Space` emits U+00A0 and `Option+F` emits `ƒ` on plain
  ABC. State it as: *an Option-modified binding matches `event.code` and calls `preventDefault`, because
  Option is a character-producing modifier on macOS.*
- [ ] 6.2 **`CLAUDE.md:270`** — narrow *"a missing tag artifact is an absent aid, never a refusal"* to the
  **hosted** tagger. The local tagger is a prerequisite of the sheet. `design.md` D21.
- [ ] 6.3 **`CLAUDE.md:263`** — *"prose first because it is the only one anything downstream reads"* is false;
  WD14 is. **The ordering itself does not change** — prose → WD14 → JoyCaption stands, and the failure
  isolation it buys is unchanged.
- [ ] 6.4 **`CLAUDE.md:134`** — *"ten capabilities today"* is stale: `ls -d openspec/specs/*/` returns
  **eleven**, because `0020` is archived and `tagging` is in the living spec. **Correct it to eleven, not
  twelve.** That same paragraph states the rule that makes twelve wrong here — *"a capability enters and
  leaves the living spec only when a change is archived, which is `mf-release`'s act and never the
  builder's, so the number here is always the count on disk and never the count a pending change
  implies."* So: list the eleven, and replace the trailing v0.20 clause with its v0.21 equivalent — **this
  change's delta adds `field-map` and makes it twelve, and until this change is archived it is eleven.**
  Keep the instruction to count `openspec/specs/*/` rather than trust the sentence.
- [ ] 6.5 **`CLAUDE.md:88-90`** — the call-graph sentence, now that `caption.py` is the sole `pipeline/`
  importer of `boundary/claude_cli.py`.
- [ ] 6.6 **`CHANGELOG.md:771-776`, inside `[0.18.0]`** — it claims a suffix-anchored `Space` picker that
  **never shipped**: the feature lived on a prop named `hint` and was deleted in `8aa6fb0`, *"feat(ui):
  rework the keyboard model"*, an **ancestor of the `v0.18.0` tag**. Structurally it could not have worked
  either — `ui/app.py:78` sends `list(batch.flow.schema.names)`, names only, so a suffix has never reached
  the browser. **Correct the entry; do not delete the section.** `design.md` D28.
- [ ] 6.7 **`ui/design/ux-flow.md:71`** — *"Out-of-vocabulary tags only arrive from the sorter, which is why
  they are a refusal kind rather than an input error."* The router emits only canonical tags, so that
  refusal kind is now **unreachable**. Also `ui/design/README.md:14, 140, 147` and
  `ui/design/states.md:56, 60, 132, 185`, all written around *"the sorter is mediocre"*.
- [ ] 6.8 The group `README.md` files that name the sorters: `isekai/interface/README.md:17`,
  `isekai/pipeline/README.md:23, 33`, `isekai/shared/README.md:22`, and `isekai/boundary/ollama.py:35`'s
  docstring. Add `isekai/shared/README.md`'s entry for `field_map.py`.
- [ ] 6.9 **Verify:**
  ```
  git grep -in "sorter" -- CLAUDE.md CHANGELOG.md README.md ui/design/ isekai/*/README.md | grep -v "\[0\.1[0-9]\.\|hosted"
  uv run pytest -q
  ```

---

## 7 — `/api/fields`, the cheatsheet overlay, and the two keystrokes

**Acceptance:** `Option+Space` opens a filterable reference grouped by the flow's own criteria from a tag
field and gives the fragment back on close; `Option+F` opens the photograph; the gate is green and **neither
keystroke is proven by it**.

- [ ] 7.1 `isekai/interface/ui/app.py` — `GET /api/fields`, returning `{fields: {<field>: [{tag, posts}]}}`
  for the acting flow, ordered by descending post count, with an empty group for a declared field the table
  holds nothing for, and **the excluded list absent**. `design.md` D13.
- [ ] 7.2 Tests for the four `ui:cheatsheet:*` scenarios in `tests/test_ui_api.py`. **These are the only
  mechanical checks this phase has.**
- [ ] 7.3 `ui/src/components/CheatsheetOverlay.vue` — composing **`PhotoOverlay`'s `.overlay` ground**
  (`app.css:586-668`), the same `Teleport to="body"`, `.overlay__controls` / `.overlay__exit` /
  `.overlay__foot`, `.kicker` + `.source__head` for section heads, **`.row__tags` + `TagChip.vue`** for the
  grid, `.input` for the filter, `.drop__posts` for counts, `.mono` for keystrokes. **Not
  `.dialog`** — it is unused by any component and capped at `width: min(440px, 100%)`, which is wrong for an
  800-row group. `design.md` D12. **No new component, colour, space or type step.**
- [ ] 7.4 The overlay is **read-only** — clicking a tag does not insert it (`ui.md` § ②) — shows **every** tag
  in a group with the post-count tier visible and **nothing dropped** (`design.md` D7: a `>10,000` cutoff
  would hide 10 of the 113 tags the operator approved), and its filter is what makes length the point rather
  than the problem.
- [ ] 7.5 `ui/src/ReviewApp.vue` — two branches in `onKey`, **both on `event.code` and both
  `preventDefault`**: `altKey && code === 'Space'` and `altKey && code === 'KeyF'`. `preventDefault` is
  load-bearing twice over — U+00A0 into a tag field is the silent dead end this feature removes, and Space is
  the **native activation key** of a focused `<button>` (`BatchRail.vue:41`, `PhotoFrame.vue:25`, and
  `ReviewApp.vue:292` focuses `.rail__card--current` on mount). `design.md` D14.
- [ ] 7.6 **The focus round-trip, which both keystrokes need.** `design.md` D27: on open, remember the field
  and the fragment, blur the field, focus the overlay's filter; while an overlay is open, `TagInput`'s Escape
  (`:78`, which `stopPropagation`s at `:88`) and arrow (`:101-105`) branches **yield**; on close, restore the
  field and the fragment exactly. Without it, `PhotoOverlay.vue:89-90`'s printed *"Editing is suspended … the
  sheet is behind this, untouched"* is **false**, Escape is eaten, and `←`/`→` double-fire.
- [ ] 7.7 Three corrections in the same files: delete `PhotoOverlay.vue:23`'s **`step` emit, which is never
  emitted**, and `ReviewApp.vue:424`'s binding of it; and `SourcePanel.vue:69`'s `'click to fill window'`,
  which asserts click is the only route. `design.md` D11.
- [ ] 7.8 **Do not fix `Cmd+Z`.** `ReviewApp.vue:243` matches `event.key.toLowerCase() === 'z'` and so does
  nothing under a Cyrillic layout — a live violation of 6.1's new rule. **At the operator's call it is out of
  scope**: the focus is macOS English, and he has asked for a **keybinding re-work as its own version**,
  which is where `useKeyboard()` — specified at `ui/design/components.md:76` and never built — belongs.
  Record it in the backlog with 6.1's rule as its trigger.
- [ ] 7.9 **Verify:**
  ```
  uv run pytest tests/test_ui_api.py tests/test_ui.py -v
  bash scripts/typecheck_ui.sh
  ```
  Paste both, **and state in the report that the two keystrokes are unverified by any check in this
  repository.**

---

## 8 — ⚠️ **HUMAN · FREE** — author the remaining groups and prune the excluded list

**HALT and hand back.** This is taste, and it is one handback rather than two.

- [ ] 8.1 Prune the seven seeded groups. Phase 2's report prints what each seed pulled in; the flagship number
  proves the need — **six of the celebrated 63 `hair_silhouette` tags are bunny costumes and a festival.**
- [ ] 8.2 Seed the remaining criteria, or leave them empty. **Empty is legal** (`design.md` D9), and it is the
  honest answer for a criterion the vocabulary cannot express: over eight photographs `age_band` was approved
  **0** times and `marks` **0** times, `age_band` has no candidates in the vocabulary at all, and `eyelashes`
  holds four tags in total — `eyelashes` 128,622 · `colored eyelashes` 23,255 · `long eyelashes` 4,797 ·
  `thick eyelashes` 1,268.
- [ ] 8.3 Prune the excluded list. The candidate set is the **43** tags WD14 offered across the eight-photograph
  batch that never reached an approved field — but **`design.md` D8: it conflates two kinds.**
  `realistic ×8`, `photorealistic ×8`, `artist name`, `photo background`, `foreshortening` and `holding` are
  *never a criterion*; **`bra ×3`, `dress ×2`, `high heels ×2`, `thighhighs`, `sweater`, `shorts`,
  `leotard`, `pantyhose`, `fishnets`, `lace`, `lace trim` are ordinary garments WD14 was wrong about on those
  photographs.** Excluding the second group would silently shrink `clothes`. The list's definition is
  semantic: **no criterion can hold this.**
- [ ] 8.4 Re-run the four checks, and **resolve every collision the disjointness and one-primary checks
  report.** Each is one decision.
- [ ] 8.5 **Verify:** `uv run pytest tests/test_field_map.py -v` and `make gate`.

---

## 9 — ⚠️ **HUMAN · FREE** — the acceptance, on fresh photographs

**HALT and hand back.** Fresh photographs the operator has not seen in this project.
`caption` → `sheet` → `ui` → approve. **No render is required and no pod is used.**

**Three sub-claims, recorded separately because they fail independently. A no is a finding.**

- [ ] 9.1 **the router** — *"the draft arrived with the tags in the right fields, and correcting it was less
  work than correcting what came before."* **There is no Qwen baseline** — `design.md` D2: the only one
  available is circular, because `ui/app.py:136` put WD14's list on the review page *before* the v0.20 sheets
  were approved. This is a judgement, stated directly.
- [ ] 9.2 **the cheatsheet** — *"I reached a tag I could not previously name."* This is also the completeness
  test for phase 8: a criterion whose group is empty is a criterion this claim will fail on.
- [ ] 9.3 **coverage, measured and recorded with no pass mark** — of the WD14 tags above the floor, **N%
  routed to a field; of those, M% survived review.** Record the raw counts per photograph. **These numbers
  are what v0.22 reads, and no gate depends on them** (`design.md` D2).
- [ ] 9.4 For the record beside them, the n=8 figures this change was cut against: approved **200** tags over
  eight photographs (**25.0/photo**); WD14 offers **35.2/photo** at 0.15; Qwen supplied **33.5%** of the
  approved sheet at **56.3%** precision and **6.5 deletions/photo**; and of the **133** tags the operator
  typed by hand after Qwen, WD14 already held **128**.
- [ ] 9.5 Write the result into `design.md` as a new decision, and say which of the three sub-claims failed if
  any did.
