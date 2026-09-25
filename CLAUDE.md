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
> [`docs/data-flow.md`](docs/data-flow.md), and the module graph in [`docs/modules.md`](docs/modules.md).
> **This file is instructions for an agent, not a description of the system.** A document that does
> both grows forever, because every version adds to the architecture: that is exactly how the
> `## The path` section this version deleted came to be a quarter of the file. When a paragraph here
> starts explaining how something works rather than what to do about it, it belongs in `docs/`.

**The method this repo runs is OpenSpec SDD** — work is defined as a change before it is built, the
living spec is test-backed, and a release folds one into the other. `## How a change is cut here`,
below, is the in-tree statement of that contract; everything else here is a rule this repository holds
in particular.

**Identity preservation is `summon`'s product.** An anime image of someone else is a failed `summon`
run. `conjure` takes no photograph and makes no identity claim
([docs D10](docs/decisions.md#d10--the-face-and-the-pose-are-carried-by-the-graph)).

**The principles are imported below, so every session has them.** The choices in force are
[`docs/decisions.md`](docs/decisions.md)'s — read it before changing anything it decides.

@docs/principles.md

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

The active change's **`design.md`** is authoritative for that change, with this file behind it — read
it. **`docs/decisions.md` records the decisions in force; a change's `design.md` records why one was
taken**, and is frozen when the change is archived.

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
   The id is `<digits>-<lowercase-slug>`, and the digits are **the next free number**, zero-padded
   to four — higher than every id under `openspec/changes/` and its `archive/`, for a minor and a
   patch alike. (`0001-mf-standard` predates all of this and keeps its id — an id is never renamed
   once commits carry it as a trailer.)
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

**A minor delivers one feature; a patch delivers none**, and meets every one of these — work that
cannot is not a patch:

- no format version moves — `MANIFEST_VERSION`, the artifact envelope's `SCHEMA_VERSION`;
- every behaviour fix is required by an existing requirement: a scenario may be added under one, a
  requirement may not;
- nothing deprecates a verb or a flag;
- nothing changes the product — a sheet's fields, the prompt, the image — for the same inputs and
  configuration.

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
`docs/modules.md`. Duplicating any of that here is how this section grew the last time.

- **`flows/<id>/`** — what a flow holds and how it is named are
  [docs D14](docs/decisions.md#d14--a-flow-is-one-flat-directory) and
  [docs D15](docs/decisions.md#d15--a-flow-is-named-for-what-it-is); why it is frozen is the principle
  *Everything that shapes an output is pinned*. **Adding or re-pinning a flow** costs a line in `tests/test_flow.py`'s `PINNED` and a `CHANGELOG.md`
  entry carrying its digest — the designed price of the freeze. A re-pin states what moved; a test
  fails on any pinned digest no entry carries. The comment above `PINNED` states the rule, never its
  history.
- **A derived file** is the principle *Configuration is declared*'s. `eval_licences.md` records each
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
- **The repository-path anchors resolve inside the repository** — `tests/test_package_paths.py` pins
  each one. A runs root defaults to `.data/runs` and may sit outside the repository; inside it, it
  must sit under `.data/` ([docs D18](docs/decisions.md#d18--runs-stay-out-of-what-git-tracks)).
- **The repository holds no pointer to the operator's notebook** — no path, no variable naming it.
  Research notes and the running log live there; the notebook reads the repository, never the
  reverse. **Review holds this; no test does.**
- **A demo subject is a synthetic portrait**, never a real person's photograph.

---

## The architecture — read before changing it

The rules every component follows are [`docs/principles.md`](docs/principles.md)'s, imported above; the
choices in force are [`docs/decisions.md`](docs/decisions.md)'s. **Read both before changing anything
they decide.** What the code is today — the module graph, the verbs, the run layout — is
[`docs/modules.md`](docs/modules.md)'s and [`docs/data-flow.md`](docs/data-flow.md)'s.

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
