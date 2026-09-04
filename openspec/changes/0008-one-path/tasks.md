# Tasks — 0008-one-path

## Progress

- [ ] 1 — Delete the three dead paths: `qwen`, `animagine`, `animagine-i2i`
- [ ] 2 — Rename the survivor to nothing: `workflows/pipeline.json`, `inject()`, model-free spec keys
- [ ] 3 — The CLI becomes the product: flags out, directory output, five derived variations
- [ ] 4 — The sweep: the registry, the aliases and every branch with no reachable caller
- [ ] 5 — The prompt: drop the pose tag, pin the string
- [ ] 6 — The docs: `README.md` and `CLAUDE.md` describe one path
- [ ] 7 — The spend rule: rewrite `CLAUDE.md`'s metered bullet
- [ ] 8 — ⚠️ **GPU · HALT** — live smoke test, run by the operator

## The per-phase ritual

Every phase, without exception:

1. **Test-first where there is logic.** Phases 6 and 7 are prose and have no new logic; every other phase does.
   Red → green.
2. **Run each phase's stated verification — run it, never summarize it.** The commands are named in the phase
   detail below. Paste real output.
3. **Gate green before the commit** — `make gate`, which runs the five commands in `.minions/minions.toml`'s
   `gate` array, in order. A phase that leaves the gate red is not done. **Never weaken the gate to pass**;
   halt instead.
4. **Append that phase's entry under `## [Unreleased]` in `CHANGELOG.md`**, in the style of the entries already
   there. Use `### Removed` / `### Changed` / `### Added` headings; mark the two breaking items **BREAKING**
   (see phase 3).
5. **Check the box** in the `## Progress` list above, in that phase's own commit. The first unchecked entry is
   the current phase; that is how the loop reads this file.
6. **One commit per phase**, staged **by name**, carrying the trailer `Change: 0008-one-path` **contiguous**
   with `Co-Authored-By:` — no blank line between them, or git stops parsing the trailer block.

**The test count moves down, not up, for most of this change.** v0.7 ends at 114. A phase that deletes
scenarios is expected to delete their tests; that is not a weakened gate, it is the work. What is *not*
allowed is a test deleted because it fails — see the stop-conditions in `mf-build`.

## Phase detail

### 1 — Delete the three dead paths

Remove `qwen`, `animagine` and `animagine-i2i` entirely: their graphs, their fixtures, their code paths, their
tests and their spec scenarios. `animagine-i2i-cn` survives under its current name; phase 2 renames it.

**Files deleted:** `workflows/qwen-image-edit.json` · `workflows/qwen-image-edit.reference.json` ·
`workflows/animagine-instantid.json` · `workflows/animagine-i2i.json` ·
`tests/fixtures/qwen-image-edit.json` · `tests/fixtures/animagine-instantid.json` ·
`tests/fixtures/animagine-i2i.json` · `openspec/specs/model-registry/`.

**Code:** `isekai/workflow.py` loses `inject_qwen`. `isekai/models.py`'s registry drops to the one surviving
entry (the file itself goes in phase 4). `isekai/cli.py`'s `--model` `choices` drops to the one surviving name
(the flag itself goes in phase 3). `scripts/download_models.sh` loses the four Qwen downloads and its
`--model`-naming comments; the Animagine + InstantID + antelopev2 + ControlNet-stack downloads stay.

**Tests:** `tests/conftest.py` keeps only the surviving fixture. `tests/test_model_dispatch.py`,
`tests/test_cli.py`, `tests/test_workflow_injection.py`, `tests/test_mutation.py`, `tests/test_overrides.py`
and `tests/test_variations.py` lose every test bound to a deleted path, and the rest move onto the surviving
fixture. Also deleted here: `test_run_without_overrides_is_byte_identical_to_v04` — it pins v0.4's output for a
path this phase deletes, so it is back-compat with nothing.

*The fixture swap is mechanical.* Both graphs put `KSampler` at node `10` with the same `denoise` 0.65 / `cfg` 5
and the same `ip_weight` 0.9 on `ApplyInstantIDAdvanced`, and ControlNet jitter draws **last** — so pinned
`denoise` / `cfg` / `ip_weight` values carry over unchanged. Only the graph's baked `seed` differs, and mutation
overwrites it.

**⚠️ The tooling risk, already half-answered:** `openspec/specs/model-registry/` is a whole capability going to
zero requirements, and nothing in this repo has removed one before. `openspec validate 0008-one-path --strict`
was **green at cut time** with all three requirements declared REMOVED, so the delta is well-formed. Re-run it
here, after the directory is actually deleted. If it rejects, take the fallback `design.md` R1 already settled —
absorb the one surviving fact into `cli` and keep `model-registry` as a stub — and **say so in the commit
message**. Do not improvise a third option. The remaining exposure is at **archive** time, which is
`mf-release`'s problem, not this phase's.

**Verification:**
- `openspec validate 0008-one-path --strict` — green (run this first, see above)
- `git grep -ril qwen -- . ':!CHANGELOG.md' ':!openspec/changes/archive'` — no hits
- `git grep -n "animagine-instantid\|animagine-i2i\.json"` — no hits outside `CHANGELOG.md` and the archive
- `make gate` — exit 0

**Closes:** `model-registry` (all three requirements REMOVED) · `cli:model-selection:*` ·
`cli:dispatch:*` · the qwen scenarios in `workflow-injection`.

---

### 2 — Rename the survivor to nothing

The one path stops naming its base. Renamed **once**, here, before v0.9 relocks anything against it.

- `workflows/animagine-i2i-cn.json` → `workflows/pipeline.json` (`git mv`)
- `workflows/animagine-i2i-cn_ui.json` → `workflows/pipeline_ui.json` (`git mv`) — the ComfyUI-editor export,
  and the only artifact the API graph can be regenerated from by hand. It survives.
- `inject_animagine` → `inject`
- `tests/fixtures/` deleted entirely; `tests/conftest.py`'s loader reads `workflows/` (`design.md` D9)
- Spec keys lose their model segment. Two keys change:
  `workflow-injection:photo-wiring:controlnet-single-loader-across-stack` →
  `workflow-injection:photo-wiring:single-loader-fans-out`, and
  `workflow-injection:latent-init:img2img-inits-from-photo-below-one` →
  `workflow-injection:latent-init:inits-from-photo-below-one`. Every `@pytest.mark.spec` naming either moves
  with it.

**Verification:**
- `git grep -rn "animagine" -- . ':!CHANGELOG.md' ':!openspec/changes/archive'` — no hits
- `ls workflows/` — exactly `pipeline.json` and `pipeline_ui.json`
- `test -d tests/fixtures` — absent
- `make gate` — exit 0

**Closes:** the renamed keys in `workflow-injection`.

---

### 3 — The CLI becomes the product

`convert.py photo.jpg` is the whole required surface.

- **Deleted:** `--model`, `--workflow`, `--prompt`. `--prompt` was **required**; every v0.7 invocation breaks.
- **`-o` becomes a directory**, default `./outputs` (already gitignored). An `-o` naming a file with an image
  extension is **rejected at parse time**, with a message saying the flag now names a directory — otherwise an
  upgrading caller silently gets a directory called `out.png`.
- `main()` resolves `<dir>/<UTC instant>/` — compact basic ISO, `20260904T141530Z` — and hands the **resolved**
  path to `run`. `run` draws no clock; that is what keeps the suite deterministic (`design.md` D4).
- `--variations` defaults to **5**, ceiling **25**, both enforced at parse time in the shape of the existing
  dial validators.
- Every variation's seed is derived from `random.Random(seed)`; variation 0 loses its verbatim-seed exemption
  (`design.md` D5). The per-variation seed is still printed.
- Images are `0.png` … `4.png` inside the run directory, and `run.json` records the run seed, the per-variation
  seeds and the dial values in force.
- `run`'s `prompt` parameter goes with the flag; `inject` is called with the photo alone.

**Unchanged, deliberately:** `--seed` (the reproducibility contract) and `--server`, plus `--denoise`, `--cfg`
and `--ip-weight` — the dials are the only way to *find* a tuned value, which is what v0.9 has to do.

**Verification:**
- `uv run pytest tests/test_cli.py -q` — green
- `uv run python convert.py --help` — shows no `--model`, `--workflow` or `--prompt`
- `uv run python convert.py photo.jpg -o out.png` — exits non-zero, message names the directory change
- `make gate` — exit 0

**Closes:** `cli:output-destination:*` · `cli:reproducibility:*` (modified) ·
`workflow-mutation:output-layout:*` · `workflow-mutation:reproducibility:every-variation-seed-is-derived` ·
`workflow-mutation:reproducibility:seeded-run-is-reproducible-and-distinct`.

---

### 4 — The sweep

Delete every abstraction with nothing passing through it. `design.md` D2 and D3 are authoritative here.

- `isekai/models.py`, `Model`, `get_model` — deleted. `tests/test_model_dispatch.py` with them.
- `Injector` and `Mutator` deleted from `isekai/comfy_types.py`. `ComfyTransport` **stays** — `FakeComfyClient`
  is what makes the suite offline, which is the rule: *a parameter is a seam only if something else is actually
  passed through it.*
- `pipeline.run` loses `inject` and `mutate` as parameters and imports them. `workflow` **stays** a parameter,
  so `run` does no file I/O.
- `Mutator | None` and the `mutate is None` branch — gone. The `variations > 1 and model.mutate is None`
  refusal in `cli.py` goes with the models it protected.
- `overrides.py`'s "no `ApplyInstantIDAdvanced`" silent no-op — unreachable; deleted.
- `mutate.py`'s `_base` wired-dial guard — it existed because qwen wired `cfg`; deleted.
- `mutate.py`'s `_node_order` subgraph-id handling (`"102:14"`) — no surviving graph has one; deleted, and the
  ControlNet ids sort numerically.
- `find_node`'s `title` parameter — no caller; deleted, along with the title-lookup scenario.
- `mutate.py`'s "draws nothing without ControlNet nodes, so animagine-i2i stays byte-for-byte unchanged"
  ordering comment — its reason was deleted in phase 1. The ordering itself may stay; the justification changes.

**Verification:**
- `test -f isekai/models.py` — absent
- `git grep -n "Injector\|Mutator\|get_model"` — no hits outside `CHANGELOG.md` and the archive
- `uv run pytest -q` — green
- `make gate` — exit 0

**Closes:** the scenarios dropped by `workflow-mutation`'s five REMOVED-and-re-ADDED requirements
(`ip-weight-ignored-without-identity-node`, `linked-dial-is-overwritten`, `linked-dial-refused-legibly`,
`no-draw-without-controlnet-nodes`, `no-mutator-stays-deterministic`,
`no-override-matches-previous-release`) · `workflow-injection:node-location:locates-by-title`.

**Note the delta shape** (`design.md` D13): `openspec` has no scenario-level removal, so a requirement whose
scenarios narrow is REMOVED and re-ADDED under a new name. Requirement *names* therefore change in the living
spec; scenario *keys* do not, so `@pytest.mark.spec` bindings are unaffected.

---

### 5 — The prompt

The positive string loses its one piece of typed subject text and nothing else.

- Remove `arms crossed` from the graph's positive `CLIPTextEncode`. **Keep `1girl, solo`** — it is the
  Danbooru mode selector, not subject text, and changing it would be a register decision v0.8 may not make
  (`design.md` D6).
- Comment the string in `workflows/pipeline_ui.json`'s node title, or beside the pinned literal in the test,
  naming the version that owns the register: **v0.9, the version that changes the base.**
- Pin the string by **equality** in the suite, not by a blacklist (`design.md` D7).
- `CHANGELOG.md` records the known defect plainly: `1girl` fixes the gender of every input photo, in a product
  whose input is "a photo of a person". It is owned by v0.9.

**This phase changes render output** and there is no GPU in the build to check it. That is expected: phase 8
confirms the path *runs*. Nothing in this change may claim it renders better.

**Verification:**
- `uv run pytest -q -k prompt` — green
- `python3 -c "import json;print(json.load(open('workflows/pipeline.json'))['3']['inputs']['text'])"` — the
  string, with no pose tag
- `make gate` — exit 0

**Closes:** `workflow-injection:committed-prompt:*`.

---

### 6 — The docs

`README.md` and `CLAUDE.md` currently describe a product that no longer exists.

**`README.md`:** the four-row model table, `--model` in "Useful flags", `--prompt` in the Quickstart command,
and the "four selectable models" status line all go. The status line becomes v0.8. Quickstart becomes
`python convert.py me.jpg`, with the run-directory layout shown. The repository-layout block loses
`workflows/ # ComfyUI graphs, one per model`.

**`CLAUDE.md`:** three statements are now false and are rewritten —

- *"Every version extends the previous. Models are additive and all stay selectable; nothing is removed."*
  → **"There is one path. A version may replace it; it may not add a second."**
- *"The model registry (`isekai/models.py`) — a name→`Model` map … adding a model is a registry entry, not a
  branch."* → replaced by the seam rule this change learned: **a parameter is a seam only if something else is
  actually passed through it** — which is why `ComfyTransport` is a parameter and injection is not.
- *"## The models"*, listing four → the one path and what carries each identity axis.

Also: the `--prompt`/`--model` references in the opening description, and the `injection wires image + prompt`
phrasing, which is now `injection wires the image`.

**Verification:**
- `git grep -n -e "--model" -e "--prompt" -e "animagine" -e "qwen" -- README.md CLAUDE.md` — no hits
- `git grep -n "nothing is removed" CLAUDE.md` — no hits
- `make gate` — exit 0

---

### 7 — The spend rule

Rewrite `CLAUDE.md`'s metered-work guardrail. This is an authority **expansion** in an otherwise subtractive
change, which is why it is its own phase and why it is late (`design.md` D10).

The bullet currently ends *"**Never bring up a paid pod on your own initiative.**"* It is replaced by a rule
that states **all four** of:

1. **Who creates** — `infra/up.sh`.
2. **Who tears down** — `infra/down.sh`. Teardown is the act.
3. **Who confirms** — the RunPod MCP confirms the pod is gone. **Confirmation is not the act**; a rule that
   only names the check has not said what stops the billing.
4. **What happens when the MCP is unreachable** — the explicit human "go" is back, unchanged. A rule whose
   enforcement mechanism may be disconnected when the rule is read must say what it degrades to.

Plus a ceiling: **45 minutes, ~$0.30** for a single pod session, stated as numbers rather than "promptly".

**Precondition for phase 8, not for this phase:** the RunPod MCP must be authorized from an **interactive**
session. It cannot be authorized non-interactively. Authorizing it is the operator's action.

**Verification:**
- `git grep -n "on your own initiative" CLAUDE.md` — no hits
- `git grep -n -e "up.sh" -e "down.sh" -e "MCP" -e "45" CLAUDE.md` — all four clauses and the ceiling present
- `make gate` — exit 0

---

### 8 — ⚠️ **GPU · HALT** — live smoke test

**This phase spends real money, and `mf-build` does not run it. HALT here.**

This is `mf-build` stop-condition 1 — *an acceptance that cannot be made a passing check* — invoked
deliberately. Stop cleanly, **without committing and without ticking the box**, and hand back to the operator
with the checklist below. An unticked box on a clean tree is where this resumes.

**The division of labour, agreed in advance:**

| who | does what |
|---|---|
| agent | brings the pod up (`infra/up.sh`), prints the tunnel command, tears it down (`infra/down.sh`), confirms via the RunPod MCP that the pod is gone |
| operator | supplies a photo of a person, opens the tunnel, runs `convert.py`, judges the result |

**Pass criterion — written before the run, not after.** All five, or the phase fails:

1. `convert.py <photo>` exits 0
2. `./outputs/<UTC instant>/` exists
3. `0.png` … `4.png` present and non-empty
4. `run.json` present and carrying five seeds
5. teardown confirmed via the RunPod MCP, and **what it returned is recorded**

**Nothing from this run is tracked** — not the photo, not the renders. The input would be the repo's first
tracked binary, and committing five renders of a specific tuning in a repo whose next version changes the base
means stale images that edge toward the quality claim this change forbids (`design.md` D11).

**What this phase proves, and what it does not.** It proves the path **runs**. It makes **no** claim about what
was rendered — not fidelity, not identity, not quality. There is no evaluator yet; that is two versions out.

**A failure is blocking.** It adds phases to `0008-one-path`; it does not become `0009`.

**The commit is a record, not a change** — a ticked box, the result written into this phase's detail, and one
`CHANGELOG.md` line under `## [0.8.0]` recording the live verification (the version's single permitted claim,
stated publicly). That is deliberate and is not an empty phase: the paid run is the act, and the record is its
only tracked artifact.

**This is also the spend rule's first exercise.** Record what the MCP teardown confirmation actually returned —
it is the only evidence phase 7 will have before that rule starts guarding unattended runs.

**Estimated cost:** one pod session, capped at 45 minutes, ~$0.30.

---

## What this change does NOT do

Named here so a build pass does not drift into them:

- **No base change.** Checkpoint, ControlNet stack, InstantID weights and the network volume are untouched.
- **No register decision.** `1girl, solo` ships as-is; only the pose tag leaves.
- **No tagger seam.** The future WD14 entry point is designed against the base it will run on.
- **No quality claim**, in any artifact of this change.
- **No tracked binaries.**
