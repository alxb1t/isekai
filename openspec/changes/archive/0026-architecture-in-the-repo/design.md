# Design — 0026 the architecture in the repo

How the sweep, `docs/`, `CLAUDE.md` and `README.md` are rewritten without changing what the system does.
**Verdict: `feasible`.** Every site, file and symbol below was re-checked at `main` `2ccda2f`.

## Context

- **`docs/arc/`** holds `modules.md` and `data-flow.md`. Each carries false claims ([D1](#d1)).
- **The principles and decisions** were drafted outside the repository and settled at the architecture
  grilling. They arrive here as [payload/](payload/), word for word ([D3](#d3)).
- **`CLAUDE.md`** mixes process with design rules that restate the principles and decisions, some of them
  false ([D8](#d8)).
- **Tests read some files this change edits** — `pyproject.toml`, `boundary/wd14.py`'s source, `cli.py`'s
  verb table — **but no string a test asserts changes.** No test names `README.md`, `CLAUDE.md`, `docs/` or
  `openspec/`: `git grep -n -e README -e CLAUDE.md -e openspec -e 'docs/' -- 'tests/*.py'` finds only a
  comment in `tests/test_evaluate.py`.
- **Line numbers are `2ccda2f`'s.** A builder re-resolves each site by its quoted *before* text.
- **`docs D<n>`** is decision `D<n>` of `docs/decisions.md`, drafted in [payload/decisions.md](payload/decisions.md).
  A bare `D<n>` is this design's.

## Goals / Non-Goals

**Goals**

- Every site in [D1](#d1) says what the code does.
- `docs/` holds the architecture: principles, decisions, modules, data flow, overview.
- `CLAUDE.md` holds process only, and imports `docs/principles.md`.

**Non-Goals**

- Any behaviour change, check, or new test.
- Any site a later version rewrites: the refusal remedies, the approval states, the attempt number, the
  transport's failure classification.
- Anything in the evaluation sub-system.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the sweep is the sites below, each with its *after* | a task needs one reading | "sweep the false claims" with no list |
| [D2](#d2) | requirement bodies change through the delta; `## Purpose` preambles are edited in the build | a delta cannot carry a Purpose | a Purpose edit at release |
| [D3](#d3) | the drafts ride in `payload/`; the build writes `docs/` from them in the prose rules | the build reads only the change | the build reading the notebook |
| [D4](#d4) | `docs/arc/` is flattened into `docs/`, with every link re-pointed in the same phase | one level; no dangling link at a phase's end | keeping `docs/arc/` |
| [D5](#d5) | how the components interact is a section of `docs/modules.md` | the module graph is where a reader looks for it | a new file |
| [D6](#d6) | phases: sweep, `docs/`, `CLAUDE.md`, group READMEs, `README.md` | a rule leaves `CLAUDE.md` only once `docs/` holds it | `CLAUDE.md` first |
| [D7](#d7) | the product scope becomes docs D29 and docs D30 | the repository holds no decisions page but `docs/decisions.md` | leaving it in the notebook |
| [D8](#d8) | `CLAUDE.md` keeps process, loses design rules, gains the id and patch rules | the builders read `CLAUDE.md` | a partial copy of each rule in each file |
| [D9](#d9) | the group READMEs point at `docs/` | *"the design record"* names nothing in the repository | deleting the line |
| [D10](#d10) | `README.md` keeps what the project is, how to run it, and the machines | it restated `data-flow.md` word for word | a second copy held equal by a test |
| [D11](#d11) | this is a patch | it meets every patch condition | a minor |

### D1

**The sweep is these sites.** Confirmed with the operator at the cut: the backlog's sweep rows, the review's
live findings, the grilling's passing finds, the review's *verified but too weak* claims, and the cut's own
finds. Each *after* is the meaning to write; the build words it under the prose rules.

**S47–S51 were added at the cut's reviews.** **Dropped as fixed at `2ccda2f`:** `EPISTEMICS-3` (`wd14.py`'s
`tagging` extra) and `isekai/interface/README.md:22`'s `[ui]` extra.

#### Phase 1 — code, tests, scripts, spec preambles

| id | site | before | after |
|---|---|---|---|
| S1 | `isekai/pipeline/tagging.py:15-19` | *"…and it ships anyway, marked for what is committable, because the panel is advisory and a wrong tag costs a glance (design.md D1, D15)."* | the artifact keeps every tag; the review surface shows only the tags the vocabulary carries — `interface/ui/app.py`'s `_tags` |
| S2 | `isekai/pipeline/tagging.py:21-24` | *"**`caption()` is not modified and is byte-identical in the diff.** … These two sit beside it and the CLI says three times."* | `caption_wd14` and `caption_tags` sit beside `caption()`, not inside it, and `cli.py` reports each artifact on its own |
| S3 | `isekai/pipeline/tagging.py:245-247` | *"**This is the first producer in this repository that can honestly claim a pin.** Every artifact in the tree records `pinned: false` and `show` prints *"unpinned"* over all of them;"* | this producer can claim a pin; the reader and the hosted tagger record `pinned: false`, and a sheet built from this list carries the `true` across (`pipeline/sheet.py`) |
| S4 | `isekai/interface/ui/batch.py:108-110` | *"…a flow with no `hosted` block never produces the sibling, and a failed tagger leaves neither -- three legitimate absences…"* | a run captioned before v0.20 has no such directory, and a failed tagger leaves its own list absent and every list after it — legitimate absences, none of which may stop a review |
| S5 | `isekai/interface/ui/batch.py:127-128` | *"which is what `reopened` below is for."* | *"which is what `state()` below is for."* |
| S6 | `isekai/foundation/run.py:560` | *"The CLI did not return what a stage can use, and the kind says what next."* | *"A model call did not return what a stage can use, and the kind says what next."* |
| S7 | `isekai/foundation/run.py:633` | *"was a sixth file in the flow directory"* | *"was another file in the flow directory"* |
| S8 | `isekai/foundation/flow.py:60` | *"so a sixth sibling cannot be added silently"* | *"so a sibling cannot be added silently"* |
| S9 | `tests/test_flow.py:168` | *"the silent addition of a sixth sibling"* | *"the silent addition of a sibling"* |
| S10 | `scripts/derive_field_map.py:30-33`, `:165-167` | names `flows/conjure-v1/sheet.briefing.md` as a file that exists and that *"this version"* reads | the briefing is deleted; its example tags were transcribed before it went, and `BRIEFING` holds them |
| S11 | `tests/test_sheet_stage.py:63` | *"`tests/test_isolation.py`'s argument, applied to…"* | *"The isolation argument, applied to…"* |
| S12 | `pyproject.toml:41` | *"serves six endpoints and a built bundle."* | *"serves a JSON API and a built bundle."* |
| S13 | `tests/test_pipeline_cli.py:15-16` | *"this guard is the only thing that would catch a module-scope import appearing here -- nothing else fails when one is added."* | installed by default, a module-scope import resolves rather than failing, so this guard is what catches one; `tests/test_wd14.py`'s source scan also catches one in `boundary/wd14.py` |
| S14 | `tests/test_wd14.py:265-266`, `:268-269` | *"this file is the only one in the package that touches `onnxruntime`, `numpy` or `Pillow`"*; *"this is the only thing that would catch one moving to module scope -- nothing else fails when it does."* | this file reaches `onnxruntime`, `numpy` and `Pillow` through `_require`, inside the function that needs each — and `evaluation/eval_backends.py` touches them too (`_numpy()`, `_pil()`, `OnnxSession.__init__`). This scan catches one moved to module scope, and so does the `-S` guard in `tests/test_pipeline_cli.py`, because `cli.py` imports `wd14.py` at module scope |
| S15 | `isekai/boundary/wd14.py:18-19` | *"Being installed by default is what makes that guard the only check"* | installed by default, an import moved to module scope resolves; the `-S` guard and `tests/test_wd14.py`'s source scan catch it |
| S16 | `isekai/README.md:46` | *"so that guard is the only check on this."* | *"and that guard is what checks this."* |
| S17 | `isekai/boundary/README.md:40-41`, `:43-45` | *"it is the only module in the package that touches the tagger's stack"*; *"so that guard is the only thing that would catch one moving to module scope;"* | `wd14.py` touches the tagger's stack, as `evaluation/eval_backends.py` does too; one import moved to module scope resolves silently, and the `-S` guard and `tests/test_wd14.py`'s source scan catch it |
| S18 | `isekai/README.md:26-27` | *"Every `__init__.py` here holds a docstring and no code"* | every group's `__init__.py` holds a docstring and no code; `interface/ui/__init__.py` is a subpackage's front door and holds `serve()` |
| S19 | `isekai/shared/vocabulary.py:1-20` | the cascade, the four-pass mapping, *"it still ships"*, *"Every pass, the curated table included…"* | the docstring names what the file holds — `normalise()`, `Vocabulary`, `read_tags()`, `load()`, `identity()` — and says the no-invented-tag guarantee holds by construction elsewhere: WD14's labels are the vocabulary, and `shared/field_map.py` is a table over it |
| S20 | `isekai/shared/image.py:260-261` | *"the runtime carries no imaging wheel and this is on `python -m isekai`'s import graph."* | *"this is on `python -m isekai`'s import graph, which reaches no wheel."* |
| S21 | `isekai/pipeline/generate.py:341-344` | *"The four below read dials a flow that has no identity adapter, no pose preprocessor and no hires pass does not declare"* | the guards below read dials a flow without that role does not declare — an identity adapter, a pose preprocessor, a clip skip, a hires pass |
| S22 | `isekai/interface/run_view.py:5-6` | *"nothing but a human is watching before a review UI exists, and the inspection command is what that human reads."* | a person reads this command, and the review UI reads the run directory itself |
| S23 | `isekai/pipeline/review.py:235-236` | *"changing its signature would move 26 call sites"* | *"changing its signature would move every one of its call sites"* |
| S24 | `isekai/interface/cli.py:14-15` | *"caption   (1) a photograph in, descriptive prose out"*; *"sheet     (2) prose in, a sheet of canonical tags out"* | *"caption   (1) a photograph in; prose, the WD14 tags and the hosted tags out"*; *"sheet     (2) the WD14 tag list in, a sheet of canonical tags out"* |
| S25 | `isekai/interface/cli.py:75-76` | `("caption", "read a photograph into descriptive prose")`; `("sheet", "sort a caption into a sheet of canonical tags")` | `("caption", "read a photograph into prose, the WD14 tags and the hosted tags")`; `("sheet", "fill a sheet of canonical tags from the WD14 tag list")` |
| S26 | `isekai/interface/cli.py:146` | `"The staged pipeline: photograph -> prose -> sheet -> render."` | `"The staged pipeline: photograph -> tags -> sheet -> render."` |
| S27 | `isekai/interface/cli.py:435-436` | *"Prose first, because it is the only one of the three anything downstream reads."* | *"prose first; the sheet reads the WD14 list, so a prose refusal abandons that list too — a known cost"* |
| S28 | `openspec/specs/comfy-transport/spec.md:14-16` | *"The runtime is **stdlib-only**: the multipart body is built by hand…"* | the transport is on `python -m isekai`'s import graph, which reaches no wheel, so the multipart body is built by hand… |
| S29 | `openspec/specs/model-provisioning/spec.md:15-17` | *"so this capability leaves the stdlib-only runtime rule untouched."* | *"so this capability leaves the entry point's import rule untouched."* |
| S30 | `openspec/specs/sheet/spec.md:5-7` | *"turning descriptive prose into a sheet of fields filled with canonical vocabulary tags, using the schema and the standing instructions inside the flow that asked"* | filling a sheet's fields with canonical vocabulary tags from the WD14 tag list, through the field map, against the schema inside the flow that asked |

#### Phase 2 — `docs/`, and the layer claim it contradicts

S48 edits `isekai/README.md` here, not in phase 4: the contradiction appears the moment
`docs/principles.md` lands, so it goes in the same phase.

| id | site | before | after |
|---|---|---|---|
| S31 | `docs/arc/data-flow.md:39` | *"The two verbs outside the stages each differ"* | *"`show` and `ui`, which are not stage verbs, each differ"* |
| S32 | `docs/arc/data-flow.md:47-56` | *"…and the order is the failure isolation. … Prose goes first because it is what a human reads before anything else."* | the order was chosen to isolate failures when the sheet was built from prose; the sheet reads the WD14 list now, so a prose refusal — Ollama unreachable — stops the sheet's input too (docs D1) |
| S33 | `docs/arc/data-flow.md:58-61` | *"a missing *hosted* tag list is an absent aid and never a refusal — the model may simply not be running"* | a missing hosted list is an absent aid and never a refusal — its own call failed after the prose and the WD14 list were written |
| S34 | `docs/arc/data-flow.md:128-129` | *"a WD14 artifact is the only producer here that records `pinned: true`"* | a WD14 artifact records `pinned: true`, and a sheet built from it carries that across; the reader and the hosted tagger record `false`, and `show` marks theirs *unpinned* |
| S35 | `docs/arc/modules.md:35-39` | *"Neither `boundary`, nor `evaluation`, nor the surface's `fastapi`/`uvicorn` may sit at module scope… Move any of those imports to module scope and that guard goes red"* | the `-S` guard goes red when a chain of module-scope imports from the entry point reaches a wheel. The lazy edges above are between this package's own modules and reach no wheel, so moving one leaves the guard green; review holds them |
| S36 | `docs/arc/modules.md:97-100` | *"**The `-S` guard in `tests/test_pipeline_cli.py` is now the only thing holding this.**"* | the `-S` guard holds this, and `tests/test_wd14.py`'s source scan holds it for `boundary/wd14.py` |
| S47 | `docs/arc/modules.md:8-12` | *"the group graph does, and drawing it as a stack would be a lie. … A group is a filing decision … and not a layer."* | the layers are the rule (`docs/principles.md`): imports point down, and nothing in the package imports `evaluation`. The module graph has no cycles. Today's upward imports, the group cycles below, and the lazy `shared → evaluation` and `boundary → evaluation` edges below are the rule's known breaks, removed by the change that moves those imports |
| S48 | `isekai/README.md:30-32` | *"**A group is a filing decision, not a layering rule.** … drawing it as a stack would be a lie."* | the layers are the rule (`../docs/principles.md`): each group but `evaluation` is a layer, imports point down, and nothing in the package imports `evaluation`. The module graph has no cycles. Today's upward imports, group cycles, and imports from `shared` and `boundary` into `evaluation` are known breaks, removed by the change that moves those imports |
| S49 | `docs/arc/modules.md:86-88` | *"Each wheel-needing tree is still reached from a single named module — … the tagger's stack from `boundary/wd14.py`"* | each wheel-needing tree is reached from inside a function or behind a lazy import: `fastapi`/`uvicorn` from `interface/ui/app.py`; `[eval]` from `evaluation/eval_backends.py`, which also reaches `numpy`, `Pillow` and `onnxruntime` (`_numpy()`, `_pil()`, `OnnxSession.__init__`); the tagger's stack from `boundary/wd14.py` |
| S50 | `docs/arc/modules.md:52-57` | *"`run` writes every artifact through it, so `foundation` reaches down into `shared`. … Both edges point at whatever is more primitive than the module reaching for it."* | `run → atomic_write` points up, from `foundation` into `shared`: a known break of the layers, removed by the change that moves those imports. `fields → flow` points down |
| S51 | `docs/arc/modules.md:69-71` | *"Read the group edges as *what each group is allowed to know about*, and go to the module graph when the question is whether something is acyclic."* | the layers are the rule: a group imports from itself and the layers below it (`docs/principles.md`). An edge that points up, or into `evaluation`, is a known break. Go to the module graph when the question is whether something is acyclic |

#### Phase 3 — `CLAUDE.md`

| id | site | before | after |
|---|---|---|---|
| S37 | `CLAUDE.md:27` | *"**Identity preservation is the product.** A beautiful anime image of someone else is a failed run."* | identity preservation is `summon`'s product: an anime image of someone else is a failed `summon` run. `conjure` takes no photograph and makes no identity claim (docs D10) |
| S38 | `CLAUDE.md:34-35` | *"the `-S` guard in `tests/test_pipeline_cli.py` is the only thing that catches a violation."* | leaves with its constraint ([D8](#d8)) |
| S39 | `CLAUDE.md:208` | a 142-character line | re-flowed to the file's width, near 101 |
| S40 | `CLAUDE.md:253-255` | *"**Everything a run reads or writes is inside the repository.**"* | the repository-path anchors resolve inside the repository — `tests/test_package_paths.py` pins each one; a runs root defaults to `.data/runs`, may sit outside the repository, and inside it must sit under `.data/` (docs D18) |
| S41 | `CLAUDE.md:275-277` | *"The ordering is the failure isolation and is not free to change"* | leaves with its section ([D8](#d8)); docs D1 states the true reason |
| S42 | `CLAUDE.md:36-40` | *"**A selectable implementation is a measured one.**"* | deleted: the registry it governed is gone, and a new model is a new flow |

#### Phase 5 — `README.md`

| id | site | before | after |
|---|---|---|---|
| S43 | `README.md:8-9` | *"reads a photograph into prose, sorts the prose into a sheet of canonical tags"* | reads a photograph into prose and tags, fills a sheet of canonical tags from the tags by a table |
| S44 | `README.md:124-125` | *"the hosted one is silently absent when Ollama is not running, which is never an error;"* | if Ollama is not running, `caption` refuses the photograph at the prose, before either list; the hosted list alone is absent only when its own call failed |
| S45 | `README.md:126-127` | *"Neither tag list is narrowed — they are what the review surface shows beside the prose"* | neither list is narrowed on disk; the review surface shows the WD14 list, and the hosted list filtered to what the vocabulary carries |
| S46 | `README.md:313-315` | *"The root `Makefile`, this file and CI … mirror it; change one and you change all four"* | the root `Makefile` and this file mirror it, and CI runs `make gate`; change the array and you change the `Makefile` and this file, in the same commit |

### D2

**A requirement's body changes through the delta; a `## Purpose` preamble is edited in the build.**

```
openspec/specs/<cap>/spec.md
  ## Purpose        ← not requirement text: edited in phase 1 (S28, S29, S30)
  ## Requirements   ← changed only by a MODIFIED block in specs/, folded at release
```

`openspec instructions specs` says a delta's `## Purpose` is ignored, and to edit the main spec directly.
Commit `3c30094` (`0022`) did exactly that for `**Source:**` headers. The MODIFIED blocks in `specs/`:

| capability | requirement | sentence |
|---|---|---|
| `cli` | *The pipeline surface is the only entry point, and its verbs are subcommands* | *"the stdlib-only guard"* → *"the entry point's import guard"* |
| `cli` | *The rendering verb takes many photographs and either a count or explicit seeds* | *"Reading and sorting are cheap"* → *"Reading and filling a sheet are cheap"* |
| `image-generation` | *A failure is recorded as the kind it was, and one flow's failure is its own* | the scenario's *"attempts the work rather than refusing on the record"* → *"refuses on the record, naming it, until the record is deleted"*; the rationale says what a kind buys at a budget of one (`run.py`'s `BUDGETS["render"]`, `check_budget`) |
| `model-provisioning` | *The manifest declares every artifact the shipped graph requires* | *"while `summon-v1` is the only flow, that is its graph"* deleted |
| `ui` | *A tag artifact that is absent is silent* | *"a flow that declares no hosted model"* leaves the absences; *"every flow that can never have one"* becomes *"every input whose list is missing"*; *"he"* → *"they"* |

### D3

**The drafts ride in the change as `payload/`, and the build writes `docs/` from them.**

```
payload/principles.md ──▶ docs/principles.md
payload/decisions.md  ──▶ docs/decisions.md   (+ docs D29, docs D30, per D7)
payload/overview.md   ──▶ docs/README.md
```

- **Word for word**, frontmatter stripped: `cmp` against each draft's body passed at the cut. Nothing in them
  names the notebook.
- **The prose rules change form only** (`P1`–`P13`). The payload's titles, statements and measured figures
  stay as written.
- **`W3` governs claims about what the code does, not rules.** A principle is a rule, and its *Held by* line
  states what enforces it: a test, review, or *not yet*; a decision is a rule too. So a principle's or a
  decision's *only* and *never* stay as written — *"only `up.sh` knows the image…"* included.
- **No principle or decision may change what it says.** Converge compares `docs/` against `payload/`; a rule
  whose meaning moved is a blocking finding.
- **`payload/` is never edited.** `openspec validate --strict` accepts it beside the artifacts.

### D4

**`docs/arc/` is flattened into `docs/`, by `git mv`, and every link to it is re-pointed in the same phase.**

```
docs/
├── README.md       from payload/overview.md
├── principles.md   from payload/principles.md
├── decisions.md    from payload/decisions.md
├── modules.md      git mv from docs/arc/
└── data-flow.md    git mv from docs/arc/
```

Links to re-point: `CLAUDE.md` (every `docs/arc/`), `README.md:374`, `isekai/README.md:34`. `CHANGELOG.md`'s
released sections keep `docs/arc/`: they are history.

### D5

**`docs/modules.md` gains `## How the components interact`**, an ASCII diagram and a few lines. It states
these facts, each true at `2ccda2f`:

- The CLI builds the components through `interface/wiring.py` and hands them to the review UI its `ui`
  verb starts (`cli.py:258-260`). The UI builds no component: nothing under `interface/ui/` calls a builder
  in `wiring.py`.
- Each front end calls the stage functions directly.
- No module under `interface/ui/` imports `cli.py`.
- A stage reads and writes its run directory. No stage imports another stage; review holds this until the
  layer test lands.
- A stage reaches a model, the GPU or the network through `boundary/`.
- `foundation`'s run, flow and refusal are what every layer uses.
- `StageFailure` lives in `foundation/run.py`, not `refusal.py`: `refusal.py` imports nothing, the class
  needs `Kind`, and `run.py` already imports `refusal.py` — the move would be a cycle. (Moved from
  `CLAUDE.md`, [D8](#d8).)

### D6

**Phase order: sweep → `docs/` → `CLAUDE.md` → group READMEs → `README.md`.**

```
1 sweep ──▶ 2 docs/ ──▶ 3 CLAUDE.md ──▶ 4 group READMEs ──▶ 5 README.md
            holds the     loses what       point at docs/     loses what
            rules          docs/ holds                          docs/ holds
```

A rule leaves `CLAUDE.md` or `README.md` only after `docs/` holds it — the old thing stays declared until
the new one is in place.

### D7

**The notebook's product scope becomes docs D29 and docs D30**, under *The product*, after docs D0.

| notebook row | disposition |
|---|---|
| identity | already: docs D10, and S37 in `CLAUDE.md` |
| scope — face, hair, clothes, pose | **docs D29** |
| tattoo — outside the scope | **docs D29** |
| open — open models, self-hosted | already: docs D0 |
| payoff — learning and portfolio | **docs D30** |
| repo — a public repository, not a service | **docs D30** |
| measured — the evaluator, not by eye | not carried: evaluation's, parked with the measurement principles |
| order — photo path before character LoRA | not carried: unbuilt work, and `docs/` holds current state |

The text to write, in `docs/decisions.md`'s format:

```
### D29 · What `summon` preserves

**Identity is face, hair, clothes and pose, held together. A tattoo is outside it.**

- **Why:** these are what a viewer checks first. The graph carries the face and the pose, and the
  approved sheet's tags carry hair and clothes (D10). A tattoo is local and arbitrary; neither
  holds it, and bundling it would make every version a research version.
- **Made by:** the project's founding decision.

### D30 · A public repository, for learning

**The deliverable is a public repository, not a hosted service. Its payoff is learning and a
portfolio piece, not product polish.**

- **Why:** a portfolio piece is read, not signed up for, and tuning comes after the stack runs
  end to end.
- **Made by:** the project's founding decision.
```

### D8

**`CLAUDE.md` keeps process, imports `docs/principles.md`, and loses the design rules it restates.**

| `CLAUDE.md` today | disposition | lives in |
|---|---|---|
| opening paragraphs and the ceiling note | kept; `docs/arc/` → `docs/` | — |
| hard constraint: identity | rewritten, S37 | `CLAUDE.md`; docs D10 |
| hard constraint: the entry point imports no third-party package | moved out; the guardrail *Deps minimal* keeps the agent's half | docs D20 |
| hard constraint: a selectable implementation is a measured one | deleted, S42 | — |
| the note *standing instructions, not a workflow … the prompt wins* (`:42-44`) | kept | — |
| the quality gate | kept | — |
| *design.md is authoritative … and nowhere else* | rewritten: `docs/decisions.md` records the decisions in force; a change's `design.md` records why one was taken, frozen when archived | `CLAUDE.md` |
| seams: a parameter is a seam | moved out | principle *A component is a contract* |
| seams: the flow manifest declares | moved out | principle *Configuration is declared* |
| seams: a network boundary lives in `boundary/` | moved out | principle *The code is layered* |
| seams: `StageFailure`'s home | moved out | `docs/modules.md` ([D5](#d5)) |
| seams: the run owns the layout; no stage imports another | moved out | principle *The run directory is the only channel*; docs D17 |
| seams: Option keybindings | moved out | docs D25 |
| tests are bound to the spec | kept | — |
| how a change is cut | kept; the id rule rewritten; patch conditions added | — |
| layout: `__main__.py`, a group's `__init__.py` | moved out | principle *The code is layered*; `docs/modules.md` |
| layout: `flows/` frozen, flat, named, and its naming rule | design moved out; the process kept — adding or re-pinning a flow costs a `PINNED` line and a `CHANGELOG.md` entry with its digest, a re-pin states what moved, the comment above `PINNED` states the rule and not its history | docs D14, docs D15, principle *Everything … is pinned* |
| layout: a derived file is byte-identical | design moved out; the process kept — a new evaluator artifact owes an `eval_licences.md` entry | principle *Configuration is declared* |
| layout: `openspec/`, `.minions/`, `.data/`, the ignored roots | kept | — |
| layout: everything a run reads or writes is inside the repository | rewritten, S40 | `CLAUDE.md`; docs D18 |
| rules the render path is under — the whole section | moved out; replaced by a pointer to `docs/principles.md` and `docs/decisions.md`, read before changing anything they decide | the principles; docs D1, docs D3, docs D22, docs D23 |
| guardrails | kept | — |

**Added:**

- **The import**, near the top: `@docs/principles.md`, so every session has the principles.
- **The change id is the next free number** — higher than every id under `openspec/changes/` and its
  `archive/`. The `(major × 100) + minor` formula goes: it gives the next minor `0023`, which `v0.22.1` holds.
- **What a patch may hold.** A minor delivers one feature; a patch delivers none, and meets every one of these:
  - no format version moves — `MANIFEST_VERSION`, the artifact envelope's `SCHEMA_VERSION`;
  - every behaviour fix is required by an existing requirement: a scenario may be added under one, a
    requirement may not;
  - nothing deprecates a verb or a flag;
  - nothing changes the product — a sheet's fields, the prompt, the image — for the same inputs and
    configuration.

  Work that cannot meet them is not a patch.
- **The notebook rows the repository did not hold:**

| notebook row | disposition |
|---|---|
| no notebook path in any file | added: the repository holds no pointer to the operator's notebook — no path, no variable naming it. **Review holds this; no test does** |
| the notebook reads the repository, never the reverse | added, with the row above |
| demo subjects | added: a demo subject is a synthetic portrait, never a real person's photograph |
| no personal photograph committed | already: the `.data/` bullet |
| `.env` holds the paths; `.env.example` shape only | already: the guardrails |
| `.gitignore` written first | not carried: a bootstrap step, done |
| the spec lives in `openspec/`; the gate; every test bound | already |
| agents build each version; findings closed before release; learning notes | not carried: the skills' rules, or the notebook's |

### D9

**Each group README's closing line points at `docs/`.** The group READMEs are `isekai/README.md` and the
`README.md` of `boundary`, `evaluation`, `foundation`, `interface`, `pipeline` and `shared`.

```
before:  > Files and importers only. What a seam *is*, and what could replace it, is the
         > design record's; neither restates the other.

after:   > Files and importers only. What a component *is* is `docs/principles.md`'s, and the
         > choices in force are `docs/decisions.md`'s; neither restates the other.
```

Each path is a relative link: `../docs/` from `isekai/README.md`, `../../docs/` from a group's.

### D10

**`README.md` keeps what the project is, how to run it, and the machine topology.** It links to `docs/` for
the rest.

| section | disposition |
|---|---|
| title, intro, status banner | kept; S43 |
| *Why this exists* | kept |
| *How it works* | kept; *"one path (see below)"* points at `docs/`; the *Interface* bullet names the import rule by docs D20 instead of restating it |
| the local/RunPod diagram and *Lifecycle* | kept |
| *The path* | removed: its identity table is `data-flow.md`'s, its flow paragraph is docs D14 and docs D15, its scaling paragraph repeats `shared/image.py`. Replaced by `## Architecture`: one line and links to the files in `docs/` |
| *Running a flow* | kept; S44, S45 |
| *Setup* | kept |
| *Development* | kept; S46; its closing line names `docs/` beside `CLAUDE.md` |
| *Repository layout* | kept; `docs/arc/` → `docs/` |
| *Provisioning flow*, *Cost*, *License* | kept |

### D11

**This is a patch.** It meets each condition [D8](#d8) writes into `CLAUDE.md`:

| condition | met because |
|---|---|
| no format version moves | no `flows/` file, manifest or artifact writer is touched |
| a behaviour fix is required by an existing requirement | no behaviour is fixed; the delta corrects prose to what the code does |
| nothing deprecates a verb or a flag | no verb or flag changes |
| nothing changes the product | the sheet, the prompt and the image are untouched; the `caption` and `sheet` verbs' help text, the parser's description and `scripts/derive_field_map.py --help` change |

## Dependencies

None.

## Risks / Trade-offs

- **Terse rewriting moves a rule's meaning.** → Converge compares `docs/` against `payload/`, and a moved
  meaning is blocking ([D3](#d3)).
- **An agent loses a design rule from `CLAUDE.md` that `docs/decisions.md` holds but no session imports.** →
  `CLAUDE.md` names `docs/decisions.md` to read before changing anything it decides; the guardrails keep the
  import half of docs D20.
- **`docs/modules.md`'s edges and cycles change again when the layers move.** → Accepted: this change makes
  it true at `2ccda2f`, and the change that moves the layers corrects it.
- **`image-generation:failure:an-unreachable-endpoint-is-transient`'s test asserts only the first THEN.** →
  Unchanged; no check is added here. The corrected clause is true of `check_budget`.
- **The sweep list is a reconstruction.** The grilling's own list of sites was not written down. → The
  operator confirmed [D1](#d1) at the cut.
- **The build finds more false claims as it edits.** → Outside [D1](#d1), a find is reported, not fixed.

## Verdict

**`feasible`.** Prose only, every site re-checked at `2ccda2f`, no string a test asserts changes, and the
payload is settled.
