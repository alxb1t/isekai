# isekai — operating instructions for an agent

A self-hosted, headless pipeline: **photo of a person → anime image of that same person**, using open
models on an on-demand RunPod GPU running our own ComfyUI image. It exists to learn — and to show — how
open image models are run end to end, from container to rented GPU to CLI. Flows —
`summon-anime-wai` from a photograph, `conjure-anime-wai` from a corrected sheet alone,
`control-anime-wai` as `summon` with its face dials at zero, `summon-flat-anime-wai` as `summon` in a flat,
lined look — on a WAI-illustrious-SDXL v17.0 base, driven by staged verbs an operator runs one at a time:
`tag` and `caption` → `sheet` → `review`/`approve` → `generate`, with `show` reading a run and `ui` serving the
library of collections — each collection's hub, stage ③, its render and its images — in a browser. Everything before `generate` is free and local; only the render costs money.

> **That paragraph is the ceiling, and the ceiling is the point.** A fuller account — the verbs, what
> each stage reads and writes, the run layout, the identity mechanisms and their dials — belongs in
> [`docs/data-flow.md`](docs/data-flow.md), and the module graph in [`docs/modules.md`](docs/modules.md).
> **This file is instructions for an agent, not a description of the system.** A document that does
> both grows forever, because every version adds to the architecture: that is exactly how the
> `## The path` section a past version deleted came to be a quarter of the file. When a paragraph here
> starts explaining how something works rather than what to do about it, it belongs in `docs/`.

**The method this repo runs is OpenSpec SDD** — work is defined as a change before it is built, the
living spec is test-backed, and a release folds one into the other.
[`CONTRIBUTING.md`](CONTRIBUTING.md) is the in-tree statement of that contract; everything else here is a
rule this repository holds in particular.

**The gate is `make gate`**, run from the repository root.

**Before work, read [the coding standards](CODING_STANDARDS.md) and [how a change lands](CONTRIBUTING.md): mandatory
shared context.** **Before designing, building or reviewing, also read [the decisions in force](docs/decisions.md),
[the architecture](ARCHITECTURE.md) and [the threat model](THREAT_MODEL.md).**

**Identity preservation is `summon`'s product.** An anime image of someone else is a failed `summon`
run. `conjure` takes no photograph and makes no identity claim
([docs D10](docs/decisions.md#d10--the-face-and-the-pose-are-carried-by-the-graph)).

**Read [`docs/principles.md`](docs/principles.md) before your first edit** — the rules every component
follows. A tool that expands `@` imports loads it through the line below; any other opens the file.

@docs/principles.md

> **These are standing instructions, not a workflow.** What you should *do on this task* comes from the
> prompt you were given; if your prompt conflicts with this file, **the prompt wins.** Don't infer a
> workflow from this file alone.

---

## The run's lines

- **Worktrees:** `../` — each version's worktree sits beside the primary, named by its change id.
- **Workspace setup:** `make setup` — restores what a fresh worktree lacks.
- **Ship network:** none — the given package hosts are enough, because the setup fills the worktree first.
- **Ship loopback:** yes — the browser tests and the server tests serve on `127.0.0.1`.

---

## Layout — where things live here

**The file-by-file inventory is not here.** Each group directory carries its own `README.md` naming its
files and who imports them, `isekai/README.md` sits over them, and the graph is drawn once in
`docs/modules.md`. Duplicating any of that here is how this section grew the last time.

- **`flows/<id>/`** — what a flow holds and how it is named are
  [docs D14](docs/decisions.md#d14--a-flow-is-one-flat-directory) and
  [docs D15](docs/decisions.md#d15--a-flow-is-named-for-what-it-is). **Adding or re-pinning a flow**
  costs a line in `tests/test_flow.py`'s `PINNED` and a `CHANGELOG.md` entry carrying its digest —
  the designed price of the freeze. A re-pin states what moved, and a test fails on any pinned digest
  no entry carries. The comment above `PINNED` states the rule, never its history.
- **`AGENTS.md` is the one instruction file, for every coding agent** — Claude Code, Codex, Qwen Code.
  A rule for agents goes here; the repository keeps no `CLAUDE.md`, `QWEN.md` or other per-tool copy,
  because Claude Code reads a `CLAUDE.md` *instead of* this file, and a second copy drifts.
- **`openspec/`** — the living specs and the changes. Authoritative for what is being built and how far
  along it is.
- **`.minions/`** — MinionsFactory's run artefacts, gitignored whole.
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
  | `ui/node_modules/` | fetched from npm | a `make setup`, which nothing runs for you — it pulls arbitrary third-party packages |

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

The rules every component follows are [`docs/principles.md`](docs/principles.md)'s, named above; the
choices in force are [`docs/decisions.md`](docs/decisions.md)'s. **Read both before changing anything
they decide.**

---

## Guardrails (invariants — hold for every role)

- **Never commit a secret, or a *real* absolute path from the machine the run is on** — the RunPod API key,
  **a pod id**, the operator's home, or this repository's own root, transcribed out of a run
  artefact or a tool's output into tracked prose. `.gpunit/`, where gpunit keeps a session's pod id and
  keys, is gitignored for that reason; no pod id is in `CHANGELOG.md`, and this rule keeps it so.
  `.env` is gitignored and holds all of it; `.env.example` declares shape only. A path a fixture
  *constructs* is not the target of this rule; a rendered one, carrying a real username, is.
- **Deps minimal + human-gated.** The declared list is short and every entry is on the path of a verb
  a run actually takes. Any new dependency — argue for it and **wait for approval** before installing.
  pytest / ruff / ty stay dev-only. **A new one is an import-graph question as well as a supply-chain
  one**: reach it from inside the verb that needs it, or the `-S` guard in `tests/test_pipeline_cli.py`
  fails.
- **Never weaken the gate to pass.** A deleted or skipped test, a blanket suppression, a loosened config —
  each is a *plan* problem, not a coding shortcut. **Halt and say so.**
- **State lives on disk.** Reconstruct "where are we" from the active change's `tasks.md` + git — never
  from memory.
- **Some phases spend real money**, and the active change's `tasks.md` marks them (⚠️ GPU). The protocol
  names four things, because a rule that leaves any of them implicit is not a rule:
  1. **Who creates the pod** — `uv run python -m isekai render`, through gpunit, and nothing else; the app's
     Render runs that verb as its child. Announce before you run it. `uv run --env-file .env gpunit volume up --yes` makes or extends the window's volume,
     announced with the render.
  2. **Who tears it down** — the same `isekai render`: its gpunit session deletes the pod on every exit and
     leaves no `gpunit-isekai` pod listed; the pod also stops itself at its session's limit, never past
     `gpunit.toml`'s `ceiling`. When the
     session reports a failed teardown, `uv run --env-file .env gpunit down` is the act — gpunit reads no
     `.env`. **Teardown is the act**: it is the call that stops the billing, and it belongs to the same
     session that created the pod. The volume's is `uv run --env-file .env gpunit volume down`, on the
     operator's word, and nothing else: the 4-hour `volume_ceiling` is not a teardown — past it, the volume
     bills until gpunit's next session, `up`, `status`, `down`, `volume up` or `volume down` sweeps it, if
     that delete succeeds.
  3. **Who confirms** — the RunPod MCP, by checking no `gpunit-isekai` pod is left. **Confirmation is not
     the act.** A rule that only names the check has not said what stops the billing, and an unconfirmed
     teardown is not one you may report as done. Record what the MCP returned. When the MCP confirms gone a
     pod whose `gpunit down` did not delete it, delete `.gpunit/pod` and `.gpunit/pending`: gpunit keeps
     its record until the pod is confirmed gone, and refuses the next session beside it. A window is closed
     only when `list-network-volumes` shows no `gpunit-isekai` volume, whatever `volume down` printed.
  4. **What happens when the MCP is unreachable** — it must be authorized from an *interactive* session,
     so it can be disconnected exactly when this rule is read. Then the **explicit human "go" is back,
     unchanged**, and holds for the whole session: announce, wait for the "go", spend, tear down, report.

  **A session's limit and price are its quote's, at most `gpunit.toml`'s `ceiling` and `max_hourly`**, and
  4 hours and ~$0.02 for the window's volume — numbers, not "promptly", so a human can hold you to it.
  `isekai render` prints `session limit <seconds>s` as it opens, and the app's Render dialog quotes both.
  Exceeding the quote is a halt, not a judgement call. And whichever route applies, the authority to spend
  comes from a **phase `tasks.md` marks metered, or from the operator's explicit go in the session, which
  quotes the limit and the price** — never from the agent.
- **GPU renders live in the pod's memory**; only the models volume persists, for its window. Download
  before teardown or the output is gone.
- **The Blackwell (sm_120) pod needs cu128 PyTorch** — cu124 gives "no kernel image". It is pinned in the
  image; keep it.
