# Tasks — the deletion

## Progress

- [x] 1 — The gate's exemption, landed first while it is still a no-op
- [x] 2 — The old path deleted: modules, graphs, tests
- [x] 3 — `isekai/photo.py`, and the 4:1 ceiling restored to the surviving path
- [ ] 4 — The run root's containment, and the requirement that holds it
- [ ] 5 — The manifest's orphans, and `infra/up.sh`'s bounded wait
- [ ] 6 — The record: `CLAUDE.md`, the README, `.gitignore`, the version line

## The per-phase ritual

Every phase, without exception:

1. **Test-first where there is logic.** Phases 3 and 4 have it. Red → green.
2. **Run each sub-task's stated verification — run it, never summarize it.** Paste real output.
3. **Gate green before the commit** — every command in `.minions/minions.toml`'s `gate` array, in order.
   **Never weaken the gate to pass**; halt and say so.
4. **A `CHANGELOG.md` entry** under `## [Unreleased]`, appended in that phase's own commit.
5. **Check the box** in `## Progress` above, in that phase's own commit. The first unchecked entry is
   the current phase.
6. **One commit per phase**, staged **by name**, carrying the trailer
   `Change: 0014-delete-the-old-path` **contiguous** with `Co-Authored-By:` — no blank line between
   them.

### Why the phases are in this order, and why it is not negotiable

Every boundary must be green, and two orderings would make it red:

```
  1  the ty override        a no-op today; without it, phase 2's deletions turn `ty check` red
                            on an archived file the repo forbids editing        (design.md D5)
        ▼
  2  delete the old path    isekai/workflow.py KEEPS ITS NAME and every name in it here.
                            Pruning the four old-path names before their importers are gone
                            breaks conftest, cli, pipeline, mutate and overrides at once.
        ▼
  3  rename and prune       now nothing imports them. `git mv`, delete the four, add the ceiling.
        ▼
  4  5  6                   independent of each other; their order is convenience only.
```

**The arithmetic each phase must land on**, so a miscount is caught at its phase rather than at release.
Today: **726**.

```
  phase 2   -55 test_cli · -30 test_variations · -21 test_mutation · -13 test_overrides
            -2  test_polling · -1 test_pipeline_cli (the vacuous one)
            -21 test_workflow_injection (62 → 41)
            -3  test_evaluate (the -S guard on convert, and the two pipeline-driven pod_image tests)
            +2  comfy-transport, rebound into test_generate
            +1  the -S twin, moved into test_pipeline_cli
                                                            ──▶ 726 - 146 + 3 = 583
  phase 3   +2  the ceiling · +1 the per-photograph refusal · +1 the seed's width
                                                            ──▶ 587
  phase 4   +3  run-root containment
                                                            ──▶ 590
```

**This is the change's own arithmetic, not a measured promise.** If a phase lands on a different number,
**stop and account for the difference before ticking the box** — a count that drifts silently is how a
deleted test becomes a deleted requirement.

**Every surviving test keeps its `@pytest.mark.spec("<key>")`.** Where a scenario changes capability the
marker moves with it — `workflow-injection:working-resolution:*` → `image-generation:working-resolution:*`,
and `workflow-mutation:jitter:seed-is-64-bit` → `image-generation:seeds:seeds-are-drawn-at-full-64-bit-width`.
A test whose scenario is `REMOVED` is deleted with it, never left unbound.

---

## 1. The gate's exemption, landed first while it is still a no-op

- [x] 1.1 Add `openspec/changes/archive/0010-illustrious-base/controlnet_probe.py` to the existing
  `[[tool.ty.overrides]]` `include` list in `pyproject.toml` — **by literal path**, the form already
  proven in that file. A `**` glob is unverified; design.md **D5** says to use the literal form. Verify:
  `uv run ty check` exits 0, and `git diff --stat pyproject.toml` shows one file changed.
- [x] 1.2 Add a comment in that block's established style: an archived change is a record of code that
  was true at a past commit, and `unresolved-import` asks whether it is true *today*, which the archive
  makes no claim about. State that the exemption is **permanent** — the probe is never repaired, because
  *"archived changes are never deleted."* Verify: `uv run ruff format --check .` exits 0 and
  `git diff pyproject.toml` shows the comment above the entry.
- [x] 1.3 Full gate green. `CHANGELOG.md` entry. Tick box 1. Commit.

## 2. The old path deleted: modules, graphs, tests

> **`isekai/workflow.py` keeps its name and every name in it for this whole phase.** The rename and the
> pruning are phase 3. Doing them here breaks five importers at once and the boundary cannot be green.

- [x] 2.1 Delete `convert.py`, `isekai/cli.py`, `isekai/pipeline.py`, `isekai/mutate.py`,
  `isekai/overrides.py`, `workflows/pipeline.json`, `workflows/pipeline_ui.json`, and the now-dead
  `Overrides` TypedDict from `isekai/comfy_types.py`. Verify:
  `grep -rn "isekai\.cli\|isekai\.pipeline\|isekai\.mutate\|isekai\.overrides\|Overrides" --include='*.py' . | grep -v '\.venv'`
  returns **only** `openspec/changes/archive/0010-illustrious-base/controlnet_probe.py`.
- [x] 2.2 Delete `tests/test_cli.py` (55), `tests/test_variations.py` (30), `tests/test_mutation.py`
  (21), `tests/test_overrides.py` (13), `tests/test_polling.py` (2), and
  `tests/test_pipeline_cli.py`'s `test_the_pipeline_surface_does_not_load_the_render_surface` (`:53-69`),
  which still passes after the deletion but asserts `'isekai.cli' not in sys.modules` about a module that
  no longer exists. Verify: `uv run pytest --collect-only -q | tail -1`.
- [x] 2.3 Repoint `tests/conftest.py:11,50`'s `_shipped_workflow` fixture at
  `flows/summon-v1/graph.json` and drop its `PIPELINE_PATH` import. Verify:
  `uv run pytest tests/test_manifest_binding.py tests/test_infra.py -q` — failures are expected here and
  2.4 fixes them; **this sub-task's check is that they are assertion failures, not import or fixture
  errors.**
- [x] 2.4 Fix the five assertions the new graph invalidates: `tests/test_manifest_binding.py:56`, `:71`,
  `:85` — the LineArt/Tile trio; `summon-v1` uses `DWPreprocessor` alone, so `unclassified_node_classes`
  is `[]` and `graph_model_files` no longer names the Tile or mistoLine ControlNets — and
  `tests/test_infra.py:65`, `:81`, where `annotator_files` yields **2**, not 4: drop `sk_model.pth` and
  `sk_model2.pth` from the set literal and change `len(needed) == 4` to `2`. Verify:
  `uv run pytest tests/test_manifest_binding.py tests/test_infra.py -q` exits 0 at 12 and 24.
- [x] 2.5 Split `tests/test_workflow_injection.py` **in place** — the file is renamed in phase 3, with
  the module. Delete the 21 tests that depend on the old path: the 17 taking the `workflow` fixture, the
  three `find_node`/`find_nodes` tests over synthetic dicts (`:25`, `:35`, `:43`), and the one calling
  `cli.parse_args` (`:163`). **The two ceiling tests at `:480` and `:498` are among the 17** — they drive
  `inject`, and `summon-v1` has two `ImageScale` nodes, so `find_node` is ambiguous against it. Their
  scenario is reborn in phase 3 against the new implementation. Verify:
  `uv run pytest tests/test_workflow_injection.py --collect-only -q | tail -1` reads **41**.
- [x] 2.6 Rebind `comfy-transport`'s two scenarios into `tests/test_generate.py`, carrying their existing
  keys: a polling test constructing `FakeComfyClient(pending_polls=2)` and asserting
  `client.history_calls == 3`, and a retrieval test asserting `client.viewed` equals the image dict the
  fake's history named. They are `tests/test_polling.py`'s two, with `pipeline.run` swapped for `render`.
  Verify: `uv run pytest tests/test_generate.py -q` exits 0 and
  `grep -rn "comfy-transport:polling\|comfy-transport:retrieval" tests/` finds both keys.
- [x] 2.7 Resolve the `-S` stdlib guard pair. `tests/test_evaluate.py:750` guards `import convert` and
  **dies with its target**; its falsifiability twin at `:769` — *"the guard above proves nothing unless
  `-S` really refuses"* — then guards nothing where it sits. **Delete the first; move the twin into
  `tests/test_pipeline_cli.py`**, beside `:92`'s guard on `isekai.__main__`, which v0.13 already built.
  Keep its `spec_exempt` marker and update its comment to name the guard it now falsifies. Verify:
  `uv run pytest tests/test_pipeline_cli.py -q` exits 0 and
  `grep -rn '"-S"' tests/ | grep -v test_pipeline_cli` returns nothing.
- [x] 2.8 **Delete** `tests/test_evaluate.py`'s two `pipeline.run`-driven tests — `:601`
  `test_the_table_names_the_image_the_pipeline_itself_recorded` and `:626`
  `test_the_table_says_unrecorded_when_the_run_never_learned_its_image`. Their driver is deleted and the
  surviving render path writes no `pod_image` key. **Change nothing else**: `pod_image_of` and `table()`
  keep their signatures, and the `evaluation` spec's report requirement is not touched — design.md
  **D13**. Verify: `uv run pytest tests/test_evaluate.py -q` exits 0 at **50**, and
  `grep -c 'spec("evaluation:report:names-its-run")' tests/test_evaluate.py` returns **3**, so the
  scenario keeps its binding.
- [x] 2.9 Full gate green, and `uv run pytest --collect-only -q | tail -1` reads **583**. `CHANGELOG.md`
  entry. Tick box 2. Commit.

## 3. `isekai/photo.py`, and the 4:1 ceiling restored to the surviving path

- [x] 3.1 `git mv isekai/workflow.py isekai/photo.py` and
  `git mv tests/test_workflow_injection.py tests/test_photo.py`. Update the two importers —
  `isekai/generate.py:56` and `isekai/evaluate.py:34`, one line each — plus the moved test file's
  imports, and `isekai/evaluate.py:228`'s comment, which names the module and becomes true again. Verify:
  `uv run pytest -q` exits 0 and
  `grep -rn "isekai\.workflow" --include='*.py' . | grep -v '\.venv'` returns only the archived probe.
- [x] 3.2 Delete `PIPELINE_PATH`, `find_node`, `find_nodes` and `inject` from `isekai/photo.py`. Keep the
  JPEG/PNG header walk, the EXIF transpose, `image_dimensions`, `working_resolution`, `WORKING_SCALE`,
  `DIMENSION_STEP`, `MAX_HEADER_DIMENSION`, `MAX_HEADER_BYTES` and `MAX_TARGET_LONG_SIDE` — the last is
  used by 3.6, not dead. Verify: `uv run pytest -q` exits 0 and
  `grep -n "def inject\|def find_node\|def find_nodes\|PIPELINE_PATH" isekai/photo.py` returns nothing.
- [x] 3.3 Rekey the moved file's markers from `workflow-injection:working-resolution:*` to
  `image-generation:working-resolution:*`. Its `scale-precedes-every-consumer` test now reads
  `flows/summon-v1/graph.json` and asserts the scaling node sits between `LoadImage` and **both**
  `ApplyInstantIDAdvanced` and `DWPreprocessor`. Verify: `grep -rn "workflow-injection" tests/` returns
  nothing, and `uv run pytest tests/test_photo.py -q` exits 0 at 41.
- [x] 3.4 **Red first.** In `tests/test_generate.py`, two tests bound to
  `image-generation:working-resolution:an-extreme-aspect-ratio-is-refused`: a photograph whose short side
  at the working scale drives its long side past `MAX_TARGET_LONG_SIDE` raises **`Refusal`** — not
  `SystemExit` — naming the file, both computed dimensions and the bound; and a photograph at exactly the
  bound still renders. Verify both fail, and that they fail because no such refusal is raised.
- [x] 3.5 **Red first.** One test bound to
  `image-generation:working-resolution:a-refusal-is-per-photograph`: a batch of three photographs, the
  middle one refused for the reason above, still renders the other two and reports the refusal against
  its own photograph. Verify it fails.
- [x] 3.6 Implement in `isekai/generate.py`'s `photo_resolution` (`:235-251`): after computing the
  working target, raise `Refusal` when `max(width, height) > MAX_TARGET_LONG_SIDE`. **Bound the working
  target, not the hires target** — design.md **D4**: hires scales both axes by `hires_scale` and so does
  not change the aspect ratio, and bounding the hires value would tighten 4:1 to 2.67:1 for a reason
  unrelated to aspect. Verify 3.4 and 3.5 now pass.
- [x] 3.7 **Red first, then green:** a test bound to
  `image-generation:seeds:seeds-are-drawn-at-full-64-bit-width`, asserting `draw_seeds` draws across the
  full 64-bit space and that the width comes from the single `SEED_BITS` constant rather than a repeated
  literal. It carries `workflow-mutation:jitter:seed-is-64-bit` forward. Verify:
  `uv run pytest tests/test_generate.py -q` exits 0.
- [x] 3.8 Fix `working_resolution`'s docstring, which justifies the short-side rule with *"a wide photo
  lands below the **line-art ControlNet's** floor"* — `summon-v1` has no LineArt node. The rule holds on
  SDXL's own trained scale; the reason written beside it belongs to the deleted path. Verify:
  `grep -in "line.art" isekai/photo.py` returns nothing.
- [x] 3.9 Full gate green, and `uv run pytest --collect-only -q | tail -1` reads **587**. `CHANGELOG.md`
  entry. Tick box 3. Commit.

## 4. The run root's containment, and the requirement that holds it

- [ ] 4.1 **Red first.** Three tests bound to `run-directory:containment:*`, in
  `tests/test_run_directory.py`: a run root resolving **inside the repository working tree and not under
  `DATA_ROOT`** is refused before any run is created, with a message naming the path given and what would
  be accepted; a run root resolving **outside the repository** is accepted and a run is created under it;
  the default is under `DATA_ROOT`. Verify the first fails and the other two pass.
- [ ] 4.2 Implement the refusal in `wiring()` (`isekai/__main__.py:189-204`), taking the repository root
  from the module's own location rather than from the process's working directory. **The rule bounds the
  working tree, not the filesystem** — design.md **D7**: any path outside the repository is accepted,
  because version control cannot reach it, which is what keeps `--runs` useful for a run on another disk.
  Verify 4.1 passes.
- [ ] 4.3 Replace the comment at `isekai/__main__.py:106-109`, which has claimed containment under
  `.data/` since v0.13 while no check existed. The new text states what is actually enforced, and why a
  path outside the repository needs no check. Verify: `grep -n "Anywhere it points" isekai/__main__.py`
  returns nothing.
- [ ] 4.4 Full gate green, and `uv run pytest --collect-only -q | tail -1` reads **590**. `CHANGELOG.md`
  entry. Tick box 4. Commit.

## 5. The manifest's orphans, and `infra/up.sh`'s bounded wait

- [ ] 5.1 Remove the four artifacts the old graph orphaned, from `scripts/models.json` **and** from
  `scripts/derive_manifest.py`'s `PINNED` —
  `controlnet/TTPLANET_Controlnet_Tile_realistic_v2_fp16.safetensors`,
  `controlnet/mistoLine_rank256.safetensors`,
  `annotator_ckpts/lllyasviel/Annotators/sk_model.pth` and `…/sk_model2.pth` (≈2 GB) — and drop
  `TTPlanet`, `TheMistoAI` and `lllyasviel` from `PUBLISHERS` **only if** no surviving entry names them.
  Verify: `uv run pytest tests/test_manifest.py tests/test_derivation.py tests/test_flow.py -q` exits 0
  — that is where the byte-identical re-derivation invariant (**L21**) is held.
- [ ] 5.2 Port **only** `infra/up.sh`'s bounded readiness wait from the `v0.13_prototype` branch — the
  **420 s deadline that tears the pod down itself on timeout**, replacing `main`'s `while true … sleep 5`,
  which has no deadline at all. **Do not port the `8188/http` port or the proxy probe** — design.md
  **D10**: the RunPod proxy is a public, unauthenticated ComfyUI endpoint, and it is gated on
  authentication landing first. Keep `main`'s own GPU-preference-list fix, which the prototype predates.
  Verify: `bash -n infra/up.sh` exits 0, `uv run pytest tests/test_infra.py -q` exits 0, and
  `grep -n "8188/http\|proxy\.runpod\.net" infra/up.sh` returns nothing.
- [ ] 5.3 Full gate green. `CHANGELOG.md` entry. Tick box 5. Commit.

## 6. The record: `CLAUDE.md`, the README, `.gitignore`, the version line

- [ ] 6.1 `CLAUDE.md:17` — replace the one-path bullet with **L3's entry gate**, keeping the history
  clause. The replacement text is settled in design.md **D11**; it is **replaced, not restored**, because
  a count would forbid the flow registry v0.16 adds. Verify: `grep -n "There is one path" CLAUDE.md`
  returns nothing.
- [ ] 6.2 `CLAUDE.md` — correct the twelve remaining stale sites: `:15` (`convert.py`'s import graph),
  `:48`, `:62`, `:69-72` (injection, mutation and overrides as seams), `:109-110` — **it still says "four
  capabilities… a fifth, `model-provisioning`, on the v0.9 branch"**, and it is **nine**, named —
  `:136-143` (layout: the entry point, `workflows/`), `:178-179` (*"the whole required surface is
  `convert.py photo.jpg`"*), and `:198`. Verify:
  `grep -n "convert\.py\|workflow-injection\|workflow-mutation\|pipeline\.json\|isekai/cli\.py" CLAUDE.md`
  returns nothing but deliberately-historical prose.
- [ ] 6.3 `README.md` — rewrite the work-in-progress banner so it **names no version at all**: the banner
  already cites `openspec/` as authoritative for what is being built next, and a forward version
  reference is one reordering away from being wrong, which it already was. Then replace every runnable
  command — `:42`, `:51`, `:60`, `:98`, `:111-113`, `:157`, `:225`. **Verify the new Quickstart against
  the actual parser**: run `python -m isekai --help` and each verb's `--help`, and paste the output;
  never write it from memory. `generate` needs `--server` and an open tunnel. Verify:
  `grep -n "convert\.py\|--denoise\|--variations" README.md` returns nothing.
- [ ] 6.4 `.gitignore` — remove `outputs/`, whose producer this version deletes. **Keep `.inputs/`**:
  `baseline/build_contact_sheets.py:107` still defaults `--sources` to `.inputs/baseline` and survives
  this change. Update the comment, which schedules both lines for this version and is wrong about one.
  Verify: `grep -n "^outputs/" .gitignore` returns nothing and `grep -n "^\.inputs/" .gitignore` returns
  the surviving line.
- [ ] 6.5 The version line in the three places this change controls — `proposal.md`'s `version: v0.14`
  (already set), `CHANGELOG.md`'s released heading, and `pyproject.toml`'s `version`. The annotated tag
  is `mf-release`'s act, not this change's. Verify: `grep -n '^version' pyproject.toml` and
  `grep -n '^## \[' CHANGELOG.md | head -2` agree on `0.14.0`.
- [ ] 6.6 Full gate green. `CHANGELOG.md` entry. Tick box 6. Commit.

---

## What this version does **not** do

Stated so a later reader does not mistake an omission for an oversight, and so no phase invents it:

- **No `migrate`.** v0.13 removed it by decision (change 0013's `design.md` D2) and the living spec
  enforces the removal — `run-directory:schema:refusal-names-the-fix` requires that a refusal *"does not
  suggest an action this build cannot perform."* It arrives with the version that introduces the second
  schema version.
- **No `session()`, no orphan reconciler, no `status.json`, no `provision`.** v0.16, v0.17, v0.19.
- **No `scripts/` → `provisioning/` rename**, though this version does open `scripts/models.json`.
  Design.md **D10**.
- **No HTTP-proxy fallback in `infra/up.sh`** — design.md **D10**: it opens a public, unauthenticated
  ComfyUI endpoint.
- **No SSH host-key pinning.** RunPod's API publishes no host key — `GET /v2/pods/{id}` returns
  `ssh.proxy` and `ssh.direct` with `host`, `port`, `username` and `command` and nothing else — so the
  recorded fix does not exist as described. The mechanism that would work is `session()`-shaped: **v0.16**.
- **No re-measurement.** No flow has yet been graded against L30's bar on SFace, and the tool that would
  is v0.18. This version's licence is **L3**, not L30 — design.md **D1** and **D2**.
