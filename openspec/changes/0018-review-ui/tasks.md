# Tasks — 0018 review ui

## Progress

- [x] 1 — The nine `## Purpose` lines, before anything is folded
- [x] 2 — `security/S1`: containment decided by identity, not by text
- [x] 3 — `wiring_from()`, and the seams a ③-only caller does not need
- [x] 4 — `review.py`: `save_draft()`, `TokenBudget`, and two refusals that do not run
- [x] 5 — The server and the verb
- [ ] 6 — Vue: shell, tokens, rail, and the read-only sheet
- [ ] 7 — Vue: the autocomplete
- [ ] 8 — Vue: editing and autosave
- [ ] 9 — Vue: approve, read-only, and the refusal line
- [ ] 10 — Vue: the overlay, the loading state, the manifest
- [ ] 11 — The docs this version makes false
- [ ] 12 — The free walkthrough: the surface end to end, on data that already exists
- [ ] 13 — ⚠️ **HUMAN · METERED · GPU · HALT** — the acceptance run

## The per-phase ritual

1. **Run each sub-task's stated verification — run it, never summarize it. Paste real output.**
2. **Gate green before the commit** — `make gate`, the five commands in `.minions/minions.toml`'s `gate`
   array, in order. **Never weaken the gate to pass**; halt and say so.
3. A `CHANGELOG.md` entry under `## [Unreleased]`, appended in that phase's own commit.
4. The phase's box ticked in `## Progress` above, in that phase's own commit.
5. **One commit per phase**, staged **by name**, carrying `Change: 0018-review-ui` contiguous with the
   `Co-Authored-By:` line.
6. **Every new test carries a binding** — `@pytest.mark.spec("<key>")` naming the scenario it proves, or
   `@pytest.mark.spec_exempt("<reason>")` if it is genuinely structural. An unregistered marker binds
   nothing while looking exactly like a binding.

**Phases 1–12 are free.** Nothing in them boots a pod, calls a hosted model or spends money — phase 12
runs against a copy of existing run data, deliberately, so a defect is found before anything is rented.
**Phase 13 is the only metered one, and it halts before it starts**: the operator supplies the
photographs, confirms the spend and gives an explicit go. Do not start it on the strength of phase 12's
approval.

**node is not in CI and never will be, and `make gate` is close to vacuous on phases 6–10.** They
change no Python, so a green gate there proves only that nothing regressed — it says nothing about the
work. **Their real verification is the stated `npm run build` plus an eye check against a named PNG**,
and the eye check is a human's. Where a phase's acceptance is *by eye*, do not invent a passing check
for it: run the build, present the result, and halt for the operator exactly as the stop-conditions
require.

**Read before phase 6.** `design.md` § *Frame deltas* is a build instruction, not a footnote. The PNGs
are the reference for layout, spacing, type, colour and behaviour; the ten rows of that table are where
the build deliberately differs, and `design.md` § *Build reference* carries the component tree, the
build order, the three things that are easy to get wrong and the keyboard model.

---

## 1. The nine `## Purpose` lines, before anything is folded

> Design D9. **This phase changes no requirement and carries no delta.** It adds a heading the spec
> parser needs above prose that is already in every file. Do it first, because this change adds a
> capability and the fold rule that would create it is the same rule that broke the nine.

- [x] 1.1 Confirm the damage before touching anything. Verify:
      `openspec validate --specs --strict --no-interactive` — **`0 passed, 9 failed`**, and
      `openspec list --specs` — **`requirements 0`** on all nine.
- [x] 1.2 In each of `openspec/specs/{caption,cli,comfy-transport,evaluation,image-generation,model-provisioning,review,run-directory,sheet}/spec.md`,
      insert a blank line and `## Purpose` immediately after the `# Capability: \`<name>\`` line, leaving
      the existing paragraph, the `**Source:**` / `**Tests:**` block and `## Requirements` exactly as
      they are. **Write no prose.**
- [x] 1.3 Verify every one is now readable: `openspec validate --specs --strict --no-interactive` —
      **`9 passed, 0 failed`**.
- [x] 1.4 Verify the parser now sees the requirements it has been blind to: `openspec list --specs` —
      every capability reports a non-zero count, and `review` reports **6**.
- [x] 1.5 Verify nothing else moved: `git diff --stat` — **nine files, nine insertions of two lines
      each, no other change.**
- [x] 1.6 Verify the gate: `make gate`

## 2. `security/S1`: containment decided by identity, not by text

> Design D10, and spec delta `run-directory`. **This is a fix inside the function phase 3 extracts.**
> Do it before the extraction so the extraction never carries a broken guard, not even for one commit.

- [x] 2.1 **Reproduce it first, and paste the output.** Verify:
      ```
      uv run python -c "
      from pathlib import Path
      from isekai.interface.wiring import REPOSITORY, _check_run_root
      from isekai.foundation.refusal import Refusal
      probe = Path(str(REPOSITORY).replace('/Users/','/users/',1)) / 'runs'
      print('samefile:', Path(REPOSITORY).samefile(probe.parent))
      try: _check_run_root(probe); print('GUARD: PASSED -- the defect is live')
      except Refusal: print('GUARD: refused')
      "
      ```
      Expect **`samefile: True`** and **`GUARD: PASSED`**. On a case-sensitive filesystem the probe's
      parent will not exist; say so and use the skip in 2.4 instead.
- [x] 2.2 Write the failing test first, in `tests/test_run_directory.py`, bound to
      `run-directory:containment:containment-is-decided-by-identity`: a run root naming a directory
      inside the working tree by a spelling the filesystem resolves to the same directory is refused.
      **Guard it** with a probe for filesystem case-insensitivity and `pytest.mark.skipif` — CI is Linux.
      Verify: `uv run pytest tests/test_run_directory.py -k identity` — **fails, for the stated reason.**
- [x] 2.3 Replace the textual comparison in `isekai/interface/wiring.py:71-88`. Decide containment by
      walking `runs.resolve()` and its parents and comparing `(st_dev, st_ino)` against `REPOSITORY` and
      `DATA_ROOT`. A run root that does not exist yet must still be decidable, so compare against the
      nearest ancestor that does. **`os.path.normcase` is a no-op on darwin and will not close this** —
      do not reach for it. Keep the refusal message exactly as it is.
- [x] 2.4 Verify the new test passes and the three existing containment scenarios still do:
      `uv run pytest tests/test_run_directory.py -k containment -v`
- [x] 2.5 Verify the other axes are still sound — traversal, symlinks, `..`, relative paths and a
      non-existent root all behave as before. Verify: `uv run pytest tests/test_run_directory.py`
- [x] 2.6 Verify the gate: `make gate`

## 3. `wiring_from()`, and the seams a ③-only caller does not need

> Design D1. **The reason this extraction exists is the guard phase 2 just fixed**: a front end that
> builds `Wiring(...)` directly the way the suite does would skip it, and a server is exactly the thing
> that should not.

- [x] 3.1 Add `wiring_from(*, runs: Path, server: str | None = None) -> Wiring` to
      `isekai/interface/wiring.py`, carrying the `_check_run_root` call and the construction.
      Reduce `wiring(args)` to `return wiring_from(runs=args.runs, server=getattr(args, "server", None))`.
- [x] 3.2 Make `reader` and `sorter` optional on `Wiring`, following `client`'s precedent. A ③-only
      server fabricating a `ClaudeReader()` it never calls is a lie in the code.
- [x] 3.3 Verify the guard cannot be skipped by the new door, bound to
      `run-directory:containment:in-tree-run-root-is-refused`: `wiring_from(runs=<in-tree path>)` refuses.
      Verify: `uv run pytest tests/ -k wiring_from -v`
- [x] 3.4 Verify no call site changed meaning: `uv run pytest tests/test_pipeline_cli.py tests/test_generate.py tests/test_resume.py tests/test_run_directory.py`
- [x] 3.5 Verify the gate: `make gate`

## 4. `review.py`: `save_draft()`, `TokenBudget`, and two refusals that do not run

> Design D4, D5, D6, D13, and spec delta `review`. **Four separate things in one file, and the file is
> opened once.** `approve()` and `estimate_tokens` are **not** touched — that is what keeps all 26
> `approve` call sites standing.

- [x] 4.1 Write the tests first, in `tests/test_review.py`, bound to the six `review:draft-update:*` and
      `review:budget:*` keys in `specs/review/spec.md`. Verify:
      `uv run pytest tests/test_review.py -k "draft_update or budget"` — **fails, for the stated reasons.**
- [x] 4.2 Add `save_draft(run, flow, fields)`. It replaces the highest draft's `fields` in place, keeps
      the version and the recorded `sheet`, and **refuses a payload whose key set differs from the
      draft's** — `set(fields) != set(existing["fields"])`. It refuses when no draft exists. It does not
      create one: `review()` owns that.
- [x] 4.3 Add `TokenBudget(total, per_field, overhead)` and `token_budget(fields, schema, flow)`.
      `total` is counted over `assemble(fields, schema.names, flow)[0]`; `per_field[name]` is that
      field's words plus one separator per tag; `overhead` is `total - sum(per_field.values())`.
      **Leave `estimate_tokens` byte-identical** — it is `approve()`'s and it stays wrong on purpose.
- [x] 4.4 Verify the numbers reconcile against real data. Verify:
      ```
      uv run python -c "
      from isekai.foundation.flow import load_flow
      from isekai.foundation.run import read_artifact
      from isekai.pipeline.review import token_budget, estimate_tokens
      f = load_flow('summon-v1')
      from pathlib import Path
      b = read_artifact(Path('.data/v0.17/runs/e831676b7ccf_cowboy-shoot-1/summon-v1/sheets/001.json'))['fields']
      tb = token_budget(b, f.schema, f)
      print('total', tb.total, 'sum(shares)+overhead', sum(tb.per_field.values())+tb.overhead)
      print('old estimate_tokens', estimate_tokens(b, f.schema))
      "
      ```
      Expect the two printed totals on line 1 to be **equal**, and the old estimate to be **lower by
      roughly nineteen**.
- [x] 4.5 Repair `review.py:112` — it names `python -m isekai sheet`, which exits 2 because `--flow` is
      required. Make it name `python -m isekai sheet --flow {flow}`. **Verify in two steps, never by
      running the verb** — running `sheet` for real calls a paid model. Verify the string changed:
      `grep -n "isekai sheet --flow" isekai/pipeline/review.py` — **one hit.**
      Then verify that remedy is something the parser accepts:
      ```
      uv run python -c "
      import shlex
      from isekai.interface.cli import build_parser
      build_parser().parse_args(shlex.split('sheet --flow summon-v1'))
      print('the remedy parses')
      "
      ```
      Expect **`the remedy parses`** and no `SystemExit`.
- [x] 4.6 Repair `review.py:224` — it names `{REVIEW}/{flow}/`, the stage-first layout v0.16 deleted.
      Make it `{flow}/{REVIEW}/`. Verify: `uv run pytest tests/test_review.py -k overwritten -v`
- [x] 4.7 Verify the whole review suite and the remedy allowlist:
      `uv run pytest tests/test_review.py tests/test_resume.py`
- [x] 4.8 Verify the gate: `make gate`

## 5. The server and the verb

> Design D1, D2, D3, D11, and spec delta `ui`. **`batch.py` must import no web framework**, so the whole
> startup refusal order is testable in the main suite without the `ui` extra. Only `app.py` imports
> FastAPI.

- [x] 5.1 Add the extra to `pyproject.toml`: `[project.optional-dependencies] ui = ["fastapi", "uvicorn"]`
      — both explicit, because `fastapi[standard]` pulls a much wider tree for one server.
      **`dependencies = []` stays empty.** ⛔ **This is a dependency addition: state the justification
      and stop for approval before running anything.**
      **Two gate commands break unless both of these land with it.**
      **(a) The lock.** `uv sync --locked` is gate command one and fails against a `pyproject.toml` the
      lock does not cover. Run `uv lock`, commit `uv.lock` with this phase, then verify:
      `uv sync --locked` — **exits 0**, and `uv sync --locked --extra ui` — **exits 0**.
      **(b) The type checker.** `uv run ty check` is gate command four and CI never installs this extra,
      so `isekai/interface/ui/app.py`'s FastAPI import is unresolvable there. Add a
      `[[tool.ty.overrides]]` block scoped to that one file and that one rule —
      `include = ["isekai/interface/ui/app.py"]` with `unresolved-import = "ignore"` — following the
      block `eval_backends.py` already has, **and copy its reasoning into the comment**: an override is
      green whether or not the extra is installed, which per-line `ty: ignore` comments cannot be,
      because ty exits non-zero on the unused-directive warning they raise when the extra *is* present.
      Verify: `uv run ty check` — **exits 0**, and again under `uv run --extra ui ty check` — **exits 0.**
- [x] 5.2 Write `isekai/interface/ui/batch.py` — `Batch` and `establish(...)`, performing the refusal
      order stated by `specs/ui/spec.md`'s first requirement: flow, inputs, `review()` per input, `image_dimensions()` per
      input, vocabulary, bundle. Report together via `across()`. **No FastAPI import in this file.**
- [x] 5.3 Write `tests/test_ui.py` for the startup order, bound to the four `ui:startup:*` keys and the
      two `ui:batch:*` keys. **Stdlib only, main suite.** Verify:
      `uv run pytest tests/test_ui.py -v`
- [x] 5.4 Add the invariant test to `tests/test_ui.py`, bound to
      `ui:invariant:server-never-names-an-artifact`: no file under `isekai/interface/ui/` contains
      `envelope(`, `artifact_name(` or `write_json(`. **Its docstring must state that it is a tripwire
      and not a proof** — an aliased import walks past it and a hand-built f-string is invisible to it.
      Verify: `uv run pytest tests/test_ui.py -k invariant -v`
- [x] 5.5 Write `isekai/interface/ui/app.py` — `create_app()` and the six endpoints of
      `design.md` § *The API*. `Refusal` becomes an HTTP response; nothing else catches it.
- [x] 5.6 Write `isekai/interface/ui/bundle.py` — `ensure_built()`, bound to
      `ui:bundle:a-missing-bundle-is-built` and `ui:bundle:missing-dependencies-refuse-by-name`. A missing `ui/node_modules/`
      **refuses, naming `npm install`**; a missing `node` refuses naming what to install, copying
      `claude_cli.require_binary()`'s shape. A missing `ui/dist/` runs `vite build`.
- [x] 5.7 Write `isekai/interface/ui/__init__.py` — `serve(...)`, which runs uvicorn on 127.0.0.1.
- [x] 5.8 Add the verb to `isekai/interface/cli.py`: `("ui", "serve the review surface for a batch of
      inputs")` in `VERBS`, its own `--flow` (**single, required — not `action="append"`**) and
      `--port` defaulting to 8517. **The handler imports `isekai.interface.ui` inside the function**,
      with a comment naming `tests/test_pipeline_cli.py`'s `-S` guard as the reason.
- [x] 5.9 Verify the guard is still green and understands why: `uv run pytest tests/test_pipeline_cli.py -v`
- [x] 5.10 Verify the serving verb's flag shape, bound to `cli:flow-selection:a-serving-verb-takes-one-flow`:
      `uv run python -m isekai ui --flow summon-v1 --flow conjure-v1 2>&1 | tail -2` — **refused, naming
      the one-flow limit.**
- [x] 5.11 Verify the API against a running app with the extra installed, in `tests/test_ui_api.py`.
      **It must open with `pytest.importorskip("fastapi")`** — a module-level `from fastapi.testclient
      import TestClient` fails *collection* without the extra, which is gate command five going red, not
      a skip. Do **not** copy the eval tests here: they stay in the main suite by faking their boundary
      (`tests/eval_fakes.py`) and never import the extra at all, so they are not this pattern.
      Bind the remaining four
      `ui` scenarios here: `ui:vocabulary:matches-are-ranked-by-post-count`,
      `ui:vocabulary:an-unmatched-fragment-commits-nothing`,
      `ui:approval:approved-input-refuses-a-draft-update` and
      `ui:approval:approved-input-opens-read-only`. Verify:
      `uv run --extra ui pytest tests/test_ui_api.py -v`
- [x] 5.11b Verify every scenario in the change's `ui` delta now has a test naming it. Verify:
      ```
      for k in $(grep -ho '\*\*Key:\*\* `ui:[^`]*`' openspec/changes/0018-review-ui/specs/ui/spec.md \
                 | sed 's/.*`\(.*\)`/\1/'); do
        grep -rq "$k" tests/ && echo "OK   $k" || echo "MISS $k"; done
      ```
      — **no `MISS` lines.**
- [x] 5.12 Verify the gate: `make gate`

## 6. Vue: shell, tokens, rail, and the read-only sheet

> `ui/design/components.md` build order 1–2, and `design.md` § *Build reference*. **This is most of the pixels.**

- [ ] 6.1 Scaffold `ui/` — `package.json`, `vite.config.ts`, `index.html`, `src/main.ts`,
      `src/ReviewApp.vue`. Add `ui/dist/` and `ui/node_modules/` to `.gitignore`.
- [ ] 6.2 Copy `ui/design/design-system/styles.css` to `ui/src/styles.css` **and delete line 2's
      Google Fonts `@import`.** Download Inter 400/500/600/700 as woff2 into `ui/src/assets/fonts/` and
      add a local `@font-face` block. `ui/design/` is imported and read-only — **never edit it.**
- [ ] 6.3 Build `AppHeader.vue`, `BatchRail.vue` and `StatusMark.vue` against a static fixture. Four
      marks, not five — `square` went with 5a. Header run line is **`summon-v1 · 3 inputs · 0 approved`**
      (frame delta 2), receipts are **`<flow>/review/001.draft.json`** (delta 3), **no ② draft pill**
      (delta 1).
- [ ] 6.4 Build `SheetForm.vue`, `SheetHeader.vue`, `TokenBudget.vue`, `FieldRow.vue`, `TagChip.vue` —
      read-only. Schema order, never re-sorted. Empty rows read `empty` with a hollow ring and **no
      empties action anywhere** (delta 5). Above 77 the bar **clamps at 100%** and the total takes
      `--color-accent` — nothing else of 4b (delta 8).
- [ ] 6.5 Verify it builds: `cd ui && npm install && npm run build`
- [ ] 6.6 Verify by eye against `ui/design/screens/01-review-draft-loaded.png`, less deltas 1, 2, 3,
      4, 5 and 8. **State which deltas you applied and confirm nothing else differs.**
- [ ] 6.7 Verify the gate: `make gate`

## 7. Vue: the autocomplete

> `ui/design/components.md` build order 3. **This is the piece that decides whether the tool is fast.**

- [ ] 7.1 Build `useVocabulary()` against `GET /api/tags?q=`, debounced at 120 ms. The client ranks
      nothing — the server's order is the order.
- [ ] 7.2 Build `TagAutocomplete.vue` — 430px, `--color-surface`, `--radius-md`, `--shadow-md`,
      `top: 30px`, **absolutely positioned so it overlays the rows below and never displaces them.**
      Row 1 preselected with `accent-900`. Counts right-aligned, mono, `tabular-nums`. Footer
      `↑↓ move · ⏎ commit · esc close` and `<matches> of 8,106`.
- [ ] 7.3 Render ` · rare` in `accent-300` for `posts < 2000`. **This threshold exists nowhere in the
      repo** — the design is its only authority.
- [ ] 7.4 Verify the real data, not the design's: `curl -s 'localhost:8517/api/tags?q=blonde' | head` —
      **two matches, `blonde hair` and `blonde pubic hair`.** `platinum blonde hair` is absent from the
      prediction set (delta 10), so 2b is a layout reference only.
- [ ] 7.5 Verify by eye against `ui/design/screens/02-editing-autocomplete.png` and
      `ui/design/screens/03-autocomplete-blonde-detail.png` for **layout and behaviour**, not content.
- [ ] 7.6 Verify it still builds: `cd ui && npm run build` — **exits 0.** `make gate` cannot see this phase.
- [ ] 7.7 Verify the gate: `make gate`

## 8. Vue: editing and autosave

> `ui/design/components.md` build order 4, and the keyboard model in `design.md` § *Build reference*.

- [ ] 8.1 Build `TagInput.vue` — the fragment as **bare mono text with a 1px accent caret**, never a
      chip. Committed and in-flight must never look alike.
- [ ] 8.2 Implement the keyboard model, less `⌃↓` and `⌥⏎`, which went with 5a. **Replacing a selected
      chip by typing then `Enter` is the single commonest edit in the job** — it must be three
      keystrokes, not delete-then-add.
- [ ] 8.3 Build `useSheet()` — a **400 ms** debounced `PUT` of the whole draft. The last-saved timestamp
      comes from the server, not the client clock: the receipt has to be true. **There is no Save
      control anywhere** — if one appears, the design has been broken.
- [ ] 8.4 Undo is a stack of **edit operations**, not sheet snapshots, crossing all fields, cleared when
      the operator changes input.
- [ ] 8.5 Verify a fragment matching nothing cannot be committed — **there is no path to free text in a
      chip.** This is what underwrites two of the four refusal kinds the version defers.
- [ ] 8.6 Verify the draft on disk changes and keeps its number:
      `watch -n1 'ls -la .data/v0.18/runs/*/summon-v1/review/'` while typing — **`001.draft.json`
      updates in place; no `002` appears.**
- [ ] 8.7 Verify it still builds: `cd ui && npm run build` — **exits 0.** `make gate` cannot see this phase.
- [ ] 8.8 Verify the gate: `make gate`

## 9. Vue: approve, read-only, and the refusal line

> `ui/design/components.md` build order 5, Design D5 and D6. **The screenshot target is `ui/design/screens/08-approved.png`
> only — `ui/design/screens/07-refused.png` is 5a and out of scope.**

- [ ] 9.1 Build `ApproveBar.vue` — accent-outlined, **always live, no disabled twin, no empties action.**
- [ ] 9.2 Build `useApproval()`. On success the header shows **both receipts**, the approved one in
      `accent-300`, and the button becomes the fact `Approved HH:MM:SS`.
- [ ] 9.3 **The input goes read-only** (Design D5). The footer states the fact and names
      `<flow>/review/NNN.approved.json`. No control, no exit affordance (deltas 6 and 7).
- [ ] 9.4 Add the refusal line to `AppHeader.vue` — **one header-level line carrying the `Refusal`
      string verbatim**, in the design's established voice for undesigned states: blunt, no modal, and
      it must never imply the operator's work was lost.
- [ ] 9.5 Verify the refusal path end to end: approve an input, then `PUT` a draft to it from a second
      tab. **Refused, the line appears, and nothing on disk changed.**
- [ ] 9.6 Verify by eye against `ui/design/screens/08-approved.png`, less deltas 2, 3, 6 and 7.
- [ ] 9.7 Verify it still builds: `cd ui && npm run build` — **exits 0.** `make gate` cannot see this phase.
- [ ] 9.8 Verify the gate: `make gate`

## 10. Vue: the overlay, the loading state, the manifest

> `ui/design/components.md` build order 6.

- [ ] 10.1 Build `PhotoOverlay.vue` — teleported to body, ground
      `color-mix(in srgb, var(--color-bg) 72%, black)`, **no `.lighten` blend** (this is the one place
      the photograph must be seen as it is), `Fit` / `1:1 pixels`, and arrow keys still moving through
      the batch. The caption shows paragraphs only — no tinted phrases, no dashed runs (delta 4).
- [ ] 10.2 Build `LoadingSkeleton.vue` — **counted, not spun.** 135° striped placeholders, flat bars,
      **no shimmer**, no photograph until it is decoded. `vocabulary 8,106 tags · loaded` is a real
      number from `len()`.
- [ ] 10.3 Build `RunManifest.vue` — 7b, with real paths: `<run>/<flow>/review/` and
      `NNN.approved.json`, never the design's `runs/2026-09-17/` or `.sheet.json` (delta 9).
- [ ] 10.4 Verify by eye against `ui/design/screens/04-photo-overlay.png`, `ui/design/screens/09-batch-loading.png` and
      `ui/design/screens/10-all-approved.png`, less the stated deltas.
- [ ] 10.5 Verify it still builds: `cd ui && npm run build` — **exits 0.** `make gate` cannot see this phase.
- [ ] 10.6 Verify the gate: `make gate`

## 11. The docs this version makes false

> Design D12, and the roadmap's §⑤ sweep. **Three of these are claims the repository makes about itself
> that this change falsifies.** Leaving one false adds to a list this release is supposed to shorten.

- [ ] 11.1 `CLAUDE.md:199-201` — *"there is nothing generated outside it to get wrong"* is no longer
      true. Extend the boundary paragraph to name **four** roots and how each fails differently:
      `.data/` loss of work · `models/` a byte-identical re-download · `ui/dist/` a deterministic
      rebuild · `ui/node_modules/` an `npm install`.
- [ ] 11.2 `CLAUDE.md` — state that **node is a system dependency of `isekai ui`**, and that it is the
      repo's **second**, after the `claude` binary. Add `ui` to the verb list and correct *"six verbs"*
      wherever it appears.
- [ ] 11.3 `CLAUDE.md:109` — *"`openspec` 1.11 ships no `new`/`scaffold` command"* is **false**;
      `openspec new change <name>` works in 1.11.0. Correct it, and note that this repo scaffolds by
      hand anyway because it keeps no `openspec/config.yaml`.
- [ ] 11.4 `README.md` — add `ui/` to the tree and `isekai ui` to the verb list. `isekai/README.md` —
      add a `ui` row to the edge table.
- [ ] 11.5 `openspec/specs/cli/spec.md` — its gloss reads *"one entry point, six verbs"*. **This is
      header prose, not a requirement, so no delta carries it**; correct it here so the release fold
      does not have to remember.
- [ ] 11.6 Verify nothing claims six verbs or one ignored root:
      `grep -rn "six verbs\|one ignored root" --include="*.md" . | grep -v CHANGELOG | grep -v changes/archive`
      — **no output.**
- [ ] 11.7 Verify the gate: `make gate`

## 12. The free walkthrough: the surface end to end, on data that already exists

> **Nothing here is metered.** It runs against a copy of the v0.17 run data, so no hosted model is
> called and no pod is rented. **It is the gate in front of phase 13** — a defect found here costs
> nothing, and the same defect found after the pod is up costs a session.

- [ ] 12.1 Build the walkthrough root from existing data. Verify:
      ```
      rm -rf .data/v0.18 && mkdir -p .data/v0.18 && cp -R .data/v0.17/runs .data/v0.18/runs
      rm -rf .data/v0.18/runs/*/summon-v1/review .data/v0.18/runs/*/conjure-v1/review
      ls .data/v0.18/runs/*/summon-v1/sheets/
      ```
      Expect four inputs, each with `001.json` and no review directory.
- [ ] 12.2 Start the surface and paste what it prints. Verify:
      ```
      uv run --extra ui python -m isekai ui \
        e831676b7ccf_cowboy-shoot-1 147ea6d5604b_full-height-1 4965a5b47b45_cowboy-shoot-3 \
        --flow summon-v1 --runs .data/v0.18/runs
      ```
      Expect a URL and nothing else — **every refusal lands before it.**
- [ ] 12.3 **Correct and approve all three in the browser.** Verify on disk:
      `ls .data/v0.18/runs/*/summon-v1/review/` — **three `001.approved.json`, and no
      `001.draft.json` left.**
- [ ] 12.4 Verify at least one sheet records that a human changed it:
      ```
      uv run python -c "
      from pathlib import Path
      from isekai.foundation.run import read_artifact
      for p in sorted(Path('.data/v0.18/runs').glob('*/summon-v1/review/001.approved.json')):
          print(p.parts[3], read_artifact(p)['producer']['edited'])
      "
      ```
      — **at least one `True`.**
- [ ] 12.5 **The all-empty sheet.** `bf0b95dba4d6_cowboy-shoot-2`'s summon sheet has every field empty —
      2 tokens. Open it and confirm sixteen hollow rings, the word `empty` sixteen times, **no empties
      action anywhere**, and that it approves.
- [ ] 12.6 **The 21-field schema.** Run the surface once for `4965a5b47b45_cowboy-shoot-3` with
      `--flow conjure-v1` — it is one of the three inputs that carries a conjure sheet — and confirm all
      21 rows fit a 1000px viewport without scrolling. The record claimed they would not; the
      measurement says they do.
- [ ] 12.7 **Read-only is real.** Reopen the surface against the same root. Every input opens read-only,
      named by its approved artifact, and nothing offers to edit it.
- [ ] 12.8 **The refusal line is real.** With an input approved, `PUT` a draft to it from a second tab.
      **Refused, the line appears carrying the `Refusal` verbatim, and nothing on disk changed.**
- [ ] 12.9 Verify the gate: `make gate`

## 13. ⚠️ **HUMAN · METERED · GPU · HALT** — the acceptance run

**The only metered phase, and it does not start itself.** Phase 12 has already proved the surface works
on data that exists; this proves it on photographs that do not yet, and closes the loop through a render.

**Ceiling: 45 minutes and ~$0.30 for the GPU half.** Planned at **three photographs × one flow × one
seed = three renders — $0.036 boot plus 3 × ~$0.01 ≈ $0.07**, about 15–25 minutes boot to teardown. The
hosted-model half is six calls — three captions and three sorts — at the rate `caption` and `sheet`
already bill; it is cents, and it is not what the ceiling is for. **Exceeding the ceiling is a halt, not
a judgement call.**

- [ ] 13.1 ⛔ **HALT. Run nothing in this phase until the operator has answered.** Stop here and ask
      them for three things, then wait:
      1. **Three photographs**, placed where they want the run root to be, and the `--runs` path to use.
      2. **Confirmation that spending is fine now** — this phase calls a hosted model six times and
         rents a GPU. Quote the ceiling above when you ask.
      3. **An explicit go.** Silence is not a go, and neither is *"looks good"* on the phase before it.
      **Do not prepare the photographs yourself, do not pick substitutes from `.data/`, and do not
      proceed on the assumption that phase 12's approval covers this.**
- [ ] 13.2 ⚠️ **METERED — hosted model.** With the operator's photographs and their `--runs` path:
      ```
      uv run python -m isekai caption <photos…> --flow summon-v1 --runs <root>
      uv run python -m isekai sheet   <ids…>   --flow summon-v1 --runs <root>
      ```
      Verify three captions and three sheets exist, and paste the run ids — the surface needs them.
- [ ] 13.3 **The acceptance.** Start the surface on those three inputs, **correct every sheet in the
      browser against the photograph, and approve each one.** Verify: three `001.approved.json` on disk
      and no drafts left. **If every sheet approves, the version works** — `review.approve()` is the only
      writer of an approved artifact whatever calls it, so the only thing the UI controls is the draft's
      contents.
- [ ] 13.4 ⚠️ **ABORT CHECK — this is the one task that can change the version's verdict.** Before the
      pod: the operator confirms that correcting on this surface was **faster and better informed** than
      `$EDITOR` would have been — that the post count and the live token number changed a decision they
      would otherwise have made blind. **If it did not, say so and halt.** The version's whole claim is
      *a sheet is corrected on a surface that knows the vocabulary*; a surface nobody prefers has not
      earned the deprecation of the hand path.
- [ ] 13.5 ⚠️ **GPU** — one session, announced before `infra/up.sh` and torn down with
      `infra/down.sh` in the same session:
      ```
      uv run python -m isekai generate <ids…> --flow summon-v1 --seed <N> --server <addr> --runs <root>
      ```
      Download the outputs before teardown, tear down, and **confirm the account is empty through the
      RunPod MCP, recording what it returned.** Verify three renders from **one** boot.
- [ ] 13.6 **By eye, and this is the version's product judgement:** the renders reflect the corrections
      made in the browser rather than the sorter's draft. A tag the operator added is visible; a tag they
      removed is gone. **This is the only evidence that the surface changed the output rather than just
      the file.**
- [ ] 13.7 Record the session's duration and actual cost in `CHANGELOG.md`, and the answer to 13.4
      alongside them.
- [ ] 13.8 Verify the gate: `make gate`
- [ ] 13.9 Verify the change is well-formed: `openspec validate 0018-review-ui --strict` — **exits 0.**
