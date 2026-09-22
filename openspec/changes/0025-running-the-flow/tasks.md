# Tasks — 0025 running the flow

## Progress

- [x] 1 — The negative prompt becomes quality-only
- [x] 2 — `tagging` and `ui` become required dependencies
- [x] 3 — `## Quickstart` becomes the guide to running a flow
- [x] 4 — ⚠️ **HUMAN · METERED** — the acceptance, both flows, one pod

## The per-phase ritual

1. **Run each sub-task's stated verification — run it, never summarize it. Paste real output.**
2. **Gate green before the commit** — `make gate`, the commands in `.minions/minions.toml`'s `gate` array,
   in order. **Never weaken the gate to pass**; halt and say so.
3. A `CHANGELOG.md` entry under `## [Unreleased]`, appended in that phase's own commit.
4. The phase's box ticked in `## Progress` above, in that phase's own commit.
5. **One commit per phase**, staged **by name**, carrying `Change: 0025-running-the-flow` contiguous with
   the `Co-Authored-By:` line.
6. **Every new test carries a binding** — `@pytest.mark.spec("<key>")`, or
   `@pytest.mark.spec_exempt("<reason>")` only where genuinely structural.

**`design.md` is authoritative.** Where the tree disagrees with a decision it settled, that is a halt and
a finding, never a quiet divergence.

**Line numbers below were resolved against `main` `7fb3d0b`, after `v0.22.2` merged.** Re-resolve by
quoted text rather than trusting a number from an earlier phase.

**⛔ Metered cost is ZERO in phases 1, 2 and 3.** A pod in any of them is a halt. **Phase 4 is the only
metered phase in this entire stabilization** — `v0.22.1` and `v0.22.2` both cost nothing.

> ⚠️ **HAND THIS TO `mf-release` BEFORE IT FOLDS.** The delta carries **one MODIFIED requirement** in
> `image-generation`, and it **renames its heading** — *"A flow is immutable; changing any file in it
> creates a new flow"* becomes *"A flow is pinned by equality; changing any file in it is an explicit
> act"*. A title-matching fold finds nothing and appends, which is the failure `v0.14 review/R11`
> recorded. **Match on the old title; replace, do not append.** It also adds one scenario beside the
> existing one, which must be carried through rather than replaced.

---

## 1 — The negative prompt becomes quality-only

**This phase's commit message is the operator's own sentence and nothing else:
*improvements to the negative prompt*.** The dependency work and the guide are phases 2 and 3 and must not
appear in it.

- [ ] 1.1 **Remove `censor, nsfw` from both flows' `flow.json` negative.** The fragment is at
  `flows/summon-anime-wai/flow.json:16` and `flows/conjure-anime-wai/flow.json:15`, both reading:
  ```
  "bad quality, worst quality, sketch, censor, nsfw, lens flare, light particles, dust"
  ```
  ✅ `lens flare, light particles, dust` is **already present in both** — the ask was half done.
  **Change nothing else in the string.**

- [ ] 1.2 **Set `graph.json`'s negative node text to an empty string** in both flows —
  `flows/summon-anime-wai/graph.json:35`, `flows/conjure-anime-wai/graph.json:26`, both currently
  `"bad quality, worst quality, worst detail, sketch, censor, nsfw"`.
  **A deletion, not a sync** (`design.md` D1). That string is overwritten on every render by
  `generate.py:336`'s `patch("negative", …)`, and it has already drifted from `flow.json`'s — `worst
  detail` appears only here. **Verify the overwrite before editing**: read `generate.py:336` and the
  prompt artifact's `negative` field, and confirm the graph text never reaches a render.

- [ ] 1.3 **Re-pin both digests.** `tests/test_flow.py`'s `PINNED` currently holds
  `conjure-anime-wai: 1e991c2be729…` and `summon-anime-wai: 8ddd4016dadd…`. Recompute with
  `manifest_digest`; **do not hand-transcribe**.

- [ ] 1.4 ⚠️ **Amend the comment above `PINNED`.** It currently says the one prior exception gains no
  *"unless"* clause. **This is the second exception** (`design.md` D2) and the comment must say so, with
  the condition that survives: **a divergence still costs a new identifier; only an abandoned
  configuration may be re-pinned.** *Do not soften the failure message itself.*

- [ ] 1.5 **Verify no other flow file moved** — `git diff --stat -- flows/` shows exactly two files,
  `flow.json` and `graph.json`, in each of two directories.

- [ ] 1.6 **Gate green. CHANGELOG. Tick 1. Commit.**

---

## 2 — `tagging` and `ui` become required dependencies

- [ ] 2.1 **Move `tagging` and `ui` out of `[project.optional-dependencies]` into `dependencies`**, pinned
  exactly at what `uv.lock` resolves at `7fb3d0b`:
  ```
  onnxruntime==1.29.0   numpy==2.5.3   Pillow==12.3.0   fastapi==0.141.1   uvicorn==0.53.0
  ```
  **`eval` stays optional** — it is the scorer, not the pipeline.

- [ ] 2.2 **Rewrite `pyproject.toml`'s comment block** at `:5-8` and around the extras. The argument it
  carries for `dependencies = []` is what this phase retires; what replaces it is the narrower claim —
  **the entry point imports no third-party package at module scope**, which is what the `-S` guard proves
  and why `isekai show` works on an unprovisioned checkout.

- [ ] 2.3 **Narrow the `-S` guard, do not delete it** (`design.md` D4).
  `tests/test_pipeline_cli.py:198` and `:205` import under `python -S`; `:214` proves the guard is not
  vacuous. With the packages installed by default, **the guard is the only thing that would catch a
  module-scope import appearing in the entry point's graph.** Keep all three; adjust what they assert.

- [ ] 2.4 ⛔ **HALT CHECK — `uv sync --locked` must now install the tagger, not remove it.** Verify:
  ```sh
  uv sync --locked && ls .venv/lib/python3.12/site-packages/ | grep -iE 'onnxruntime|numpy|PIL|fastapi'
  ```
  All four present. **If the gate still strips them, the move did not take** — halt rather than papering
  over it with a second sync.

- [ ] 2.5 **Check CI's resolution.** ⚠️ onnxruntime wheels are platform-specific; a version resolved on
  darwin/arm64 may not exist for the runner. If `uv sync --locked` goes red on CI, **that is the cause** —
  the repair is a floor in the manifest with the lock doing the pinning, never a weakened gate.

- [ ] 2.6 **Gate green. CHANGELOG. Tick 2. Commit.**

---

## 3 — `## Quickstart` becomes the guide to running a flow

- [ ] 3.1 **Five sentences are false the moment phase 2 lands**, and this phase is where they are repaid:

  | at | says |
  |---|---|
  | `README.md:110` | the local tag list *"needs `uv sync --extra tagging`"* |
  | `README.md:164` | the surface *"needs the optional extra: `uv sync --extra ui`"* |
  | `README.md:166` | *"additionally needs `uv sync --extra tagging`"* |
  | `CLAUDE.md:275` | *"the optional extras — `[ui]`, `[eval]`, `tagging` — are not installed by CI, so `dependencies = []` and the stdlib-only runtime rule both hold"* |
  | `docs/arc/modules.md:75` | *"**The runtime is stdlib-only.** Nothing on `python -m isekai`'s import graph may need a wheel"* — **written by `v0.22.2` three commits ago** |

  ⚠️ `docs/arc/modules.md`'s surrounding paragraph distinguishes *how* each extra is reached. That
  distinction survives and is worth keeping; only the **stdlib-only** claim and the extras list change.

- [ ] 3.2 **Rewrite `README.md:92-200`'s `## Quickstart` in place and rename it** (`design.md` D5).
  Commands read as a sequence; explanation moves below them or goes. ⛔ **Do not add a second guide** —
  one guide, rewritten.

- [ ] 3.3 **It covers the whole path, photo → image**, including `./infra/up.sh`, the tunnel in a second
  terminal, and `generate`.

- [ ] 3.4 ⚠️ **Mark the boundary where it stops being free so it cannot be missed.** Everything through
  `approve` is local and costs nothing. `generate` needs a pod, credentials and real money.
  `CLAUDE.md`'s spend guardrail wants that visible.

- [ ] 3.5 **Verify no count was introduced.** `v0.22.2` stripped quantities from the documents by
  decision; a rewritten guide must not reintroduce one.

- [ ] 3.6 **Gate green. CHANGELOG. Tick 3. Commit.**

---

## 4 — ⚠️ **HUMAN · METERED** — the acceptance

**A negative prompt is judged by looking at what it renders.** This is the only phase in the whole
stabilization that spends money.

- [ ] 4.1 **`make gate` — all six commands, output pasted.**

- [ ] 4.2 **A clean checkout runs `caption` with no extra flag.** The thing phase 2 exists for:
  ```sh
  rm -rf .venv && uv sync --locked && python -m isekai caption --flow summon-anime-wai <photo>
  ```

- [ ] 4.3 **Follow the rewritten guide from the top, doing only what it says**, on a fresh photograph.
  **If a step needs knowledge that is not on the page, the guide is not done.**

- [ ] 4.4 ⚠️ **One pod session, both flows, the same photographs.** Render with the new negative and
  confirm the operator's own finding: *the images are better*. **This is judged by eye and recorded as
  such** — it is the same posture this repository already takes toward diffusion quality.

- [ ] 4.5 **Record what moved.** Both flows' old and new digests, and the one string that changed. This is
  what `design.md` D2 and the modified requirement oblige a re-pinning change to leave behind.

- [ ] 4.6 **Record what was not verified.** No cohort was scored — the claim is *better by eye*, on the
  operator's own photographs, not a measured improvement on any axis. **The evaluation sub-system is
  v0.23's**, and this version does not pretend to anticipate it.

- [ ] 4.7 **`/simplify` over this change's own diff. Gate green. CHANGELOG. Tick 4. Commit.**
