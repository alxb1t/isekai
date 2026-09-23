# isekai — operating instructions for an agent

A self-hosted, headless pipeline: **photo of a person → anime image of that same person**, using open
models on an on-demand RunPod GPU running our own ComfyUI image. It exists to learn — and to show — how
open image models are run end to end, from container to rented GPU to CLI. Two flows —
`summon-anime-wai` from a photograph, `conjure-anime-wai` from a corrected sheet alone — on a
WAI-illustrious-SDXL v17.0 base, driven by staged verbs an operator runs one at a time: `caption` →
`sheet` → `review`/`approve` → `generate`, with `show` reading a run and `ui` putting stage ③ in a
browser. Everything before `generate` is free and local; only the render costs money.

> **That paragraph is the ceiling, and the ceiling is the point.** A fuller account — the verbs, what
> each stage reads and writes, the run layout, the identity mechanisms and their dials — belongs in
> [`docs/arc/data-flow.md`](docs/arc/data-flow.md), and the module graph in
> [`docs/arc/modules.md`](docs/arc/modules.md). **This file is instructions for an agent, not a
> description of the system.** A document that does both grows forever, because every version adds to
> the architecture: that is exactly how the `## The path` section this version deleted came to be a
> quarter of the file. When a paragraph here starts explaining how something works rather than what to
> do about it, it belongs in `docs/arc/`.

**The method this repo runs is OpenSpec SDD** — work is defined as a change before it is built, the
living spec is test-backed, and a release folds one into the other. `## How a change is cut here`,
below, is the in-tree statement of that contract; everything else here is a rule this repository holds
in particular.

Hard constraints that shape the code here:

- **Identity preservation is the product.** A beautiful anime image of someone else is a failed run.
- **The entry point imports no third-party package at module scope** — the ComfyUI transport is
  `urllib`, and nothing on `python -m isekai`'s import graph may need a wheel. Face detection runs
  *in the image*, never as a runtime dep. **This is narrower than the *"the runtime is stdlib-only"*
  rule it replaces, and deliberately so**: `dependencies = []` was retired in v0.22.3 because the
  local tagger runs on every `caption` and `uv sync` was stripping it, so the tagger's stack and the
  review surface's server are declared dependencies now. What is forbidden is a wheel *on the import
  graph* — reach one from inside the verb that needs it, and the `-S` guard in
  `tests/test_pipeline_cli.py` is the only thing that catches a violation.
- **A selectable implementation is a measured one.** Nothing enters the registry on the strength of
  being written; it enters on a measurement against the bar its capability states, and it leaves only
  by the version that retires it. **This replaces the older rule *"there is one path"*, and does not
  restore it** — counting permits an unmeasured single path, which is the failure that rule was
  written against. Measure it or do not offer it.

> **These are standing instructions, not a workflow.** What you should *do on this task* comes from the
> prompt you were given; if your prompt conflicts with this file, **the prompt wins.** Don't infer a
> workflow from this file alone.

---

## The quality gate — this repo's six commands

**These** are the commands this repo declares, in `.minions/minions.toml`'s `gate` array, in order:

- `uv sync --locked` — environment, from the tracked lock; not a quality axis, hence first
- `uv run ruff format --check .` — format, in check mode (a rewrite is not the check)
- `uv run ruff check .` — lint
- `uv run ty check` — strict types
- `bash scripts/typecheck_ui.sh` — strict types, in the browser: `vue-tsc --noEmit` over `ui/`,
  wrapped so a missing `ui/node_modules/` refuses by name rather than exiting 127
- `uv run pytest` — tests

**The array is the one that is run, and there are three copies of it, not four.** `Makefile`'s `gate`
target mirrors it and `README.md` lists it; CI (`.github/workflows/ci.yml`) **invokes that mirror** —
`run: make gate` — rather than keeping a third copy, because its own steps had already drifted.
Change the array, change the other two in the same commit.

All six green, or the phase is not done. **Never weaken the gate to pass** — see the guardrails.

Beyond the array, **image-as-code phases also run `bash -n` on shell scripts and `docker build --check`**.
That is a convention for those phases, not an entry in the array; adding it to one means adding it to the
`Makefile` in the same commit.

**The suite runs offline and deterministically.** The ComfyUI transport is faked behind a `ComfyTransport`
Protocol (`FakeComfyClient`), the suite reads the shipped graph itself rather than a fixture copy of it,
and seed drawing takes an injected `random.Random`. No test hits a GPU or the network — which is why every scenario declares `Layers: unit`
and none declares `e2e`. Diffusion quality and identity fidelity are verified **live on a pod, by eye**,
never mocked and never asserted.

---

## Engineering conventions

The active change's **`design.md`** is authoritative, with this file behind it — read it. It *is* the
decision record: the reasoning that settled a decision, and the measurement behind it, are written there
and nowhere else. In brief, the load-bearing seams are:

- **A parameter is a seam only if something else is actually passed through it.** That is why `client` is a
  parameter of `generate.render` — `FakeComfyClient` is what makes the whole suite offline — and why `rng`
  is one, while the reader is a seam because it has a real double. **Stage ② has no seam at all any
  more**, and that is the rule read the other way: v0.21 replaced two sorter implementations behind a
  Protocol with a dictionary lookup, so there was nothing left to pass through the parameter. A
  one-entry registry is a dispatch mechanism with nothing to dispatch.
- **The flow manifest declares; nothing computes.** `flows/<id>/flow.json` names every node the render
  path edits, by role — `flow.node("sampler")`, `flow.node("photo")` — so no node is ever located by
  class at runtime. That is what lets a broken flow be caught by the suite rather than by a boot, and
  it is not optional: `summon-anime-wai` has two `KSampler` nodes and two `ImageScale` nodes, so a
  class lookup is ambiguous against the graph that actually ships.
- **A network boundary lives in `boundary/`, and nothing else opens one.** `ComfyTransport`
  (`comfy_types.py`, implemented in `comfy_client.py`) reaches the rented GPU; `ollama.py` reaches the
  local model and is the only way out of the *pipeline* to one. `HOST` there is a module constant with
  no flag and no environment variable behind it. A second reader is a second adapter, in review — there
  is no registry to add an entry to.
  **The failure shape the stages share lives in `foundation/run.py`, not at a boundary** —
  `StageFailure`, `refusal_for`, `instructions_record`, `constant_record`. It cannot live in
  `refusal.py`: that module imports nothing by design, the class needs `Kind`, and `run.py` already
  imports `refusal.py`, so the move would be a cycle.
- **The run owns the layout, not the stages**, and **no stage imports another.** The stage directory
  names live in `isekai/foundation/run.py` and the `Schema` type in `isekai/foundation/flow.py`. The
  layout is **input above, flow below**, so adding a flow adds one subtree and no flow can read
  another's artifacts; the directories themselves are drawn in `docs/arc/data-flow.md`.
- **An Option-modified keybinding matches `event.code` and calls `preventDefault()`, because Option
  is a character-producing modifier on macOS.** Not a layout rule and not hygiene: on plain US ABC,
  `Option+Space` emits U+00A0 and `Option+F` emits `ƒ`, so a handler matching `event.key` inserts an
  invisible non-breaking space into a tag field — the silent dead end the cheatsheet exists to
  remove. `preventDefault()` is load-bearing twice, because Space is also the **native activation
  key** of a focused `<button>` and this app focuses one on mount (`ReviewApp.vue`'s
  `.rail__card--current`). Every binding in the surface satisfies this today; a new one that matches
  `event.key` alone is the regression to look for.

**Tests are bound to the spec.** Every test carries `@pytest.mark.spec("<key>")` naming the scenario it
proves, or `@pytest.mark.spec_exempt("<reason>")` if it is genuinely structural. Both are registered in
`[tool.pytest.ini_options] markers` — registration is load-bearing, because pytest silently ignores an
unregistered marker, so an unregistered one would bind nothing while looking exactly like a binding.
Behaviour gets a scenario first; a new test gets a binding.

---

## How a change is cut here

Work is defined before it is built, as a change under `openspec/changes/<id>/`. A change is the unit of
work **and** the unit of release.

A change is **four artifacts, always all four**: `proposal.md` · `specs/` · `design.md` · `tasks.md`,
plus the tracked `.openspec.yaml` where one is needed. A change may carry a fifth of its own —
`0023-backlog-paydown` shipped `no-spec-delta.md` beside the four — but never fewer than the four.

1. **Settle the decisions first.** A change is cut from decisions argued against a person, not from a first
   draft. The verdict — `feasible` / `feasible-with-caveats` / `needs-precursor` /
   `infeasible-as-specified` — is recorded in the change's `design.md`.
2. **Scaffold by hand** — `openspec new change <name>` *does* exist in 1.11.0, and this repo does not
   use it: it writes into the root `openspec/config.yaml` declares, this repo keeps no such file, and
   the id rule below is not one the CLI knows. The directory is created directly.
   The id is `<digits>-<lowercase-slug>`, and version → id is `(major × 100) + minor`,
   zero-padded: `v0.7` → `0007`, `v0.10` → `0010`, which stays monotonic past 1.0. **The formula has
   no patch case**, and a patch release still needs an id: `v0.22.1` shipped as `0023`, the next
   free number rather than anything the formula produces. Take the next free number for a patch, and
   keep it monotonic. (`0001-mf-standard` predates all of this and keeps its id — an id is never
   renamed once commits carry it as a trailer.)
3. **Author** each artifact against `openspec instructions <proposal|specs|design|tasks> --change
   <NNNN-slug>`, one at a time, fetching each immediately before writing it. `proposal.md` additionally opens with `version: vX.Y`
   frontmatter — **the CLI neither emits nor checks that key; it is on the author.**
4. **A change that changes no requirement** declares the absence rather than inventing one: `skip_specs:
   true` in the change's tracked `.openspec.yaml`, **plus** `specs/.gitkeep`. Both, not either —
   `0023-backlog-paydown` carries the pair. Never write a requirement solely to satisfy the validator.
5. **Finish on a green check** — `openspec validate <NNNN-slug> --strict`.

**Progress lives in `tasks.md`**, in its `## Progress` checklist, and **the current phase is the first
unchecked box**. A phase is advanced by a commit **and** a ticked box, in that phase's own commit — either
alone is not an advance.

**The living spec** is `openspec/specs/<capability>/spec.md`, each capability a contract with one
owner: `caption`, `cli`, `comfy-transport`, `evaluation`, `field-map`, `image-generation`,
`model-provisioning`, `review`, `run-directory`, `sheet`, `tagging`, `ui`. **List
`openspec/specs/*/` rather than trusting that line** — when it carried a *count* instead of the names,
that count was wrong in three consecutive versions.
A capability enters and leaves the living spec only when a change is **archived**, which is
`mf-release`'s act and never the builder's — so what is on disk is never what a pending change
implies. Every `#### Scenario:` carries a `- **Key:**` and a `- **Layers:**` bullet, and the key is
`<capability>:<requirement-slug>:<scenario-slug>`, so a key locates its own file. On release the delta
is folded in and the change moves to `openspec/changes/archive/`; archived changes are never deleted.

**The version line is one line in four places** — `proposal.md`'s `version:`, `CHANGELOG.md`'s
`## [X.Y.Z]`, `pyproject.toml`'s `version`, and the annotated tag `vX.Y.Z`. A minor release spells that
`vX.Y` / `## [X.Y.0]` / `vX.Y.0`; a patch release spells it `vX.Y.Z` throughout, as `0.22.1` did. All
four agree or the release halts. One branch per version. `CHANGELOG.md` follows Keep a Changelog + SemVer, with an entry appended
**per phase** under `## [Unreleased]` and cut at release.

Every commit is a Conventional Commit, **one phase = one commit**, staged **by name** and never with
`git add -A`. Each carries a `Change: <change-id>` git trailer, in the trailer block at the end of the
message and **contiguous** with any `Co-Authored-By:` line — a blank line between them silently breaks the
block.

The tooling is **operator tooling, recorded and not pinned**: `@fission-ai/openspec@1.11.0`, resolved on
`PATH`. It is deliberately **not** in the gate array — nothing in CI runs it, so a moving version can never
turn CI red. There is **no spec↔test binding checker in this repo**, so `spec` / `spec_exempt` bindings are
maintained by hand and reviewed, not enforced; that gap is known and open.

---

## Layout — where things live here

**The file-by-file inventory is not here.** Each group directory carries its own `README.md` naming its
files and who imports them, `isekai/README.md` sits over them, and the graph is drawn once in
`docs/arc/modules.md`. Duplicating any of that here is how this section grew the last time.

- **`isekai/__main__.py`** is the only entry point — the path `runpy` resolves for
  `python -m isekai <verb>`, and a shim over `interface/cli.py`. **A group's `__init__.py` holds a
  docstring and no code**, so a group never becomes a place two modules reach each other through.
  `interface/ui/__init__.py` is the one exception and is not a group: it is a subpackage with a front
  door, and `serve()` is that door.
- **`flows/<id>/` is frozen, flat, and its files are named rather than counted**: `flow.json`,
  `graph.json`, `schema.json`, `caption.briefing.md`. The manifest names none of its siblings — a key
  that can only ever hold one value is not a declaration — and they sit *directly* in the directory,
  because the digest that freezes a flow covers regular files only, so a nested layout would leave the
  schema and the briefing outside the freeze with the gate green. **The rule does not tally them, and
  that is deliberate**: a numeral is the part of a rule that goes stale, and `tests/test_flow.py`
  asserts `len(SIBLINGS)` so a sibling cannot be added silently.
  **A flow is pinned by equality, so nothing in one changes silently** — and it shares nothing with
  another flow. Adding one costs a line in `tests/test_flow.py`'s `PINNED` and a `CHANGELOG.md` entry
  carrying its digest, which is the designed price of the freeze rather than a defect. **The freeze forbids a silent change, not a change**: a
  *divergence* still costs a new identifier, because two flows are only comparable over one cohort if
  an identifier means one configuration, so a variant, another base or a second generation is a new
  flow. Only an abandoned configuration may be re-pinned, and a re-pin owes a statement of what moved
  in `CHANGELOG.md`, carrying the new digest — a test fails on any pinned digest no entry carries.
  The comment above `PINNED` states the rule, never its history.
  **A flow's identifier is `<verb>-<style>-<base>`**, with `-v2` appended only for a second generation
  of the same triple. The base is in the name because other bases were candidates and `summon-anime`
  could not tell two of them apart; the rule exists because its absence produced `summon-open-v1`, a
  name describing the *arm* rather than the flow.
- **A derived file must be byte-identical on a re-run.** `scripts/models.json`, `eval_models.json` and
  `field_map.json` are each some script's output, and re-running that script must leave the file
  unchanged — which is what makes the checked-in copy evidence rather than decoration. For
  `derive_field_map.py` that holds because every input it reads is tracked or pinned: the operator's
  own filings live in a constant in the script, and the gitignored runs they came from are read by
  `--refresh` alone, which prints a drift and writes nothing. `eval_licences.md` records each
  evaluator artifact's licence with the URL and the date it was read; a new artifact owes an entry.
- **`openspec/`** — the living specs and the changes. Authoritative for what is being built and how far
  along it is.
- **`.minions/`** — run artefacts, **gitignored**; `minions.toml`, the gate command list, is the one
  tracked file in it. `git check-ignore` reports the *directory* as not ignored precisely because of that
  one file — always check a file path.
- **`.data/` holds everything a run produces or consumes, and is gitignored.** The reason is not
  tidiness. A run directory holds a *copy of the photograph* — that is what makes a run reconstructable
  from disk — so it contains personal photographs **by construction**. Under a top-level `runs/` the
  standing rule that no personal photograph is committed would depend on one `.gitignore` line staying
  correct forever; under an ignored root that rule is structurally true instead, because **nothing a
  run produces is written outside it**.
- **The ignored roots are named rather than counted, and the boundary is named so the rule does not
  drift into meaning "everything untracked".** Each fails differently, and what it costs to lose is
  the whole of why it sits where it does:

  | root | what it is | losing it costs |
  |---|---|---|
  | `.data/` | captured or generated by a run | **the loss of work** — nothing regenerates it |
  | `.inputs/` | source photographs an operator put there by hand | **the loss of work**, and it holds a person's likeness exactly as `.data/` does — which is why `.gitignore` calls that line load-bearing |
  | `models/` | fetched from a pinned, checksummed manifest — including `models/wd14/`, the tag list **and** the graph it is the output layer of | a re-download that is byte-identical by construction |
  | `ui/dist/` | built from tracked source by `vite build` | a deterministic rebuild, which `isekai ui` does for you |
  | `ui/node_modules/` | fetched from npm | an `npm install`, which nothing does for you — it pulls arbitrary third-party packages |

  **Only the first two are work.** `.inputs/` is outside `.data/` because a photograph an operator
  supplies is an input rather than something a run generated. The rest are derivable, which is why
  none of them lives under `.data/`: that root's failure mode is loss of work and `rm -rf .data` is
  an ordinary cleanup, so a rebuildable bundle in there would muddle the boundary this rule exists to
  keep sharp.
- **Everything a run reads or writes is inside the repository.** No path outside the repo is resolved by
  anything tracked here. Research notes and the running log live in the operator's own notebook; nothing
  in this repo reaches into it, and its location is not recorded here.

---

## Rules the render path is under

**These are the ones an agent can break.** What the pipeline *is* — the verbs, what each stage reads
and writes, the run layout, the identity mechanisms and their dials — is `docs/arc/data-flow.md`'s,
and is not restated here.

- **Only an approved artifact is ever rendered.** The prompts are assembled per run from a sheet a
  human corrected, and that correction is the single largest measured gain in this pipeline. A render
  from an unapproved sheet is not a shortcut, it is a different product.
- **Nothing locates a node by class**, and the manifest is the only thing that names one — see the
  seam under `## Engineering conventions`.
- **Assembly happens before any endpoint is acquired**, for the whole batch, so a malformed sheet
  costs nothing rather than a boot. Do not move work across that line.
- **Refuse rather than default, and refuse the input rather than the batch.** A photograph whose
  header cannot be read refuses *that photograph*; a dimension no node here can derive is computed in
  `isekai/shared/image.py` and written into the node the manifest names, never guessed at by a node.
- **Stage ① is one verb.** `caption` writes prose, the local tag list and the hosted tag list in a
  single invocation, in that order, and there is no `isekai tags`. The ordering is the failure
  isolation and is not free to change — `docs/arc/data-flow.md` says why.
- **`review` and `approve` stay fully working verbs**, deprecated as *guidance* and never as code.
  Deleting the hand path would make stage ③ a single point of failure for the whole pipeline.
- **Ollama and node are system dependencies, and both refuse rather than assuming.** Ollama is needed
  by stage ① of every flow — the operator installs it and creates the model by hand,
  `ollama create joycaption-beta-one-q4k -f scripts/joycaption.Modelfile`. node is needed by
  `isekai ui` alone, to build the bundle. A missing one names what installs it; Ollama's refusal is
  applied to a **port and a model name** rather than to a `PATH` entry, which is the shape a hosted
  model needs and a binary check cannot give. Neither is a Python dependency — `uv sync` cannot
  install either, which is why each refusal names the command that does. **`[eval]` is the only
  optional extra left**, and CI does not install it; everything a run needs is declared, so no verb
  is behind an `--extra` flag and gate command one can no longer strip one.


---

## Guardrails (invariants — hold for every role)

- **Never commit a secret, or a *real* absolute path from the machine the run is on** — the RunPod API key,
  the volume id, **a pod id**, the operator's home, or this repository's own root, transcribed out of a run
  artefact or a tool's output into tracked prose. `.runpod_pod_id` is gitignored for that reason; the three
  pod ids already in `CHANGELOG.md` stay, because that file is append-only history and this rule is what
  stops a fourth being added. `.env` is gitignored and holds all of it; `.env.example` declares shape
  only. A path a fixture *constructs* is not the target of this rule; a rendered one, carrying a real
  username, is.
- **Deps minimal + human-gated.** The declared list is short and every entry is on the path of a verb
  a run actually takes. Any new dependency — argue for it and **wait for approval** before installing.
  pytest / ruff / ty stay dev-only. **A new one is an import-graph question as well as a supply-chain
  one**: reach it from inside the verb that needs it, or the `-S` guard fails.
- **Never weaken the gate to pass.** A deleted or skipped test, a blanket suppression, a loosened config —
  each is a *plan* problem, not a coding shortcut. **Halt and say so.**
- **State lives on disk.** Reconstruct "where are we" from the active change's `tasks.md` + git — never
  from memory.
- **Some phases spend real money**, and the active change's `tasks.md` marks them (⚠️ GPU). The protocol
  names four things, because a rule that leaves any of them implicit is not a rule:
  1. **Who creates the pod** — `infra/up.sh`, and nothing else. Announce before you run it.
  2. **Who tears it down** — `infra/down.sh`. **Teardown is the act**: it is the call that stops the
     billing, and it belongs to the same session that created the pod.
  3. **Who confirms** — the RunPod MCP, by checking the pod is gone. **Confirmation is not the act.** A
     rule that only names the check has not said what stops the billing, and an unconfirmed teardown is
     not one you may report as done. Record what the MCP returned.
  4. **What happens when the MCP is unreachable** — it must be authorized from an *interactive* session,
     so it can be disconnected exactly when this rule is read. Then the **explicit human "go" is back,
     unchanged**, and holds for the whole session: announce, wait for the "go", spend, tear down, report.

  **The ceiling is 45 minutes and ~$0.30 for a single pod session** — numbers, not "promptly", so a human
  can hold you to it. Exceeding it is a halt, not a judgement call. And whichever route applies, the
  authority to spend comes from the **phase**, never from the agent: **a pod goes up only for a phase
  `tasks.md` marks metered.**
- **GPU renders live on the pod's ephemeral disk**; only the models volume persists. Download before
  teardown or the output is gone.
- **The Blackwell (sm_120) pod needs cu128 PyTorch** — cu124 gives "no kernel image". It is pinned in the
  image; keep it.
