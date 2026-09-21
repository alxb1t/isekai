---
version: v0.21
---

## Why

**The sheet is filled by a model that can invent a tag, and the operator cannot see what Danbooru calls
the thing he is looking at.** Both are answered by the same authored artifact, read in two directions.

**Four audits were run against `main` before this change was cut, and they overturned fifteen premises
the roadmap section had settled.** The three that decide the version:

**① Qwen is much worse than the record says, and WD14 much better — re-measured at n=8.** Every number in
`roadmap.md § v0.21` came from three photographs in `.data/v0.19/runs/`. v0.20's acceptance batch is
eight, and every run carries `captions/`, `wd14/`, `tags/`, `sheets/` and `review/*.approved.json` on
disk, so the re-measurement was a pure disk read:

| | n=3 (the brief) | n=8 (measured) |
|---|---|---|
| Qwen supplies, of the approved sheet | 37 · **55%** | 67/200 · **33.5%** |
| Qwen precision | 37/43 · **86%** | 67/119 · **56.3%** |
| Qwen deletions | 6 over three · **2.0/photo** | 52 over eight · **6.5/photo** |
| suffix routing of the approved sheet | 8/67 · **11%** | 9/200 · **4.5%** |
| of what the operator typed by hand, WD14 already had | 13/30 · **43%** | 128/133 · **96%** |

**102 of the 200 approved tags live in `clothes`, `pose` and `body_shape`. Qwen gets 13 of them, and not
one of the three declares a suffix.** That is the version, stated as a measurement.

**② The comparison the acceptance was going to make is circular, and is therefore dropped.**
`ui/app.py:136` puts WD14's list on the review page, and it shipped *before* the v0.20 sheets were
approved — so "WD14 supplied 86.5% of the approved tags" partly means "the operator approved what he was
shown". The three WD14 columns are unusable as evidence. **The acceptance measures the router's own
draft on fresh photographs and compares it to nothing.**

**③ Raising the sheet's floor buys no precision, and lowering it is not available.** `boundary/wd14.py:98`
applies `FLOOR = 0.15` *before* the artifact is written — the minimum confidence anywhere on disk is
0.1502 — so the roadmap's "19 at 0.02" cannot be measured without re-running the tagger this version
undertakes not to touch. And the floor sweep that *can* be measured says the lever does nothing:
precision is flat **59–63%** from 0.15 through 0.70 while recall falls one-for-one. **0.15 stands, and
the reason in the record changes.**

**And the free-text cascade cannot be reused by the router, which the roadmap assumed it could.**
`map_phrase`'s first act is not a pass — it is an absence guard (`vocabulary.py:309`) that **drops 37 of
the 8,106 canonical tags before pass 1 runs**, including `no bra` 94k and `no panties` 87k, **both of
which appear in the operator's own approved sheets**. A router built on `map_phrase` would silently
discard tags from the ground truth it is measured against. The router is a dict lookup.

## What Changes

- **A twelfth capability, `field-map`** — one authored `tag ↔ field` table beside `scripts/vocabulary.json`,
  four gate checks, and the `tag → field` read. **One data structure, two indexes**: the cheatsheet is
  the table read `field → tags`, the router is the same table read `tag → field`, and the reverse index
  is derived rather than authored.
- **A tag has one `primary` field and may appear in several groups.** The roadmap's gate check *no tag
  appears in two field groups* is **falsified by the operator's own sheets** — `navel` is filed under
  `clothes`, `pose` **and** `body_shape`; `collarbone` under `pose` and `body_shape`; `standing` under
  `pose` and `framing`; and `lips` sits in `expression` on `summon` while `lips` is a declared field on
  `conjure`. Single assignment cannot serve both consumers. The check becomes **every tag has exactly one
  primary**, which is decidable the moment the table exists and is what the router needs.
- **`sheet()` reads `wd14/` and not `captions/`** — one line at `sheet.py:355`. Stage ① becomes a reading
  aid with no machine consumer. **An absent `wd14/` is a refusal**, which narrows `CLAUDE.md`'s
  *absent aid, never a refusal* rule to the hosted tagger.
- **The sheet stays a bare `{field: [tag]}`, ordered by the tagger's confidence descending.** Schema
  version unchanged; the review surface, the prompt assembly and `review.py` are untouched. **The
  ordering is the deletion aid** — no implication collapse, so `underwear · panties · black panties` all
  land in `clothes` and the general forms sort above the specific ones.
- **Both sorters retire, and the free-text cascade with them** — in **two** phases, because they share
  only one file and orphan different tests. `OllamaSorter`, `ClaudeSorter`, `Sorter`, `Sorting`,
  `FakeSorter`, `output_shape`, `answers_from`, `sorter_prompt`, `SORTER_OPTIONS`, `SORTER_REMEDY`; then
  **twelve** names in `vocabulary.py`, not the five the roadmap listed. **`normalise()` is not among
  them** — `shared/fields.py:64` calls it inside `validate()`, reached from the **approval** path at
  `review.py:287`.
- **Two artifacts are carried dead, not one.** `sheet.briefing.md` **and `Hosted.sorter`** — a *required*
  manifest key (`flow.py:234`, read unguarded at `:429`) whose removal moves `summon-open-v1`'s digest and
  makes it a new flow. Both stay, unread. `load_flow` still refuses a flow missing the briefing
  (`flow.py:407`), so "read by nothing" was never true.
- **`/api/fields` and the cheatsheet overlay** — `Option+Space`, read-only, grouped by the flow's own
  fields, filterable, composing `PhotoOverlay`'s `.overlay` ground and `TagChip`. **`Option+F` opens the
  photograph.** Both match `event.code` and both `preventDefault`.
- **The `event.code` rule enters `CLAUDE.md` with a corrected reason.** `event.code` appears **nowhere** in
  the tree today, so this is the first such binding and not the second — and the reason is not a layout
  switch: **macOS `Option+Space` emits U+00A0 and `Option+F` emits `ƒ` on plain ABC**. Option is a
  character-producing modifier. *`Cmd+Z` is already broken under a Cyrillic layout (`ReviewApp.vue:243`)
  and goes to the backlog with this rule as its trigger, at the operator's call.*
- **BREAKING — none on disk.** Every verb, flag, artifact shape, manifest and committed flow digest is
  unchanged. All three flow directories stay byte-identical and no flow is re-pinned.
- **Deliberately not in this version**, each with its trigger: **the in-field picker** — deferred at the
  operator's call, and note the finding that it **never shipped** (deleted in `8aa6fb0`, an ancestor of
  `v0.18.0`, while `CHANGELOG.md:771-776` still claims it) · **Danbooru's `tag_implications` graph**, which
  would sub-group `clothes` mechanically, deferred because the overlay's filter makes the hierarchy a
  nicety · **a keybinding re-work as its own version**, at the operator's call · **a spec↔test binding
  checker** (v0.22.1) · **a browser test runner** (v0.22.1) · ⑤ the per-sentence candidate list, now
  unblocked · ⑥ correction mining · ⑦ field-aware ranking, and *ranking is global* travels with it.

## Capabilities

### New Capabilities

- **`field-map`** — the twelfth. One authored table assigning each vocabulary tag a primary identity
  criterion and any further criteria it may be browsed under, plus the tags no criterion can hold. **It is
  not `sheet`**: `sheet`'s eight surviving scenarios are all about the artifact's shape and its schema,
  and the table is a property of the **vocabulary** rather than of any flow — `twintails` is
  `hair_silhouette` in every flow that declares that field. **It is not `tagging`**: `CLAUDE.md:92-93`
  forbids one stage importing another.

### Modified Capabilities

- `sheet`: **22 scenarios today, not 21.** Fourteen are REMOVED — five `sheet:mapping:*` with the cascade,
  five `sheet:selection:*` with the sorters, the three-scenario seam-and-structure requirement, and
  `sheet:purity:absence-clause-is-dropped`, which is implemented wholly by the guard that eats `no bra`.
  **Eight survive**; the stage's input requirement is restated for a tag list, and gains a refusal on an
  absent tag artifact and a `field_map` provenance record. **The 14 lost keys carry 31 test bindings, and
  `CLAUDE.md:158` states there is no binding checker** — so the 31 are listed in `tasks.md` by name.
- `tagging`: **the largest casualty, and it is not in `sheet`.** `spec.md:51-54` grounds the whole
  unnarrowed-list requirement in *"what a model offered before the sorter narrowed it … the sorter's
  narrowing is precisely what the operator is trying to see behind."* There is no sorter. The SHALL and
  every scenario stand; **the rationale is rewritten** to the stronger reason — the router is a filter,
  and the raw list is how the operator sees what it dropped.
- `cli`: the per-flow-seam requirement enumerates *"the reader, the sorter and each tagger"* and goes
  false. `cli:resolution:a-seam-without-a-manifest-key-resolves-for-every-flow` is **strengthened** — the
  router is exactly such a seam.
- `image-generation`: `hosted:flow-declares-its-hosted-models` requires *"a model name for each of the
  first two stages"* and *"both model names"*. Stage ② calls no hosted model. The block keeps its key
  (carried dead) and the requirement stops claiming the sorter.
- `ui`: gains the cheatsheet's **server-side** contract — the payload carries every declared field's
  candidates, an empty group is present and empty, candidates are ranked by post count so *ranking is
  global* holds, and the excluded list is never served. **The keystrokes and the overlay's behaviour are
  deliberately not scenarios**: there is no browser test runner in this repo, and a scenario nothing can
  prove is worse than an honest human phase.

## Impact

| | |
|---|---|
| **`isekai/shared/field_map.py`** | new — the table's loader, its reverse index, the four checks. Beside `vocabulary.py`, which both `pipeline/` and `interface/` already import |
| **`scripts/field_map.json`** | new, **committed** — the authored table, beside `scripts/vocabulary.json` which the runtime already verifies against |
| **`scripts/derive_field_map.py`** | new — the authoring aid. **Stdlib, offline, no network.** A Danbooru wildcard intersected with the pin *is* a substring match against the pin; the 63 `hair_silhouette` tags reproduce from the local CSV in milliseconds |
| **`isekai/pipeline/sheet.py`** | `captions/` → `wd14/`, the router, the refusal; then −`Sorter`, −`Sorting`, −`FakeSorter`, −`ClaudeSorter`, −`OllamaSorter`, −`output_shape`, −`sorter_prompt`, −`answers_from`, −`SORTER_OPTIONS`, −`SORTER_REMEDY`, −nine `claude_cli` imports, −`map_phrase` |
| **`isekai/shared/vocabulary.py`** | −**12** names: `map_phrase`, `CURATED`, `CURATED_SPANS`, `_curated_pass`, `_index_of`, `contained_in`, `words`, `by_word`, `asserts_absence`, `_ABSENCE`, `_spans`, `_in_order`. **`normalise()` stays** |
| **`isekai/foundation/run.py`** | `BUDGETS["sheet"]` **3 → 1**. A deterministic router has no transient failure, as `"wd14": 1` already says |
| **`isekai/interface/wiring.py`** | −`Wiring.sorter`, −`_claude_sorter`, −`_ollama_sorter`, −`SORTERS`, −`sorter_for`. **`DEFAULT_IMPLEMENTATION` and `_named_by` survive** — the readers and hosted taggers still need them |
| **`isekai/interface/cli.py`** | −`_seam(wired.sorter, …)`; `sheet` keeps its verb, its `--flow` and its `--new-version` |
| **`isekai/interface/ui/app.py`** | `+ GET /api/fields` |
| **`ui/src/`** | `+ CheatsheetOverlay.vue` composing `.overlay` + `TagChip` + `.input`; `ReviewApp.onKey` gains two `event.code` branches and the focus round-trip; `TagInput` yields Escape and arrows while an overlay is open |
| **tests** | 46 reference lines across 10 files + `tests/stages.py:48`; 16 cascade functions (21 collected) in `test_vocabulary.py`; 4 in `test_sheet_schema.py`; 4 of the 5 briefing tests in `test_sheet_stage.py` (`:364` is kept as a schema/doc check) |
| **not touched** | `caption()`, `boundary/wd14.py`, `normalise()`, `review.py`, `generate.py`, `flow.py`'s digest walk, all three flow directories and their committed digests — **to be verified by `git grep`, not assumed** |
| **money** | **zero, every phase.** WD14 is a local ONNX pass, the authoring script reaches no network, and the acceptance requires no render. **A pod is a halt.** |
