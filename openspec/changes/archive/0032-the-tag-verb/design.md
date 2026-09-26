# Design — 0032 the tag verb

How `caption` and `tag` become two verbs, how a flow declares the tagger, and what the sheet and the review
surface do with that declaration. **Verdict: `feasible`.** Every file, symbol and line below was re-checked
at `main` `50a6b17`.

## Context

- **`caption` runs the prose, WD14 and the hosted tagger per flow** (`isekai/interface/cli.py:404-447`): `caption()` (the prose,
  `<flow>/captions/`), `caption_wd14` (`<flow>/wd14/`), `caption_tags` (`<flow>/tags/`). `across()`
  (`isekai/foundation/run.py:534-547`) catches `Refusal` per input, so a prose refusal abandons the WD14 list.
- **Who reads what:** `sheet` reads only `wd14/` (`isekai/pipeline/sheet.py:112-128`). The prose and the
  hosted list are read by the review surface and `show` only. A missing caption reaches the page as
  `caption: null` (`isekai/interface/ui/app.py:265-270`).
- **The manifest:** `REQUIRED` (`isekai/foundation/flow.py:71-81`), `KNOWN = REQUIRED` (`:92`),
  `MANIFEST_VERSION = 3` (`:51`), one version read (`:380-385`), `Flow` (`:256-268`), the only type check on
  `model` (`:416-421`). The module docstring (`:16-17`) says any change *"creates a new identifier"*;
  `image-generation`'s pinned-by-equality requirement allows a re-pin when the old configuration is
  abandoned.
- **The freeze:** `PINNED` (`tests/test_flow.py:49-56`);
  `test_a_re_pin_leaves_a_record_a_later_reader_can_find` wants each pinned digest in `CHANGELOG.md`.
  **Precedent:** `0016` re-pinned `summon-v1` in place for a format-only version move.
- **The verb in remedies:** `tagging.py:61` `VERB = "caption"`; `sheet.py:115-128`;
  `isekai/boundary/ollama.py:199` (*"stages 1 and 2 of this flow"*).
- **Nothing reads `filename_prefix`** (`flows/summon-anime-wai/graph.json:174`,
  `flows/conjure-anime-wai/graph.json:96`), and the pod image copies no flow.

## Goals / Non-Goals

**Goals**

- Each verb writes its own artifacts, and `--new-version` has one meaning per verb.
- The sheet's input never waits on Ollama.
- A flow says whether it is tagged, and each stage honours that without learning about flows.

**Non-Goals**

- Anything the [proposal](proposal.md#not-in-this-change) sets out.
- A second tag list source, or a tagger chosen per flow.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | a required boolean `tagger`; `MANIFEST_VERSION` 4; both flows re-pinned in place | flows now differ in whether they are tagged; the configuration did not change, only the format | an optional key defaulting to `true`; new identifiers |
| [D2](#d2) | `tag` runs WD14 then the hosted tagger, each refusal collected on its own; `caption` runs the prose only | the sheet's input stops waiting on Ollama; each verb owns its artifacts | the order as isolation; a skip for a tagger-free flow |
| [D3](#d3) | the composition root tells `sheet()` whether a tag list is expected; a flow that declares none gets empty fields | the stage stays ignorant of flows; an empty fill hides nothing when no tagger was going to run | the stage reading the `Flow`; a refusal with no working fix |
| [D4](#d4) | the review payload carries the command that writes a missing caption | a skipped `caption` is the one skipped verb that reaches review | silence; the browser spelling the command |
| [D5](#d5) | D1 rewritten, D31 added, ① drawn as two verbs | `docs/` records the decisions in force | leaving D1's known consequence standing |
| [D6](#d6) | a minor, one feature | the split is the feature; the key and the empty fill are its parts | a patch |

### D1

**The manifest declares `"tagger": true | false`.**

- A required top-level key, written after `"model"` in both `flow.json`. `REQUIRED` gains it and
  `KNOWN = REQUIRED` stays. `Flow` gains `tagger: bool`.
- `load_flow` checks it after `model` (`flow.py:416-421`), with `isinstance(value, bool)`: a string, a
  number or `null` is refused naming the key, never coerced. Order stays version → unknown keys → missing
  keys → prompt → `model` → `tagger` → the rest.
- `MANIFEST_VERSION` 3 → 4; both manifests declare `"manifest_version": 4` and `"tagger": true`.
- **Re-pinned in place**, on `0016`'s precedent: a new identifier would claim a variant that does not exist,
  and `show` refuses a run holding a retired id (`isekai/interface/run_view.py:161-162`). The phase's
  CHANGELOG entry carries both new digests and states what moved — the key, the version, `filename_prefix`.
- **`filename_prefix` rides the same re-pin** (`v0.22 review/R6`): each graph's prefix becomes its flow's id.
  The image is unchanged; `flow_graph_sha256` moves, so renders before and after are told apart. The
  `render` golden (`tests/golden/render.json`) is re-captured: its two graph digests move, and no other byte.
- **Stale prose in `flow.py`:** the docstring (`:16-17`) states the spec's rule — a divergence is a new
  identifier, an abandoned configuration a recorded re-pin; the `model` refusal (`:420`) says *"the one model
  its reader and its hosted tagger run"*; the comment on `model` (`:94-99`) says the same. The remedies
  that say *"under a new flow identifier"* stay: they name the divergence, which is still the default.

### D2

**Two verbs, each writing its own artifacts.**

```
caption  ── caption() ──────────────▶ captions/
tag      ── tag_wd14() ─────────────▶ wd14/      ┐ each refusal collected
         ── tag_hosted() ───────────▶ tags/      ┘ on its own; both run
```

- `VERBS` (`cli.py:65-73`): `caption` reads a photograph into prose; `tag` scores it with WD14, then lists the
  JoyCaption tags. `tag` takes `--flow` (`:171`) and `--new-version` (`:180`).
- **Isolation.** `_per_item` (`:342`) is handed a list, and the `tag` branch appends each tagger's `Refusal` to
  it and moves on, the way `_generate` collects `broken`; `dispatch` (`:295`) reports that list with
  `across`'s. A `_seam` refusal is not caught: it is the wiring's, not a tagger's. WD14 runs first.
- **A flow that declares no tagger** is refused in `dispatch`, after `_flows_for` (`:313`) and before any
  identifier: *"`<flow>`'s manifest declares `\"tagger\": false`, so `tag` has nothing to do for it; drop
  `--flow <flow>` from the command"*.
- **Renames:** `caption_wd14` → `tag_wd14`, `caption_tags` → `tag_hosted`. `tagging.py`'s `VERB = "tag"`
  (`:61`), with its comment and the module docstring.
- **Remedies name `tag`:** `sheet.py:115-128` —
  before: *"run \`python -m isekai caption --flow {flow} {run.id}\` first"*
  after: *"run \`python -m isekai tag --flow {flow} {run.id}\` first"*; the malformed-list remedy becomes
  `tag --new-version`, then `sheet --new-version`. `ollama.py:199` says *"the reader and the JoyCaption
  tagger need it"*.
- **`--new-version`** needs no code of its own: each verb passes the flag only to the functions it runs. That
  closes `v0.20 grilling — --new-version`.
- `wiring.tagger_for`'s docstring (`isekai/interface/wiring.py:132`) says the key decides *whether*, in
  `cli.py`, and nothing in the manifest says *which*.

### D3

**The sheet is told whether a tag list is expected.**

- `sheet()` gains a required keyword, `tagged: bool`. `cli.py` passes `flow.tagger`; `tests/stages.py`'s
  helper passes it. No default: a default decides silently.
- `tagged` and no list → today's refusal, naming `tag`.
- Not `tagged` → no list is read. Every schema field is written empty through `route` and `validate`, and
  the vocabulary and field map are recorded as always. The producer is
  `{"implementation": "empty", "models": [], "pinned": true, "artifacts": {}}`, with no `from`.
- **`pinned: true`:** nothing unpinned shaped the sheet; `false` would make `show` print *unpinned* for a sheet
  no model touched.
- `SheetProducer`'s `from` becomes `NotRequired[int]` (`isekai/foundation/artifacts.py:124-133`). The sheet
  kind stays version 1: every existing sheet still reads, and `show` already tolerates a missing `from`
  (`run_view.py:98`).
- A `sheet-empty` golden joins `KINDS` (`tests/test_artifact_bytes.py:123-135`).

### D4

**A missing caption is shown with its command.**

- `read_input` (`app.py:245`) adds `caption_command`: `null` when a caption exists, otherwise
  `python -m isekai caption --flow <flow> <run>`. The server builds it; the browser never spells a command.
- `ui/src/types.ts`'s `InputDetail` gains `caption_command: string | null`; `ReviewApp.vue` passes it through
  `SourcePanel.vue` to `CaptionPanel.vue`, which shows *no caption* and the command when the prose is `null`
  and nothing is loading.
- The comments that say *"a flow with no hosted block"* (`ui/src/types.ts:72`,
  `ui/src/components/SourcePanel.vue:20`) say *"a flow that declares no tagger"*.
- **`0031 R8`/`S6`:** `_update_during_approval` in `tests/test_ui_api.py` bounds both waits (`:586`, `:593`)
  and asserts them, so a regression fails instead of hanging.

### D5

**The record.**

- `docs/decisions.md`: D1 becomes *Stage ① is two independent verbs* — its known consequence closes; **D31**,
  under *Flows*: *a flow declares whether it is tagged, and the sheet reads the declaration*.
- ① is drawn as two independent verbs, `tag` (the sheet's input) and `caption` (the reviewer's aid), and the
  walk-through runs `tag`, `caption`, `sheet`, `ui`: `docs/data-flow.md`, `docs/README.md:16`,
  `README.md`, `CLAUDE.md:7-8`.
- The manifest's key list names `tagger`: `docs/principles.md:146-148`, `README.md:331`.
- `docs/modules.md:62-63`, `isekai/README.md:11`, `isekai/pipeline/README.md:10-23`, `cli.py`'s module
  docstring (`:9-24`) and the `cli` and `sheet` spec preambles, which no delta can fold.

### D6

**A minor.** It adds a verb, moves `MANIFEST_VERSION` and changes what `caption` writes; the product — a
sheet's fields, the prompt, the image — is unchanged for both tracked flows. One feature: the split. The
manifest key and the empty fill are what make a tagger-free flow expressible, which is the split's reason.

## Rows carried

| row | taken in | how |
|---|---|---|
| `v0.20 grilling — --new-version` | [D2](#d2) | one meaning per verb |
| `v0.22 review/R6` | [D1](#d1) | `filename_prefix`, inside the re-pin |
| `0031 review/R8`, `security/S6` | [D4](#d4) | bounded waits in a file phase 4 edits |
| `cli`'s stage-verb list, deferred by `0026` to this split | the `cli` delta | `tag` joins it; *"sorting"* goes |

## Dependencies

None.

## Risks / Trade-offs

- [An operator runs `caption`, then `sheet`] → `sheet` refuses naming `tag`, with the run id.
- [A run tagged by the old `caption`] → its lists stand; `tag` finds them complete and writes nothing.
- [Ollama down during `tag`] → every photograph prints the hosted tagger's refusal; the WD14 lists are written.
- [The tagger-free path runs on no tracked flow] → a fixture flow in the tests is its only proof, until a
  flow declares `false`.
- [Another exception to the freeze, after `0016`'s and `0025`'s] → it is format-only, recorded in the
  CHANGELOG with both digests, and it carries `filename_prefix` so no later re-pin is owed for it.

## Verdict

`feasible`.
