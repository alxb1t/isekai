# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0/).

> **On this record's provenance.** This file was **backfilled during v0.7**, from the git
> history, after eleven phases and three releases had already shipped without it. Entries are
> reconstructed from commit messages and diffs; **anything the log does not support is not
> written here.** From v0.7 on, an entry is appended per phase under `## [Unreleased]` and cut
> at release, as the project's change contract requires.
>
> Two gaps in the record, stated rather than smoothed over:
>
> - **There is no 0.5.0.** The history goes v0.4 (2026-08-04) directly to v0.6 (2026-08-15).
>   No tag, branch or commit references a v0.5, so the version was skipped rather than lost.
> - **0.4.0 and 0.6.0 were never tagged.** They are real, completed, merged versions and are
>   recorded as releases here; their dates are their last commit rather than a tag date.
>   Tags `v0.1`–`v0.3` also use the two-part form that predates the current release contract.
>
> `0.7.0`'s heading is cut here, in the commit that completes the work; the annotated `v0.7.0`
> tag is the release act and is created against **this** commit, so the four places the
> version line lives — proposal, changelog, `pyproject.toml`, tag — all name the same thing.

## [Unreleased]

### Changed

- **The gate and the encoder window are each declared once.** The `Makefile` is the gate's one
  declaration; `.minions/minions.toml` is deleted and `.minions/` ignored whole. The review UI reads
  the window from the token budget the server sends (`0027` design D1, D2).
- **The layers, the principles' *held by* names and the vocabulary checks are held by tests.**
  `tests/test_layers.py` scans every import, with an exact allowlist of the edges still to move;
  `tests/test_principles.py` resolves each named test; a missing vocabulary fails the checks that
  read it unless `ISEKAI_VOCABULARY=absent`, which CI sets (`0027` design D3–D5).
- **`foundation` imports nothing above it.** `atomic_write.py` moves from `shared/` to `foundation/`,
  and the `Workflow` graph type from `boundary/comfy_types.py` to `foundation/flow.py`, which owns
  the graph (`0027` design D6).
- **Pin verification is `boundary/provision.py`'s.** `resolve`, `entry_for` and their exceptions move
  there from `evaluation/eval_models.py`, and `resolve` takes its manifest. `wiring.load_vocabulary`
  verifies the vocabulary; `shared/vocabulary.py`'s `load` only reads it (`0027` design D7, D8).
- **The ComfyUI transport is `boundary/comfy/`**, a package with a front door. The client turns a
  network error into `Unreachable` itself, word for word; the CLI's `_Reporting` wrapper is gone.
  `probe/loader_probe.py` now receives `Unreachable` rather than a raw `URLError` (`0027` design D9).
- **The approval state is the pipeline's.** `Status` and `state(directory)` move, unchanged, from the
  review UI's `Batch` into `pipeline/review.py`; `run_view.py` asks `run.is_approved`; the unused
  `review.is_complete` is deleted (`0027` design D11).

## [0.22.4] - 2026-09-25

### Changed

- **The sweep: code, tests and spec preambles say what the code does.** Docstrings, comments,
  the `caption` and `sheet` help text, the parser's description and `pyproject.toml` lose retired
  mechanisms, *"the only"* claims and counts (`0026` design D1, S1–S30). No behaviour changes.
- **`docs/` holds the architecture.** `principles.md`, `decisions.md` (with D29 and D30, the product
  scope) and `README.md` are written from `0026`'s payload; `docs/arc/` is flattened into `docs/`, its
  false claims corrected, and `modules.md` gains how the components interact.
- **`CLAUDE.md` keeps only process and imports `docs/principles.md`.** Its design rules move to `docs/`;
  the change id is the next free number; it gains what a patch may hold, and the notebook and
  demo-subject rules (`0026` design D8).
- **The group READMEs point at `docs/principles.md` and `docs/decisions.md`** instead of *"the design
  record"*, which named nothing in the repository (`0026` design D9).
- **`README.md` stops restating the architecture.** `## The path` becomes `## Architecture`, a link to
  `docs/`; the intro, the caption notes and the gate's mirrors say what the code does (S43–S46, D10).

## [0.22.3] - 2026-09-23

### Changed

- **The negative prompt is quality-only, and the graph no longer carries a second copy of it.**
  `censor, nsfw` left both tracked flows' `flow.json` negative — a negative whose job, per the base
  model's publisher, is quality, while the positive is what decides content. The operator measured
  the difference by eye across real renders. `lens flare, light particles, dust` was already present
  in both, so that half of the ask was a no-op.
- **`graph.json`'s negative node is emptied rather than synchronised, in both flows.** It read
  `bad quality, worst quality, worst detail, sketch, censor, nsfw`, and `worst detail` appeared
  nowhere else — the two strings had already drifted, unnoticed, because nothing reads the second
  one: `generate.py`'s `patch("negative", text=prompt["negative"])` overwrites that node on every
  render from `flow.json`'s fragment, and `negative` is a required role so the patch is
  unconditional. A shipped prompt artifact confirms it, carrying `flow.json`'s string and no
  `worst detail`. Two strings that agree today are two strings that disagree later, so there is now
  one source of truth; if a future path ever renders without patching, it renders with no negative,
  which is visible in the output rather than silently wrong. Same class as the stale
  `filename_prefix` recorded at `v0.22 review/R6`.
- **Both flows are re-pinned, and that is the second exception ever taken to flow immutability.**
  The comment above `tests/test_flow.py`'s `PINNED` now states the rule the repository actually
  follows — the freeze exists so that nothing changes *silently*, not so that nothing changes — and
  keeps the load-bearing half intact: a *divergence* still costs a new identifier, because two flows
  are only comparable over one cohort if an identifier means one configuration. Only an abandoned
  configuration may be re-pinned, and this one is: nothing compares against the old negative. The
  failure message itself is unchanged and still gains no *"unless"* clause. **The comment states the
  rule and no longer narrates the history behind it** — which release re-pinned what belongs in this
  file, not in a test module — and a new test asserts the cheap, mechanical half of the obligation:
  a flow pinned in `PINNED` and named in no `CHANGELOG.md` entry fails. Which digest moved in a given
  release is left to review, because checking it would mean storing the previous digest and so making
  a second source of truth out of the constant that exists to be the only one.
- **`test_no_text_is_taken_from_the_graphs_own_committed_strings` asserts the emptiness instead of
  its old tell.** It used `worst detail`, a tag in the graph and in no manifest, to prove the
  assembly had not read the graph; the emptied node makes that claim structurally, and the assert
  that the node is empty means a string reappearing in it fails rather than quietly becoming a
  second source of truth.
- **The gate was uninstalling the local tagger on every run, and the repair is that the tagger's stack
  is a declared dependency.** `onnxruntime`, `numpy` and `Pillow` left the `tagging` extra and
  `fastapi` and `uvicorn` left the `ui` extra; all five are now in `[project] dependencies`, pinned
  exactly at what `uv.lock` resolved. The symptom was an operator re-running `uv sync --extra tagging`,
  which is a once-per-checkout command — so the question was what removed the packages, and the
  environment answered it: `fastapi` present, the other three absent. `uv sync` makes the environment
  match exactly what it is told and removes extras it is not told about, and gate command one is
  `uv sync --locked` with no `--extra`.
- **`[tool.uv] default-extras` was refused as the fix.** It would have kept `dependencies = []`
  literally true while every real checkout carried 2 GB of onnxruntime under a manifest claiming it
  needed nothing. The local tagger runs on every `caption` for every flow, so *"optional"* was false in
  the plainest sense; the review surface moves on the operator's reading that it is part of running a
  flow rather than an add-on to it. **`eval` stays optional** — it is the scorer, and an evaluator is
  not a way to render.
- **`dependencies = []` is retired; the claim that replaces it is narrower and is what the architecture
  actually rests on** — *the entry point imports no third-party package at module scope*. `wd14.py`'s
  three imports are function-local and `interface/ui/__init__.py` keeps FastAPI off `python -m isekai`'s
  import graph the same way, which is why `isekai show` works on a checkout that has provisioned
  nothing.
- **The `-S` guard is narrowed rather than deleted, and is now falsified against a declared
  dependency.** With the packages installed by default it is the only thing that would catch a
  module-scope import appearing in the entry point's graph — nothing else fails when one is added. Its
  falsification imported `pytest`, a dev-only package; it imports `onnxruntime` now, so a guard that
  stayed green while `-S` leaked the very wheels it excludes is no longer possible.
- **The `dev` group's duplicate `fastapi` and `uvicorn` pins are gone, and a test keeps them gone.** The
  duplication existed only because the `ui` extra was never installed by gate command one, which made
  `tests/test_ui_api.py`'s `importorskip` fire and four `ui` scenarios bound only there prove nothing.
  The test that held the two pin lists equal is replaced by one asserting there is only one list: a
  `dev` entry re-pinning a declared dependency would reinstate the drift this removes. A second new
  test asserts the tagger's three are declared and that `torch` did not follow them out of `eval`.
- **The tagger's refusal names `uv sync` instead of a removed extra**, and the docstrings in
  `interface/ui/app.py`, `batch.py` and `tests/test_ui.py` that described a `ui` extra now describe a
  web framework, because the extra no longer exists to name.
- **CI's resolution checked rather than assumed** — onnxruntime wheels are platform-specific, and
  `1.29.0` publishes `cp312-manylinux_2_28_x86_64`, so `ubuntu-latest` resolves it and no floor is
  needed in the manifest.
- **`## Quickstart` is rewritten as `## Running a flow`, in place** — one guide, photograph to image,
  pod included, rather than a second one beside the old. Commands read as a sequence with the
  explanation under them; the boundary where it stops being free is drawn at the top and repeated at
  the step that crosses it, because `CLAUDE.md`'s spend guardrail wants that visible and a guide that
  hides it is worse than no guide. It now covers what the old one left implicit: where the photograph
  goes (`.inputs/`, gitignored, because it holds a person's likeness), `uv sync` with no flag, the
  tunnel in a second terminal, downloading renders before teardown, and the teardown itself.
- **Every sentence phases 1 and 2 falsified is repaid, in the same version rather than two releases
  later.** `README.md`, `isekai/README.md`, `isekai/boundary/README.md`, `CLAUDE.md` and
  `docs/arc/modules.md` said *the runtime is stdlib-only* or named `dependencies = []`; they now state
  the narrower claim that is true — the entry point imports no third-party package at module scope —
  and say that the `-S` guard is the only thing holding it. `CLAUDE.md` and `README.md` also said *a
  flow is immutable*, which phase 1 made false; both now say what the modified requirement says, that
  a flow is pinned by equality and a divergence is what costs a new identifier. Docstrings in
  `multipart.py`, `provision.py`, `ciede2000.py`, `eval_models.py`, `cli.py`, `evaluate.py` and
  `tests/test_manifest.py` carried the retired claim too and are corrected.
  **This is the third consecutive version whose prose was falsified by the next one** —
  `docs/arc/modules.md`'s rule was written by `v0.22.2` three commits before this change retired it —
  which is the cost of splitting prose from code, and cheaper than the alternative only if the
  documentation version ships close behind the code version it describes.

### Verified

- **The re-pin, recorded: what moved, in both flows.** `design.md` D2 and the modified requirement
  both oblige a re-pinning change to leave this behind in prose a later reader can find.

  | flow | digest before | digest after |
  |---|---|---|
  | `conjure-anime-wai` | `1e991c2be7290a40dbe3301619c67b0bb9c5bb9914f22e6c54ce7078903c6615` | `5de6632e33a83377347f887663213eb69733636edb3a380372e00ab3a9171f61` |
  | `summon-anime-wai` | `8ddd4016dadd16d2b8a740e420e9478ae37ef5b43959c4e86ec1974f5d0792fb` | `3ad0f323d0f4a826cd06a0c37b47fbcceceaa4e8c6074a1153529b5f2ee73e7f` |

  Two strings moved in each flow, and nothing else did — `git diff --stat -- flows/` shows exactly
  `flow.json` and `graph.json` in each of the two directories. In `flow.json`,
  `"bad quality, worst quality, sketch, censor, nsfw, lens flare, light particles, dust"` became
  `"bad quality, worst quality, sketch, lens flare, light particles, dust"`. In `graph.json`,
  `"bad quality, worst quality, worst detail, sketch, censor, nsfw"` became `""`. **Neither flow
  identifier changed**, because the old configuration is abandoned rather than still wanted; no run
  is orphaned, since orphaning follows a changed id and `manifest_digest` has one consumer.
- **Accepted on a pod, by eye, on the operator's own photographs.** Seven photographs, both flows,
  fourteen renders in one pod session — 20m 07s on an RTX PRO 4500 Blackwell at $0.72/hr, ≈$0.24,
  inside the 45-minute and ~$0.30 guardrail. The pod was torn down in the same session and its
  absence confirmed against the provider's API, not against the teardown script's own output.
  Assembly of all fourteen prompts was proved with `--server` omitted before the pod existed, and
  every assembled negative read `bad quality, worst quality, sketch, lens flare, light particles,
  dust` with none carrying `censor`, `nsfw` or `worst detail`. **The operator's verdict on the
  images was that they are good, and the acceptance passed on that.**
- **A clean checkout runs `caption` with no extra flag** — `rm -rf .venv && uv sync --locked`, then
  `caption` wrote the prose, the local WD14 tag list and the hosted tag list. The middle one is the
  artifact the gate used to make impossible.

### Not verified

- **No cohort was scored, and the claim is not that the images are measurably better.** Every render
  made for this version is post-change: there is no before-image for any of these photographs at
  these seeds, so nothing here is a controlled comparison against the old negative. The operator's
  original finding came from their own earlier renders, and this version does not reproduce it — it
  establishes that the new negative renders cleanly end to end on both flows, and rests the rest on
  judgement by eye. **That is the posture this repository already takes toward diffusion quality**,
  and the evaluation sub-system that would replace it is v0.23's; this version does not anticipate it.
- **Nothing on disk says which side of the re-pin a run falls on.** A run's provenance records the
  graph digest, not the flow directory's, so a cohort spanning the edit cannot be split by it after
  the fact. Filed as a run-provenance change rather than fixed here.
- **An intermittent native abort in the tagger, on macOS, seen and not diagnosed.** Three `caption`
  invocations printed `libc++abi: terminating due to uncaught exception of type
  std::__1::system_error: recursive_mutex lock failed` — an onnxruntime threadpool teardown race at
  interpreter exit. It fired *after* every artifact was written, all runs are complete, and a
  targeted re-run did not reproduce it. Exit codes were not captured on the invocations where it
  fired, so whether it aborted those processes is unknown rather than benign.

### Fixed

- **The re-pin record test could not fail for a re-pin.** It asserted each pinned flow was *named*
  in `CHANGELOG.md` — but a name enters when the flow is introduced and cannot leave an append-only
  file, so it would have passed for every re-pin that ever forgot to record itself, while binding a
  scenario whose THEN is *"records which flow moved and what changed in it"*. It asserts the
  **digest** now, which is what a re-pin actually moves, and fires exactly when one changes with no
  entry carrying it. The falsification that "proved" the original renamed a key to a flow the
  changelog never mentions — the new-flow case, not the re-pin case.
- **`test_no_text_is_taken_from_the_graphs_own_committed_strings` had degenerated into a
  tautology.** With the graph's negative emptied, `committed_negative == ""` asserts the fixture and
  `negative != committed_negative` holds for any non-empty negative, so the leak the scenario exists
  to catch had nothing left to fail on. It now runs against a scratch flow whose graph carries a
  string no manifest can supply — a witness that can fail — and a second test asserts the tracked
  flows' negative nodes are empty, which is the structural half.
- **The manifest's invariants moved into `tests/test_packaging.py`.** Two tests asserting the shape
  of `pyproject.toml` had been split across `test_wd14.py` and `test_ui.py` by which feature
  noticed them, carrying three copies of one requirement-name parser and two per-test reads of the
  manifest. One module, one parser, one session-scoped fixture — the shape `conftest.py` already
  uses for every tracked file the suite reads.
- **A borrowed spec binding, removed.** The tagger-stack test carried
  `tagging:pin:the-check-fires-at-first-use`, a scenario about no model file being opened when no
  tagging is performed — nothing to do with where a wheel is declared. The replacements are
  `spec_exempt` and say why.
- **`eval` names only what it adds, and the non-overlap rule is stated over every list.** It still
  floored `onnxruntime`, `numpy` and `Pillow` beside the pins `dependencies` now carries — the
  same two-lists-one-package shape this version deleted between the `ui` extra and the `dev` group,
  wearing the other hat. The narrow `dependencies`-vs-`dev` check is replaced by the general rule.
- **A comment claimed a distinction that does not exist.** The `-S` falsification swap from
  `import pytest` to `import onnxruntime` was justified as catching a leak a dev-only probe would
  miss; both resolve from the same site-packages, so either goes red identically. The comment now
  says it names a runtime dependency for readability, not for reach.
- **Three more dead references to the deleted extras** — `interface/ui/__init__.py` twice and
  `boundary/wd14.py` once — plus `tests/test_wd14.py`'s module docstring, which rested its
  "nothing here imports a wheel" discipline on the `tagging` extra being absent from the gate's
  environment. It is installed now, so that discipline is the suite's own and the docstring says so.
- **The sweep for sentences phase 2 falsified is finished, and one of them was holding a
  suppression open.** `boundary/wd14.py` still justified its `object` return type, its
  `select`/`prepare` split and its function-local imports by a `tagging` extra absent from the gate
  and a *stdlib-only* import graph; each now states the real reason — the value is opaque to every
  caller, the split is kept wheel-free on purpose, and the rule is that the entry point imports no
  third-party package at module scope. `interface/README.md` and `docs/arc/modules.md` named a
  `[ui]` extra that no longer exists. `pyproject.toml`'s `unresolved-import` override still covered
  `wd14.py` and `baseline/build_contact_sheets.py` on the ground that their packages are not
  installed; they are, `ty` is green without the cover, and both leave it. The ANN401 waiver's
  comment no longer claims `numpy` cannot be named — what it cannot name comes from `torch` and
  `transformers`, which `[eval]` still carries.
- **`CLAUDE.md` sent a re-pin's record to the place the implementation had stopped using.** It
  said the statement of what moved is owed *"above `PINNED`"*; since `a5ef56a` it is owed in
  `CHANGELOG.md`, carrying the new digest, and a test fails on any pinned digest no entry carries —
  which, as the rule now says, also costs a newly added flow an entry. The test's failure message
  names that case too. `tasks.md` 1.4 records the departure from its own instruction.

## [0.22.2] - 2026-09-22

### Changed

- **An eleventh false self-claim, caught by the convergence pass rather than by the sweep.**
  `interface/ui/app.py` said the type checker's override for `uvicorn` was *"scoped to this one file
  and this one rule, because CI never installs the extra"*. There is no such override — `app.py`
  appears in neither `[[tool.ty.overrides]]` block nor in `[tool.ruff.lint.per-file-ignores]` — and
  the `dev` group pins `fastapi` and `uvicorn`, so gate command one installs both; `pyproject.toml`
  already said exactly that, in the opposite direction. The docstring now states what is configured:
  the extra is reached from this one module so `python -m isekai`'s import graph never reaches it,
  and nothing is suppressed for it anywhere. The sweep rewrote the paragraph immediately below this
  one and left it standing, which is what *"every claim … checked against the tree"* is worth as a
  description of a pass rather than a guarantee.

  **The same claim stood twice in that file, and the first fix left the twin.** `run()`'s docstring
  carried it too — *"the type checker's override covers this file alone, and CI installs neither
  package"* — 450 lines below the paragraph that had just been corrected, so for one commit the module
  answered *"is anything suppressed for the `ui` extra, and does the gate install it?"* in both
  directions. The clause is deleted; the paragraph above already carries the configuration facts, and
  a repo-wide grep now leaves only `pyproject.toml`'s *"CI never installs this"*, which is about the
  `eval` extra and is true. Two convergence rounds found one claim at one site each: the lesson is
  that a false sentence is worth grepping for, not just fixing where it was seen.

- **The acceptance ran, and it cost nothing: no pod, no render, no `generate`.** `make gate` exits 0 on
  all six commands, 815 tests pass, and `grep spec_exempt tests/ | grep 0024` returns nothing. Every
  numeral this version touched was re-derived from the tree rather than from the sentence it replaced —
  four tracked files per flow, six repo-root anchors across four modules, seven stage directories, seven
  endpoints, seven verbs, five ignored roots, twelve capabilities on disk, three copies of the gate.
  `pytest -k test_every_tracked_flow_matches` passes, so no flow moved and `manifest_digest` did not.

- **The re-opened path was walked by hand against a running surface**, twice — once on the phase-4 code
  and again after `/simplify` rewrote the predicate, with identical results. Approve an input; the edit
  is refused `409` with the new refusal, which now names the verb and says the input comes back
  editable rather than pointing at a future version; `review --flow F --new-version` writes
  `002.draft.json` beside `001.approved.json`; the reload reports `readonly: false`, status
  `re-opened`, and still names the approved artifact; the edit saves into the draft and the approved
  artifact is byte-unchanged; and `/api/batch`'s count equals the approved artifacts the batch's run
  directories hold.

- **What was not verified, stated rather than left to inference.** No pod was created and nothing was
  rendered, so diffusion quality and identity fidelity are untouched by this version and unmeasured by
  it. **Only the four capabilities `v0.22.1` touched were audited** — the other scenarios in the living
  spec were not read against the code, and the eight requirement-level findings this version reports
  are what that partial pass turned up. A full audit is a version of its own and is filed, not done
  here. The browser was exercised through its own HTTP API rather than by a person clicking; the rail's
  rendering of the third state is covered by the type checker and the status the API returns, not by a
  screenshot.


- **The seventeen `spec_exempt` markers are repaid**, one for one, and
  `grep spec_exempt tests/ | grep 0024` returns nothing. `v0.22.1` borrowed a marker whose documented
  meaning is *genuinely structural* on the explicit condition that this version repay it; the debt was
  nearly a fifth of the repository's exemptions and was made countable so its discharge would be
  countable too. **No test in this change carries a `spec_exempt` naming `0024`** — the marker that
  exists to be repaid cannot be the instrument of its own refinancing.

- **The two tests for the state phase 4 built were written red first**, against the keys
  `ui:approval:a-re-opened-input-is-editable` and
  `ui:approval:a-re-opened-input-is-not-counted-approved`. The requirement's two older keys keep their
  tests, re-run against the narrowed gate: `approved-input-refuses-a-draft-update`'s `WHEN` gained an
  *and holds no later draft* clause, and the test that used to prove the re-opened case still refused
  now proves it is accepted — which is the behaviour change, stated where the old assertion was.

- **One binding gained an assertion rather than the scenario losing a clause.**
  `ui:source:each-hosted-tag-is-offered-once` ends *"both artifacts on disk are unchanged"*, which a
  sibling test proved and the test bound to that key did not. It asserts it now, scoped to the two tag
  artifacts: `establish()` opens a draft for every input it is given, so a whole-run snapshot would
  have caught stage ③ starting normally and called it a write by the panel.

### Added

- **Seventeen scenarios for behaviour `v0.22.1` shipped bound to nothing**, one per
  `spec_exempt("behaviour; the scenario lands in 0024")` marker it left, plus two more inside the
  modified `ui` requirement that no marker covers because that version did not build the state. They
  land across four capabilities: `ui` gains Host/Origin validation, the draft-update precondition,
  bundle staleness and the panel's hosted-tag dedup; `cli` gains flow-manifest validation at load;
  `image-generation` gains the transient-transport classification and per-flow assembly;
  `run-directory` gains `show`'s injected flows root and its refusal before any line is printed.

- **The `ui` approval requirement is rewritten rather than deleted** — *"An approved input is read-only
  on the surface"* becomes *"…until it is re-opened"*. Its old rationale inferred from *approval
  deletes the draft* that nothing on disk could hold an edit after approval; the premise is true and
  the inference is not, because `review --new-version` is exactly the explicit act that writes one. Two
  capabilities described one state and disagreed about it, and `review` was the one that was right.

  Each scenario was re-read against the tree before being counted as landed, and each is true at HEAD.
  The key check prints the two `ui:approval:*` keys the `MODIFIED` block restates, as a `MODIFIED`
  requirement must, and nothing else; `openspec validate 0024-the-documents --strict` is green.

### Changed

- **An input re-opened with `review --new-version` is editable on the surface again, and the rail
  reports it as re-opened.** This is the change's only code change, and it is in scope because shipped
  code named this version as the one that resolves it: `v0.22.1` refused every update to an approved
  input, which made `--new-version` write a draft the surface would not edit, and the refusal it
  shipped said exactly that. `review` is the capability that was right — `--new-version` exists for
  this case and `review:copy:second-review-appends` is the older, tested contract — so the gate is now
  **approved and no later draft** rather than approved (`0024` design.md D5). The refusal's forward
  reference to v0.22.2 is gone, replaced by what to do: correct it with the verb, reload, and the input
  comes back re-opened with its approved artifact still named. An approved artifact is still never
  edited in place, in either state.

- **`Batch.state()` is the one definition of the three states, and `re-opened` is *a draft numbered
  above the approved artifact* rather than *a draft exists*.** The comparison is against the approved
  artifact's own version, which is the same number `approve()` records as `approved_from` — it derives
  the filename and the field from one local — so the state is read from filenames alone and no artifact
  is opened. A draft numbered above the approved one is what the verb wrote and nothing else produces
  it; a draft that somehow predated the approval could therefore never re-open one. `readonly`, the
  `PUT` gate and the rail's status were three expressions over the same two predicates, true together
  only because they agreed; they now all read `state()`.

- **`/api/batch`'s approved count now reads the run directories, and that is the fix for the hazard a
  third status creates.** It used to be derived from the status string, which agreed with
  `Batch.approved_count` only while every input holding an approved artifact also *reported* approved —
  a coincidence that ends the moment a status exists meaning *holds one, and is open again*. Deriving
  it would have split the two answers; reading the directory keeps them one answer.
  `ui:batch:approved-count-comes-from-disk` stayed green throughout, and the new
  `ui:approval:a-re-opened-input-is-not-counted-approved` pins the same property from the other side.

- **On the page**: a third rail mark and legend row, a `re-opened` kicker in place of *draft from the
  tagger* for a draft copied from an approved artifact, and the closing manifest now lists every input
  holding an approved artifact rather than only those reporting `approved` — the rail's count reads the
  directory the same way, and a manifest shorter than the count beside it would be two answers to one
  question. `allApproved` stays strict: a re-opened input has a correction waiting and the batch is not
  finished.

- **The four capabilities `v0.22.1` touched were audited against the tree, scenario by scenario.**
  Three false statements were fixed, all of them non-normative: `cli`'s Purpose said *"six that run a
  stage"* when five do — the same file already says *"the five stage verbs"* two requirements later,
  and `isekai/interface/cli.py`'s docstring carried the identical error; and `image-generation`'s
  **Source** line named one tracked flow when two exist, the second being the one that exercises its
  own *optional roles are not assumed* scenarios.

  **Eight further findings are requirement-level and are reported rather than fixed here**, because
  changing a `SHALL` or a scenario is a spec delta and this phase fixes prose (`0024` tasks 4.4):
  `image-generation:inputs:every-approved-flow-renders` claims selecting among approved flows *"requires
  no flag"*, which `generate` has not done since `--flow` became required — and `cli`'s own requirement
  says the opposite, so two capabilities disagree; `cli:generate-signature:count-defaults-to-one` says
  *per approved flow* where the code renders per *named* approved flow;
  `image-generation:working-resolution:scale-precedes-every-consumer` reads *"a tracked flow's graph"*
  and is false for `conjure-anime-wai`, which declares no photograph and carries no image loader;
  `review:copy:second-review-appends`'s `WHEN` omits `--new-version`, without which `review()`
  short-circuits and writes nothing; `review:approval:approve-validates-then-renames` says the
  artifact's bytes are unchanged, while `approve()` builds a fresh envelope — a deviation `review.py`
  documents and the scenario does not; `review`'s provenance requirement records *edited* against the
  **sheet** while a re-opened draft is copied from the **approved artifact**, which this version makes
  a first-class state; `cli:resolution:uncomposed-seam-refuses-by-name`'s `WHEN` is unreachable outside
  the suite, because `wiring_from` always composes all three resolvers; and the `ui` bundle requirement
  covers only *absent*, not the staleness and timeout the code also has — which this change's own delta
  adds. **The other capabilities were not audited**; that full pass is a version of its own.

- **`CLAUDE.md` is agent operating instructions, and nothing else.** 420 lines to 316. `## The path`
  is gone — an audit's verdict on it was *"almost entirely data flow and architecture, with no agent
  instruction in it"* — and `## Layout`'s per-group inventory is **deleted rather than moved**, because
  the six group READMEs already hold it and moving it would have created a seventh copy (`0024`
  design.md D3). What was rule rather than description in either section stayed, relocated to the
  section that owns the rule: *only an approved artifact is ever rendered*, *assembly happens before
  any endpoint is acquired*, *refuse the input rather than the batch*, *stage ① is one verb*, *`review`
  and `approve` stay working verbs*, and the two system dependencies now sit together under a new
  **`## Rules the render path is under`**, which opens by saying what it is not restating.

- **The file states its own ceiling.** The system summary is one paragraph, and the note under it says
  so: a fuller account belongs in `docs/arc/`, and a paragraph here that starts explaining how
  something works rather than what to do about it belongs there too. The ceiling is the point — an
  unbounded summary paragraph is how `## The path` grew the first time.

- **The identity mechanisms moved to `docs/arc/data-flow.md` with the rest of the path**, and the
  dials are **named without their values**: the values live in `flows/<id>/flow.json`, and a value
  written twice is a value that can disagree with itself. The working-resolution rule, `clip_skip`'s
  home in the manifest, and the `models/wd14/` pairing travel with them.

- **Smaller cuts, all of them description.** The measured-implementation constraint lost its
  version-by-version history and kept its rule. The seam list lost `image.py`'s and `generate.py`'s
  module descriptions, whose rules now sit in the render-path section, and the `ComfyTransport` entry
  lost the account of the transport that was deleted a version ago. The living-spec paragraph lost the
  history of its own wrong counts, which was three sentences explaining why the names below it should
  be read instead. The keybinding rule lost the narrative of the violation `v0.22.1` closed.

### Added

- **`docs/arc/`, and it is where this repository's architecture is drawn.** Two files, prose and ASCII,
  **and no quantities in either** (`0024` design.md D2) — a number is the part of a document that goes
  stale, and this repository has now watched that happen to the same column twice.

- **`docs/arc/modules.md` — the module graph.** Every cross-group edge by source; the lazy ones marked
  as lazy with the function each import sits in, including `interface ──▶ interface/ui`, which the
  drawing it replaces collapsed away entirely; the subpackage cycles, each with the reason it exists.
  `isekai/README.md`'s structural sentence moves here with it — *the module graph has no cycles and
  never has; the group graph does, and drawing it as a stack would be a lie* — because it is the most
  useful sentence in that file and this is the file it is about. The two cycles are stated with their
  causes rather than merely reported: `refusal` is what everything raises, and `atomic_write` is a
  primitive `run` writes through.

- **`docs/arc/data-flow.md` — the stages.** The verbs, what each reads and writes, and the run layout
  with every stage directory in it. It leads with the two facts a reader needs before any other:
  **`caption` writes prose, the local list and the hosted list in one invocation**, and the ordering is
  the failure isolation, because the batch loop catches a refusal per *input*; and **the sheet is built
  from the WD14 list, not from the prose**, which is why a missing hosted list is an absent aid and a
  missing local one is a refusal.

### Removed

- **`isekai/README.md`'s edge table**, replaced by a pointer to `docs/arc/modules.md`. It was the
  nearest thing this repository had to a module graph and it carried three errors — a module-level
  `boundary ──▶ shared` missing outright, the `shared ──▶ boundary` laziness annotated backwards, and
  `interface/ui` collapsed away — which is what two drawings of one graph produces. The group READMEs
  keep their file tables: a file table is a local fact and a graph is not (`0024` design.md D4).

### Changed

- **The sweep: every claim this repository makes about itself, checked against the tree.** Ten false
  self-claims in tracked prose, eight stale numerals in `CLAUDE.md`, and every quantity in the group
  READMEs replaced by the names it counted. **No code changed** — `git diff` over `*.py`, `*.vue` and
  `*.ts` touches docstrings and comments only (`0024` design.md D6). Where a claim would be truer with
  a code change, the claim moved and the code change was filed.

- **The ten.** `README.md` called a flow *"two tracked files"* and it is four, now named.
  `isekai/README.md` claimed *"five files … with a falsification twin each"* against six constants
  across four files and **one** twin, and annotated the `shared → boundary` edge as eager when both
  imports sit inside `load()`. `boundary/README.md` claimed *"nothing outside this directory opens a
  socket or spawns a binary"* against three live violations — `evaluation/labels.py` spawns `git`,
  `interface/ui/bundle.py` spawns `npm`, `interface/ui/app.py` binds a port — which are now named as
  filed work rather than denied. `pipeline/sheet.py` said *"the sixteen fields"*, true of
  `summon-anime-wai` and not of `conjure-anime-wai`'s 21. `evaluation/evaluate.py` invoked *"the
  one-path rule"*, which `CLAUDE.md` records as replaced. `scripts/manifest.py` named a `convert.py`
  that does not exist, and `scripts/derive_manifest.py` promised *"the SHA-256 and byte count"* from a
  function returning the digest alone. `tests/test_flow.py` said *"the tracked flow"* singular twice;
  one reference is now plural and the other says which flow it reads and why one suffices. Three
  `CHANGELOG.md` lines 136–153 characters wide were re-wrapped, byte-unchanged in content.

- **`CLAUDE.md`'s numerals.** *"Change one, change all four"* became three copies, because CI invokes
  `make gate` rather than keeping its own. The run layout gained `wd14` and `tags`, the two stage ①
  directories `run.py` has declared since v0.21. The `Cmd+Z` keybinding is no longer described as a
  live violation — v0.22.1 made it match `event.code === 'KeyZ'` as well, so it answers under Cyrillic
  *and* Dvorak. A change is four artifacts or more, not exactly four. The change-id formula now states
  that it has **no patch case** and that a patch takes the next free number, as `v0.22.1` → `0023` did.
  `skip_specs: true` **plus** `specs/.gitkeep` is a pair, and the sentence calling them mutually
  exclusive is gone. The `__init__.py` rule is now a rule about *groups*, with
  `interface/ui/__init__.py` named as the subpackage front door it is. The *"catalogue of twelve
  candidate checkpoints"* referenced no artifact in this repository and is restated without one. The
  ignored-roots table gained `.inputs/`, which holds a person's likeness exactly as `.data/` does, and
  is now named rather than counted — as are the two further *"four ignored roots"* claims in
  `.gitignore` and `interface/ui/bundle.py`. The version line covers `X.Y.Z`, because `## [0.22.1]` is
  in this file.

- **Quantities are gone from the group READMEs.** `isekai/README.md`'s file column names each group's
  files instead of counting them, and the *"count; do not trust the row"* disclaimer goes with the
  numbers it failed to protect: two were wrong again at v0.22, one in the opposite direction from the
  drift the disclaimer described. Every *"Imported by"* table was re-derived from the import graph and
  now names its importers; eight of the counts it replaces were wrong. That re-derivation also
  corrected the importer lists themselves — `pipeline/review.py` is imported by `interface/ui/app.py`
  and `interface/ui/batch.py`, `shared/image.py` by `interface/ui/batch.py`, and
  `foundation/refusal.py` by `boundary/comfy_types.py` and `shared/image.py`, none of which the tables
  had.

- **Three claims wrong for a reason other than a count.** `shared/README.md` said none of its modules
  reads a run or a flow; `field_map.py` imports both and `fields.py` imports `flow`, because a schema
  is a flow's. `interface/README.md` and `ui/app.py` both said *"the six endpoints"*; there are seven,
  now listed by path, with the bundle mount named beside them. `evaluation/README.md`'s
  `eval_backends.py` coverage debt was owed by *"v0.19"* three releases ago; the debt is stated as open
  and the version is dropped, since naming one is what let it go stale.

- **Two smaller repairs.** `ci.yml` called `typecheck_ui.sh` the gate's *"sixth command"*; it is the
  fifth of six (`CHANGELOG.md`'s *"gains a sixth command"* is about the count and is correct).
  `CLAUDE.md`'s never-commit guardrail now names **a pod id** beside the API key and the volume id —
  the three already in this file stay, because it is append-only history and the guardrail is what
  stops a fourth.

## [0.22.1] - 2026-09-22

- **The acceptance ran: gate green and one local pass through ①②③, on five photographs, with no pod.**
  `caption` wrote prose, the local list and the hosted list for every input, in that order; `sheet`
  filled all five from the WD14 list; the surface built its bundle, served the batch and returned a
  receipt for a saved draft. The three operator-visible changes were confirmed by hand against the
  running server, including the **re-opened** state — an approved artifact with a fresh draft beside it —
  which is the one that was actually false before this version. `Cmd+Z` under a Cyrillic layout was
  confirmed by the operator in the browser. **Stage ④ was not run and no pod was rented**, which is the
  design: this version edits no flow file, so `manifest_digest` did not move.

### Changed

- **`num_ctx` is pinned at 4096 in both option maps, and the number is the one that was already in
  force.** It was unset, so the effective window was whatever Ollama resolved from the host -- an
  invisible dependency on a machine, on the two stages that decide what every sheet and every render is
  built from. Measured on the operator's machine before pinning, which is a measurement this repository
  did not have: the reader's `prompt_eval_count` is **1275** (briefing + prompt + photograph),
  `num_predict` draws 1024 from the same window, and `/api/ps` reports the window Ollama resolved with
  nothing pinned as **4096** -- so 2299 of 4096 and nothing was being truncated. **The photograph's
  share is constant at ~729 tokens**: 1275 exactly for 0.17 MB at 800x1125, 2.20 MB at 1248x1824 and
  2.28 MB at 1024x1472, because the vision tower encodes at a fixed grid and does not tile. That is
  what makes 4096 a ceiling rather than a guess, since a larger photograph cannot grow it. The tagger's
  prompt is the cheaper of the two at **779**. `v0.19 review/R4`'s own figure -- *"a 7,440-byte
  briefing"* -- was measured against a constant that no longer exists and was wrong by 3.4x
  (design.md D8).

  **The halt check ran and the pin held**: two existing inputs were re-captioned with the pin in place
  and both artifacts came back byte-identical to the ones on disk, prose and body alike. Pinning at the
  window already in force is the only value that leaves the models' output unchanged, which is the whole
  point of pinning rather than raising.

### Removed

- **The `vite` dev-server proxy, which the Host/Origin guard had just turned into a trap.**
  `ui/vite.config.ts` forwarded `/api` to `127.0.0.1:8517`, and `vite`'s proxy does not rewrite the
  browser's `Host`/`Origin`, so every call through it now answers `403 not addressed here`. Nothing
  tracked in this repository references `npm run dev` or port `5173`: the config was dead, and dead
  config that 403s is worse than none. `isekai ui` builds and serves the bundle itself.

### Fixed

- **The approved-sheet refusal says what `--new-version` actually buys.** It told the operator to
  *reopen* the input, but `review --new-version` leaves the approved artifact in place, so
  `approved_path` stays set and this page keeps serving the sheet read-only -- the reopened draft is
  the command line's to edit until the re-opened state lands in v0.22.2 (design.md D5). The command is
  still the remedy; the sentence no longer promises an effect the surface does not have.
- **An unreachable endpoint is recorded `transient`, not `permanent`.** `_reported()` in `cli.py` turned
  every `URLError`/`OSError` from the transport into a `Refusal`, and `render()` wrote `permanent` for
  any `Refusal` it caught -- so a closed tunnel, a pod that went away, or a `--server` address typed
  before the tunnel was up left a record classified as one that would recur, on the one failure that is
  over the moment the pod comes back. `comfy_types.py` now declares `Unreachable(Refusal)`, `_reported()`
  raises it, and the one caller that writes a record branches on it. Everything that only *reports* a
  refusal is unchanged: the CLI still prints the same string and exits 1.

  **It classifies the failure; it does not buy a second attempt.** Rendering's budget is one, so the next
  pass is refused on the *count* whichever kind is on disk, and the operator's remedy is still deleting
  the record by hand -- what changes is the kind the filename carries and the sentence the refusal states.
  That is deliberate: `run-directory`'s own requirement is that a render which has failed once costs a
  person's attention rather than another attempt, and letting a resume spend a second time without a
  person is a spec delta and a spending decision, not a patch (design.md D11).
- **One flow's malformed sheet no longer costs its siblings their assembly.** `prepare()` assembled in a
  dict comprehension, so the first flow whose approved sheet could not be read took every other flow of
  that run with it -- after `prompt_artifact` had already written a permanent record into the broken
  flow's own directory. It now collects per flow the way `across` collects per photograph, returning what
  was assembled beside what refused, and `_generate` reports both together at the end.

- **Every command a refusal prints is one the parser accepts.** `refusal_for` emitted
  `` `python -m isekai {verb}` `` and `prepare()` emitted `` `python -m isekai review` `` and
  `` `python -m isekai approve` `` -- all without the `--flow` v0.16 made required on every stage verb,
  so copy-pasting the remedy a refusal states returned an argparse usage error instead of the fix. The
  flow is now threaded into `refusal_for` as an argument of its own rather than patched at call sites,
  which covers every caption and tagging budget refusal as well as the two in `generate.py`
  (design.md D10). `tests/test_resume.py`'s `AVAILABLE` list held the bare forms, which was the only
  reason `cli:refusals:refusal-names-the-remedy` passed; a new test parses what is printed with the
  parser that ships, so the scenario can no longer be stronger than the fixture bound to it.
- **An assembly failure names the directory the record is actually in.** `prompt_artifact` printed
  `prompts/<flow>/` against a layout that has been `<flow>/prompts/` since v0.16 -- input above, flow
  below -- so the one path in the message pointed at a directory that does not exist. `review.py` had
  it right and is now matched.

- **A manifest missing a dial, or naming a node the graph does not carry, is refused at load.** Both
  passed all six gate commands, rented the pod and uploaded the photograph before raising a bare
  `KeyError` out of `patch()` -- not a `Refusal`, so `across` never collected it and the rest of the
  batch died with it. The dial check is **role-conditional and never a flat list**: a flat one rejects
  `conjure-anime-wai`, which legitimately declares no identity adapter and no pose preprocessor
  (design.md D4). `ROLE_DIALS` in `foundation/flow.py` encodes what each role costs, including
  `hires_resize`'s `hires_scale`, which `_hires_target` reads unconditionally and no reader of `patch()`
  alone would see; `SAMPLER_DIALS` and `SECOND_PASS_DIALS` moved there with it, so the list `load_flow`
  validates and the list `build_graph` reads cannot drift apart. Both tracked flows pass unchanged --
  `summon-anime-wai` 11/11 nodes and 12/12 dials, `conjure-anime-wai` 7/7 and 9/9 -- so no flow file is
  edited and `manifest_digest` does not move.

- **`approved_path` is authoritative for whether a sheet may be edited.** The rail keyed on it and the
  form keyed on `draft is None`, so in the state `review --flow F --new-version` produces -- approved,
  with a fresh draft beside it -- the two disagreed and `put_draft` had no approval gate at all. The
  `PUT` went through. `ui/spec.md` already required otherwise, so this makes an already-false scenario
  true (design.md D5). **The re-opened rail status is `v0.22.2`'s**; no third status is added here.
- **An overlapping draft `PUT` answers `409` instead of committing out of order.** The page autosaves on
  a debounce, so two writes could be in flight at once and committed in whatever order the server
  finished them -- last write wins, where *last* was not the operator's last keystroke. The client
  echoes the `saved` it last received and the server compares it to the draft's own `st_mtime`, which is
  the only monotonic fact on disk: the draft carries no timestamp, no revision counter and no digest,
  and a `revision` field would change the artifact shape (design.md D6). A payload carrying no `saved`
  states no precondition and behaves as before. `useSheet.ts` gains the generation counter
  `useVocabulary.ts` already had, so a slow earlier answer no longer replaces a newer one's `budget` or
  `refusal`.

  **The counter governs those two and never `saved`.** Applied to the receipt as a whole it made the
  recoverable `409` a permanent one: the two overlapping writes the precondition exists for are exactly
  the case where the *earlier* receipt carries the *later* time, so dropping it left the client echoing a
  precondition the server had already moved past and refusing every autosave after it, with a banner
  blaming another tab that did not exist. `saved` is a monotonic fact about the file on disk, so it is
  taken whatever the generation and only ever forwards.
- **Approve stops when the write it waits for was refused.** `approve()` awaited `flush()` -- so the
  debounced `PUT` is on disk before the approve `POST` goes out -- but read nothing back, which was
  sound only while a refused `flush()` meant a network error. It now means `409` as well, so an approve
  on top of one would have built the artifact from the last draft that *did* land and unlinked
  everything typed after it. `flush()` answers whether the draft reached disk, and the refusal stays on
  the header line.
- **One unreadable photograph no longer kills the whole review batch.** `batch.py` called
  `image_dimensions()` unguarded and it exits via `sys.exit`, a `BaseException` that `across` -- which
  catches `Refusal` -- walks straight past; with two bad photographs neither was named. The same wrap
  already existed one module away at `generate.photo_resolution`.
- **The bundle is rebuilt when anything it is built from changes, not only its source.** `_is_fresh`
  compared `ui/src/` and `ui/index.html` alone, so a bumped dependency, an added vite plugin or a changed
  build script left the previous build being served, silently and with a green gate. It now compares
  everything under `ui/` **except the two ignored roots** — `dist/`, its own output, and `node_modules/`,
  which is fetched. Stated as an exclusion rather than as a list of build inputs, because that list was
  wrong twice: naming `vite.config.ts`, `package.json` and `package-lock.json` would still have missed
  `tsconfig.json`, which `vite` reads and which is in that directory today.
- **`npm run build` is bounded in time.** It can reach the network resolving a missing dependency, and
  an `isekai ui` that hangs with no port bound and no output is indistinguishable from one that died.
- **The hosted tag panel shows each tag once.** `OfferedTag` is `{tag, posts}` where `posts` is a pure
  function of `tag`, so a repeat was a byte-identical object carrying no information and a duplicate Vue
  key. **The local list is deliberately not deduplicated**: `ScoredTag` is `{tag, confidence}`, where
  two rows can legitimately differ, and narrowing it would falsify
  `ui:source:both-tag-lists-are-shown-raw-and-read-only` (design.md D7). Neither artifact on disk is
  touched.
- **`show` honours the flows root it is given, and refuses before it prints.** `run_view.rendered()`
  called `load_flow` with the module default, ignoring `Wiring.flows_dir`; and `report` was a generator,
  so a run holding a directory no flow answers for printed fifteen lines of record and *then* failed.
  `report` now returns its lines as a list, so *everything refusable is read before the first line is
  printed* is a property of the shape rather than a docstring asking the next editor to keep it so --
  and both callers drain it in full, so the laziness bought nothing and cost the ordering.
- **`Cmd+Z` matches either `event.key` or `event.code`.** Under a Cyrillic layout it produced
  `event.key === 'я'` and the branch did nothing; matching the physical key alone would have traded that
  for Dvorak, where `code: 'KeyZ'` is the key printed `;` and the key printed `Z` reports `code: 'Slash'`.
  Either test alone is partial, and both are available here precisely because a meta-modified Z emits no
  character -- which is what separates this from the Option bindings thirteen lines earlier, where
  `event.key` is unusable. This is that binding only -- `TagInput.vue`'s thirteen `event.key` branches
  are a keyboard re-work of their own.
- **One wrap around `image_dimensions`, in the module that owns it.** `shared/image.py` gains
  `dimensions_or_refuse`; the render path and the review surface had grown two copies of the same
  `SystemExit` → `Refusal` translation, with two wordings for one failure.
- **A dead guard is gone from `/api/tags`.** `if (posts := vocabulary.count(tag)) is not None` dropped no
  row -- `count()` returns `int` -- and read as though a fragment match might have no count.

- **A test that was true only in a clean environment.** `tests/test_ollama.py`'s falsification twin set
  `http_proxy`/`https_proxy` and never cleared `no_proxy` -- and `getproxies()` reads that too, so on a
  machine exporting `no_proxy=localhost,127.0.0.1` the twin took the direct route and asserted the very
  thing it exists to rule out. Both spellings are now deleted for the duration of the test.
- **A dead public function is gone.** `evaluation/labels.py`'s `load_records` had no reference anywhere
  in the repository but its own definition line.

### Security

- **`Host` and `Origin` are validated on every request the review surface answers.** Until now
  `grep -rn "add_middleware\|Origin\|TrustedHost" isekai/` returned **zero hits**: the loopback API is
  unauthenticated by design, so the browser's own origin rules are the whole of its protection, and
  neither half of them was checked. `create_app()` now takes the address it is bound to and refuses with
  `403` any request whose `Host` is not one of that port's loopback names — which is the entirety of the
  DNS-rebinding attack, where a page on an attacker's domain resolves that domain to `127.0.0.1` and
  talks to this port with the browser's full cooperation — and any request carrying an `Origin` that is
  not this server's own, which is the cross-site write. **Raised independently by four converge security
  stations, across v0.18, v0.20, v0.21 and v0.22**, and landed first in this version so that every later
  UI fix is tested behind the request path that ships. It is a middleware rather than a dependency
  because the static mount is not a route and would not carry one, and it guards all **seven** routes —
  `GET /api/fields` arrived at v0.21 and the module docstring still says six; that numeral is prose and
  belongs to `v0.22.2`'s sweep.

## [0.22.0] - 2026-09-22

### Changed

- **Five shared names leave `isekai/boundary/claude_cli.py` for `isekai/foundation/run.py`**, one version
  ahead of the arm they sat behind. `CliFailure`, `refusal_for`, `instructions_record` and
  `constant_record` are what `pipeline/caption.py` and `pipeline/tagging.py` reach that file for beyond
  the CLI itself; leaving them there would make the next phase's deletion a move *and* a rewrite in one
  commit. `foundation/refusal.py` cannot host them — its first line is *"the one refusal exception, in a
  module that imports nothing"* and the class needs `Kind` from `run.py`, which already imports
  `refusal.py`: a cycle. `run.py` already owns `Kind`, `record_failure`, `attempts` and `hashlib`, so all
  four land without a new import.
- **`CliFailure` is renamed `StageFailure`, with no compatibility alias.** The name says CLI and two of
  its three raising modules have no CLI in them: `tagging.py` raises it for an Ollama transport failure
  and `caption.py` for an Ollama reader failure. An alias is how an old name survives the version that
  existed to remove it, so the rename is done in one commit across production and the suite —
  `FakeReader.failure` in `pipeline/caption.py` included, which is production code in its own `__all__`.
- **`refusal_for` widens from a `CliFailure` to `(kind, detail)`.** It read exactly two attributes off
  its `failed` argument and nothing else, and the type was friction that one call site paid for by
  **fabricating** an exception purely to satisfy the signature — `tagging.py`'s `caption_wd14` built
  `CliFailure("permanent", str(failed))` from a `Refusal | OSError`, with the very same two values
  already spelled literally one line above for `record_failure`. The fabrication is deleted, and
  `caption_wd14` now holds no `StageFailure` reference at all.

- **Two flows replace three, and the `claude` arm goes with them.** `summon-v1` and `conjure-v1`
  selected that arm by declaring *no* `hosted` block at all, so it could not be removed without
  replacing them; `summon-open-v1` loses `sheet.briefing.md`, which moves a digest and so makes a new
  flow rather than an edited one. **A flow is never edited** — three directories were deleted and two
  created. `summon-anime-wai` carries `summon-open-v1`'s graph, schema and caption briefing byte for
  byte; `conjure-anime-wai` carries `conjure-v1`'s graph and schema byte for byte — all 21 fields,
  `eyelashes` among them — and a caption briefing that is a byte-identical copy of
  `summon-anime-wai`'s, because both flows now read the same model for the same purpose and a second
  authored briefing would be a second untested artifact. The names carry the base:
  `<verb>-<style>-<base>`, because the catalogue holds eleven untried checkpoints and `summon-anime`
  could not tell two of them apart.
- **The `hosted` block is deleted rather than shrunk, and a required top-level `model` replaces it.**
  `hosted` named a distinction — a model reached over a network to a third party, as against one over a
  socket to this machine — and only the second survives. A block whose name no longer distinguishes
  anything, holding a single key, is not a declaration. The key is `model` and not `reader` because one
  alias answers **both** prompts stage ① sends: the reader and the hosted tagger are built from it, and
  the tag prompt is unframed for exactly that reason. `MANIFEST_VERSION` goes 2 → 3, and the reason it
  stayed at 2 — that a bump would force an edit to two frozen directories — expires with those
  directories.
- **Flattening closed the misspelling path for free, and no new check was written.** The `hosted` block
  had no key allowlist of its own, so `{"sortr": "x"}` inside it loaded clean; a top-level key is
  guarded by the allowlist that already existed. That allowlist now runs **before** the missing-key
  check, because a misspelling fails twice at once and reporting the absence first names `model` — a
  key the operator did not misspell — sending him to add a second one rather than fix the one he wrote.
- **The loader validates the value, not only its presence.** A bare `str()` loaded `{"model": null}` as
  the Python string `"None"` and sent a run at an alias that cannot exist. It is refused by name now.
- **The structural rule stops counting.** *"A flow is five flat files"* becomes *a flow is flat, and its
  files are the manifest and its siblings* — named rather than tallied, because the count has changed
  once and a rule carrying a numeral goes stale. `sheet.briefing.md` leaves `SIBLINGS` and every flow;
  it has had no reader since v0.21. `len(SIBLINGS)` gains the assertion it has never had: the
  set-equality that guarded this rule shrinks on both sides at once, so it stayed green through the
  removal and would stay green through a silent addition.


### Removed

- **`briefing_text` is inlined at its one caller and deleted.** Its whole body was `return
  path.read_text()`; `pipeline/caption.py` was its only caller anywhere including the suite, so it was a
  one-line alias over a stdlib method carried for a single call site.
- **`claude_cli.ROOT` is deleted rather than rehomed.** It had no production importer at all — it was
  read only inside `instructions_record`, which now reads `run.DATA_ROOT.parent`. The two are the same
  path by construction: both are computed from a file at the same depth with the same three `.parent`
  steps, and `interface/wiring.py` already spells that expression as `REPOSITORY`. Its one outside
  reference, a `pytest.param` in `tests/test_package_paths.py`, goes with it — that file's parameter list
  evaluates at module scope, so leaving it would have been a collection error rather than a test failure.
- **`isekai/boundary/claude_cli.py` and `tests/test_isolation.py`.** Thirteen names die with
  `ClaudeReader` — `BINARY`, `BASE_FLAGS`, `Runner`, `spawn`, `require_binary`, `invoke`, `Envelope`,
  `classify`, `classify_text`, `detail`, `models_that_ran`, `TRANSIENT_MARKERS`, `DECLINED` — every one
  unreferenced once the reader goes. The isolation file is deleted **whole** rather than having its
  third test rehomed: its own docstring is the argument, *"the obvious form of this test passes
  vacuously, and that is the whole reason this module exists separately"*, and with one arm the sealed
  form **is** the vacuous one. Retiring a guard deliberately is different from losing one.
- **Both reader registries, and the default they fell back to.** `DEFAULT_IMPLEMENTATION`, `READERS`,
  `HOSTED_TAGGERS`, `_resolve` and `_named_by` are gone: with one implementation there is no string to
  key a registry on, and a one-entry registry is a dispatch mechanism with nothing to dispatch.
  `reader_for` and `hosted_tagger_for` read `flow.model` directly. The table's recorded justification —
  that a conditional would hand an unrecognised name the default arm and corrupt any later comparison
  between the two — is **rewritten rather than carried**, because its premise was the second arm. What
  survives is that a manifest naming a model this build cannot reach still refuses by name, at the
  first call.
- **Six scenarios, and one of them would otherwise have been left bound to nothing.**
  `caption:selection:no-path-reaches-another-implementation` had exactly two bindings, both in the file
  this change deletes, and it is not merely unbound but **unprovable**: there is no other implementation
  for a path to reach. This repository has no spec↔test binding checker, so nothing in the gate would
  have reported it. Two further scenarios keep their keys and lose a clause —
  `caption:seam:producer-names-the-implementation` and `caption:failure:decline-is-permanent` each
  asserted something a one-armed system cannot fail.
### Documentation

- **The live documents stop claiming a subscription this pipeline does not need.** `README.md`'s
  banner said two of three flows read and sort through the `claude` CLI and so needed that binary and
  an Anthropic subscription; the system-dependency table listed three binaries; the provisioning block
  told an operator to `ollama pull qwen3:8b` and then explained, at length, why the command it had just
  given was no longer used. All of it is rewritten for one arm. The test applied throughout was **does
  this sentence claim something untrue of the running system**, not *does the word appear* — so
  `openspec/changes/archive/`, `CHANGELOG.md`'s released sections, `ui/design/` and `CLAUDE.md`'s own
  filename keep both words, and every remaining live mention is a past-tense record at the site it
  explains.
- **The scrub was scoped to two words, and the third one is what it missed.** The pass above tested
  *Claude* and *Qwen*; `hosted` was not on the list, so `isekai/boundary/wd14.py`'s module docstring
  went on saying that `ollama.py` *"exists only where a flow's manifest declares a `hosted` block"* and
  that the two taggers are not one Protocol because *"the registry that would key it is keyed on
  `hosted.implementation`"*. This change deleted both — the loader now refuses that block and there is
  no registry left to key. The paragraph now makes the argument its sibling in
  `isekai/pipeline/tagging.py` was rewritten to make: the hosted tagger resolves on the required `model`
  key and therefore runs for every flow, the local one through no manifest key at all, and a Protocol
  whose two implementations resolve through different mechanisms is a shared name rather than a seam.
- **`README.md`'s quickstart no longer contradicts itself seven lines apart.** Step 1 said *sort the
  prose into a sheet of canonical tags* and then, below, *the local list is what fills the sheet*. The
  first was true until v0.21 and was missed by that version's converge.
- **`scripts/joycaption.Modelfile` stops calling `qwen3:8b` "the sorter, stage ②" in the present
  tense.** That sentence was false before this change, not after it: v0.21's phase 6 corrected
  `README.md` and `CLAUDE.md` and missed this file. Its header also named `summon-open-v1` as the flow
  that calls the model it builds.
- **`CLAUDE.md` gains this repository's first flow naming rule**, `<verb>-<style>-<base>` with `-v2`
  only for a second generation of the same triple. What was recorded before was an *identity* rule —
  that a changed digest is a new flow — which forces a new identifier without saying what one looks
  like, and that gap is what produced `summon-open-v1`: a name describing the **arm** rather than the
  flow, deleted by this change for that reason. The base is in the name because the catalogue holds
  twelve candidate checkpoints of which eleven are untried.
- **`CLAUDE.md`'s capability count was wrong for the third time**, saying eleven where the directory
  holds twelve. The clause telling a reader to count `openspec/specs/*/` rather than trust the sentence
  is kept and now records all three misses, which is the whole argument for the clause.
- **Four `**Source:**` headers in the living spec pointed at files this change deletes** —
  `isekai/boundary/claude_cli.py`, `flows/summon-v1/`, `flows/summon-v1/sheet.briefing.md`. They are
  capability metadata above `## Requirements`, not requirement text, so correcting them is not a fold;
  the requirement and scenario bodies are left to the delta and to release.
- **The acceptance ran on a pod and the claim held — both flows, five photographs, ten renders,
  15m08s.** v0.19's isolation proof inverted: there is no second arm to prove separation from, so what
  was shown is that the one arm is **complete**. `caption` → `sheet` → `ui` → `generate` for
  `summon-anime-wai` and `conjure-anime-wai` over one set of photographs, two reviews, no refusal and no
  manual repair at any stage. **The operator's verdict was yes for both flows**, on the first ten renders
  the pod produced.
- **The router placed 118/160 tags (73%) for `summon` and 124/160 (77%) for `conjure`**, against v0.21's
  73% over eight photographs — and the tag table, its deriver, its router and its tests were **not
  touched** by this version. The rate not moving is the negative result that matters: retiring the arm
  changed nothing about what the router can place.
- **`conjure-anime-wai`'s five face-only fields were filled by hand in 7 of 25 cells.** That flow has
  neither an identity leg nor a pose leg, so the face reaches the render only as tags, and `eyelashes` —
  the field this change argued about keeping rather than dropping — is among those filled. Keeping it
  cost nothing at runtime, as predicted; dropping it would have forced a table regeneration. The
  prediction is now measured rather than reasoned.
- **Pod `r8gcl050ob1dox`, RTX PRO 4500 Blackwell, EU-RO-1, torn down and confirmed gone.**
  `infra/down.sh` reported billing stopped, and the RunPod MCP confirmed it twice — `list-pods` returned
  `pods: []` and `get-pod` returned `404 pod not found`. **The GPU cost is unposted rather than zero**:
  RunPod had posted only the network volume's `storageStandardAmount: 0.0117` for the day when this was
  written. At v0.21's implied rate 15m08s is ≈$0.21. Recorded as unposted because a figure read off a
  lagging ledger and reported as final is not a measurement.



## [0.21.0] - 2026-09-21

### Added

- **`field-map` — one authored `tag ↔ field` table, read in two directions.** `scripts/field_map.json`
  assigns each tag in the pinned vocabulary a **primary** criterion — the one a router writes it to —
  and any further criteria it may be **browsed** under. It is **one data structure with two indexes**:
  the cheatsheet is the table read `field → tags`, the router is the same table read `tag → field`, and
  **the reverse index is computed in `isekai/shared/field_map.py` and never stored**, because two copies
  of one mapping is two things to keep true. It sits in `scripts/` beside `vocabulary.json` rather than
  in a flow's schema: `twintails` answers *hair silhouette* in every flow that declares that field, so
  the assignment is a property of the **vocabulary** and not of a schema — and fixing one tag's criterion
  is one edit here rather than three digest-frozen flow directories.
- **A tag has exactly one primary and may sit in several groups.** The earlier rule — *no tag appears in
  two field groups* — is falsified by the operator's own approved sheets, which file `navel` under
  `clothes`, `pose` **and** `body_shape`, `collarbone` under `pose` and `body_shape`, and `standing`
  under `framing` and `pose`; a structural case is worse, since `lips` is a declared field of its own on
  `conjure-v1` while it is part of `expression` on `summon-v1`. Routing needs one answer and browsing
  needs all of them, so the table carries both and the check becomes **exactly one primary per tag**
  (design.md D4).
- **The loader raises all four checks, and eleven bound tests prove them.** The spec scenarios say
  *loading it is refused*, so a check living only in a test would implement nothing: every tag resolves
  in the pinned vocabulary · every tag has exactly one primary · the excluded list and the union of every
  group are disjoint · **every field any tracked flow declares has an entry**. The field list for that
  last check is read from the flows' own `Schema` objects rather than from a constant — a hardcoded
  twenty-one would stay green while a schema moved underneath it. `shared/` importing `foundation/` for
  it is not a new edge: `shared/fields.py` already imports `Schema` from `foundation/flow.py`.
- **An empty group is legal and an absent entry is not.** Over the eight-photograph v0.20 batch `age_band`
  and `marks` were approved **zero** times, `age_band` has no candidate in the vocabulary at all, and
  `eyelashes` holds four tags in total. A criterion the tag list cannot express is a fact about the
  vocabulary, and the table is the right place to say so; an absent entry, by contrast, is
  indistinguishable from one nobody has authored yet (design.md D9).
- **The table carries its own `revision`, a monotonic integer, and reports a `sha256` of its own bytes.**
  Unlike `scripts/vocabulary.json`'s entries there is no upstream revision to name — the artifact is
  authored here — so a consumer can record which revision routed it and two sheets filled under different
  revisions are distinguishable from the record alone. **This phase ships `revision: 1`.**
- **The ten suffix-carrying criteria are populated mechanically; the eleven without a suffix are present
  and empty until the next phase.** The rule that reproduces the record's group sizes is *tag equals the
  suffix, or ends in `" " + suffix`* — not substring, which gives `hair` 265 rather than 103. Sizes
  against the pinned 8,106: `hair` **103** · `eyes` **55** · `background` **47** · `skin` **23** ·
  `bangs` **15** · `lips` **13** · `nose` **12** · `eyebrows` **9** · `eyelashes` **4**. **281 primaries
  across 21 criteria.**
- **The `hair` group is one derived set serving two fields, split by a colour test.** `hair_colour` and
  `hair_silhouette` both declare the suffix `hair`, so both derive the identical 103 tags — right for the
  cheatsheet and impossible for the router, since `long hair` must have one primary. A `hair` tag whose
  non-suffix words contain a colour word takes `hair_colour` (**26**), every other takes
  `hair_silhouette` (**77**), and **both fields list all 103** so nothing is hidden from browsing. The
  operator's own sheets prove the split separates cleanly — `brown hair ×5`, `blonde hair ×2`,
  `black hair` against `long hair ×7`, `wavy hair ×6`, `straight hair ×2`, `medium hair` (design.md D16).

- **`scripts/derive_field_map.py` — the authoring aid, stdlib and offline.** The route the roadmap
  credited to Danbooru's `search[name_matches]` wildcard needs no Danbooru at all: **a wildcard
  intersected with the pinned vocabulary *is* a match against the pinned vocabulary**, and the 240
  candidates the API would return are the 74% that get thrown away (design.md D15). The script reads
  `models/wd14/selected_tags.csv`, expands a seed list per criterion, resolves one primary per tag and
  rewrites the table; `--report` prints what every seed pulled in, so the operator's pruning pass sees
  the junk rather than inheriting it. **Every input it reads is tracked or pinned**, so re-running it
  leaves the file byte-identical on any machine: the 113 filings the operator made over the v0.20 batch
  are transcribed into a `FILED` constant, exactly as the dead briefing's 41 examples already were, and
  the gitignored runs they came from are read by `--refresh` alone — which prints the drift between the
  constant and the sheets on disk and writes nothing. Reading them at derivation time would have made
  the committed table reproducible on exactly one machine: without them 17 tags change or lose their
  primary and `accessories` empties.
- **Matching is word-boundary against a stem and its inflections, not `in` and not the bare boundary.**
  Substring is the defect the roadmap flagged — `scar` matches `scarf`, and `\bscar\b` takes 44 matches
  to 15. But the roadmap's own remedy introduces a second one: `\bbraid\b` alone loses `twin braids`
  153,036 and seven more. And plurals alone leave **12 of the operator's 113 approved tags unreachable**
  — `pulling` from `pull`, `licking` from `lick`, `lifted by self` from `lift` — so `-s/-es/-ing/-ed`,
  the drop-`e` case and consonant doubling are all handled and **seeds are written as stems**.
- **The record's one verifiable number reproduces, and it is 57 rather than 63.** The seven seeds at
  `notes/v0.19_improvements/ui.md:575` reach **59** tags, **57** of them beyond the 103-tag suffix
  group. 63 is the *substring* number, and the whole difference is **six tags, every one junk**:
  `playboy bunny` 82,752 · `reverse bunnysuit` · `nontraditional playboy bunny` · `setsubun` ·
  `male playboy bunny` · `bunny day`, all from the seed `bun`, and `\bbun\b` matches none of them. All
  three figures — 59, 57 and the six — are asserted so a later change to the matcher cannot move them
  silently.
- **Seven criteria are seeded, and they are larger than the brief said.** Measured against the pinned
  8,106 from the stem lists alone: `clothes` **1,411** · `pose` **788** · `background` **235** ·
  `body_shape` **196** · `expression` **132** · `framing` **40** · `gaze` **23**. The brief's
  *"`clothes` is 900 tags from 20 seeds"* and *"63 seeds reach 2,126 tags"* both understate it — seven
  criteria alone exceed the figure claimed for twenty-one. That makes design.md D7's decision to cut
  nothing **more** consequential and does not change it: a `>10,000` cutoff still hides 10 of the 113
  tags the operator approved.
- **The dead briefing is harvested before it stops being read.** `flows/conjure-v1/sheet.briefing.md`
  names **41 example tags across ten criteria** — `framing` 8, `bangs` 6, `count` 4, `lips` 4,
  `facial_hair` 4, `gaze` 4, `skin_ancestry` 3, `eyebrows` 3, `nose` 3, `eyelashes` 2 — and it is the
  only authored group content that exists anywhere in either tree. This version carries that file dead
  (design.md D22), so the content is taken out of it now.
- **One primary per tag, decided in three steps.** The operator's own filings decide first, because a
  tag he approved and then rendered is render-tested and no ordering is; they settle **22** of the
  **301** collisions. A declared precedence order — `gaze > clothes > pose > body_shape > expression >
  framing > background`, then the suffix criteria — settles the rest. It is a tie-break and not a claim
  to be right: eleven of the seventeen filed collisions is the ceiling for any of the 5,040 orderings of
  the seven and 210 of them reach it. **Phase 8 overrides individual tags.**
- **Every criterion that loses a tag keeps it under `also`.** So `navel` still appears under `clothes`,
  `pose` and `body_shape` in the cheatsheet and routes to exactly one, and both hair criteria browse all
  103 while only one routes each tag. Measured against the ten approved sheets on disk: **all 113
  distinct approved tags are reachable in every field they were approved in, 0 unreachable** — asserted
  as a test rather than claimed.

- **`GET /api/fields` and the cheatsheet overlay — `Option+Space`.** The measured gap it closes is not
  ranking and not speed: the operator looks at a photograph, goes to type a tag, and **does not know
  what Danbooru calls the thing he is looking at**. The autocomplete cannot help, because it needs a
  fragment he already has and a fragment that matches nothing commits nothing — so the failure is a
  dead end rather than a bad tag. The endpoint answers the **whole table in one response** for the
  acting flow, tens of kilobytes, so the overlay's filter is instant with no round trip per keystroke
  and a sitting that never opens the reference pays nothing. Riding `/api/batch` was rejected — it
  would tax every page load for a surface that may never open (design.md D13).
- **The overlay is read-only, cuts nothing, and introduces no new component, colour, space or type
  step.** Clicking a tag does not insert it: inserting would make a reference surface own a target
  field and commit into it. It composes `PhotoOverlay`'s ground — the same `Teleport`, the same
  `.overlay` block below the app header, `.overlay__controls` / `.overlay__exit` / `.overlay__foot`,
  `.source__head` + `.kicker`, `.row__tags` + `TagChip`, `.input`, `.drop__posts`. Not `.dialog`,
  which no component references and which caps at `min(440px, 100%)` — wrong for a four-figure group
  (design.md D12). A declared criterion the table holds nothing for shows **nothing here** rather than
  vanishing, and the filter never removes a group heading.
- **`Option+F` opens the photograph from the keyboard**, so the lens the operator already had stops
  needing the mouse.
- **Both bindings match `event.code` and both call `preventDefault()`** — the rule this version put in
  `CLAUDE.md`, and the first `event.code` matches in this repository. `preventDefault()` is
  load-bearing twice: U+00A0 into a tag field is the silent dead end the feature exists to remove, and
  Space is the **native activation key** of a focused `<button>`, which this app focuses on mount.
- **The focus round-trip, which both keystrokes need.** On open the criterion is remembered and the
  field blurred; the lens's own filter takes the focus. While a lens is open `TagInput` **yields**
  Escape and the arrows, so `Esc` closes the lens rather than clearing a fragment behind it and
  `←`/`→` do not double-fire. On close the field is restored — and the fragment survives untouched
  because `TagInput` stays mounted behind the lens, so nothing is copied out and copied back and
  nothing can come back different. Without this, `PhotoOverlay`'s printed *"Editing is suspended …
  the sheet is behind this, untouched"* was **false** (design.md D11, D27).
- **Three corrections in the same files.** `PhotoOverlay`'s `step` emit is **declared and never
  emitted**, and `ReviewApp` bound it — dead code that read as the mechanism; both go.
  `SourcePanel`'s `'click to fill window'` asserted click is the only route and now names `⌥f`.
- **Neither keystroke is proven by any check in this repository.** There is no browser test runner
  here and the gate's whole browser half is `vue-tsc --noEmit` over the *source*. The four
  `ui:cheatsheet:*` scenarios are server-side and are proved in `tests/test_ui_api.py`; the keystrokes
  and the overlay's behaviour are verified by the operator in a named human phase, and a green gate on
  this phase is **not** evidence they work (design.md D10).

- **The acceptance passed, on eight fresh photographs.** `caption` → `sheet` → `ui` → approve on
  `summon-open-v1`, all eight approved. **Measured, with no pass mark set** (design.md D2):

  | | |
  |---|---|
  | WD14 offered | 309 tags · 38.6/photo |
  | the router placed | **226 · 73%** |
  | of those, survived review | **204 · 90%** |
  | approved | 225 · 28.1/photo, of which **21 typed by hand** · 2.6/photo |

  For the figures this change was cut against: Qwen supplied 33.5% of the approved sheet at **56.3%**
  precision and **6.5 deletions** a photograph. The router is at **90%** and **2.6**. There is no
  like-for-like baseline — D2 retired it as circular — but both numbers clear the arm it replaced.
- **The operator's verdict, on the three sub-claims.** ① *the router* — "the tags land in the right
  field, 1–2 edits per sheet." ② *the cheatsheet* — "works well and helps indeed"; `Option+Space`,
  `Option+F`, the filter and the focus round-trip all behave, **and none of them is proven by any check
  in this repository** (design.md D10). ③ *coverage* — recorded above, for v0.22 to read.
- **The eight were rendered on a pod, outside the change's phases and at the operator's explicit
  request.** `tasks.md` marks no phase ⚠️ GPU and phase 9 requires no render; this was an operator
  session, recorded here so *"money: zero, every phase"* stays true of the **phases**. 21m36s on an
  RTX PRO 4500 Blackwell, ≈$0.30, all eight downloaded before teardown, `infra/down.sh` run and the
  RunPod MCP confirming `pods: []`. **`no bra` and `no pants` rendered as intended** — the failure
  `CLAUDE.md` records for absence clauses did not reproduce, which is the first live evidence for
  design.md D24's claim that deleting the guard was a repair.

### Changed

- **The sheet comes from the tagger.** `isekai sheet` reads `<flow>/wd14/` instead of
  `<flow>/captions/` and routes each tag through `field_map.primary_of`. **It reaches nothing** — no
  model, no network, no free-text cascade — so the class of error the stage used to have is gone
  rather than guarded: a reader asked for a field structure can invent a tag that merely looks
  canonical, and it did (`light` and `dark` reached an assembled prompt past every guard), while a
  tagger whose output layer *is* the vocabulary cannot express a tag outside it. **Prose stays a
  reading aid** and stops being a machine input, so a failed reader no longer blocks a sheet it does
  not feed.
- **The router is a dictionary lookup and it does not call `map_phrase`.** The cascade's first act is
  not a pass — it is an absence guard, and swept over the whole provisioned vocabulary it drops **37
  of 8,106 canonical tags before pass 1 runs**, including `no bra` 93,761 and `no panties` 87,258,
  **both of which are in the operator's own approved sheets**. A router built on it would silently
  discard tags from the ground truth it is measured against (design.md D24).
- **An absent `wd14/` is a refusal naming `caption`.** A sheet with every field empty is legal and
  therefore silent, so writing one when the tagger never ran would hide the one thing the operator
  needs told. **This narrows `CLAUDE.md`'s rule** that a missing tag artifact is *an absent aid, never
  a refusal* to the **hosted** tagger, which contributes nothing to a sheet; the local one the sheet
  is filled from is a prerequisite (design.md D21).
- **The sheet's producer records what actually filled it.** `implementation: wd14`, `pinned: true`,
  and **both WD14 digests carried across from the tag artifact** rather than re-derived — those are
  the bytes that session was verified against. `briefing` goes, because nothing reads a briefing here
  any more, and `field_map: {name, revision, sha256}` arrives beside `vocabulary`, so two sheets
  routed by different revisions of the table are distinguishable from the record alone.
- **`BUDGETS["sheet"]` drops from 3 to 1.** A deterministic router has no transient failure for a
  second attempt to catch, which is exactly what `"wd14": 1` already records for the other local
  producer (design.md D29).
- **The sorter seam is unwired.** `Wiring.sorter`, `SORTERS`, `sorter_for`, `_claude_sorter`,
  `_ollama_sorter` and the CLI's `_seam(wired.sorter, …)` are gone; `DEFAULT_IMPLEMENTATION` and
  `_named_by` survive, because the reader and the hosted taggers still resolve through them.
  `Wiring` gains a `field_map` thunk beside `vocabulary`, memoised per invocation for the same reason:
  the table is held against the vocabulary at load, so reading it per photograph would re-run four
  whole-table checks for every input in a batch.
- **The suite fills a sheet with no double at all**, which is stronger than filling it with one.
  `tests/stages.py` gains the field map every test routes through and one helper that writes the tag
  artifact the stage reads, so forty-six call sites lost a `FakeSorter` and gained nothing. Both
  transports are rigged to explode in the routing test, on `tests/test_isolation.py`'s argument: a
  router that reached a model is caught rather than trusted not to.
- **`caption()` and `boundary/wd14.py` are byte-identical in the diff, and no flow is re-pinned** —
  `git diff main` over both paths and over `flows/` is empty, and `tests/test_flow.py`'s `PINNED`
  passes untouched. Verified rather than assumed.

### Changed

- **Phase 8 — the operator's pass, and it is deliberately one entry rather than a survey.** The seven
  seeded groups and the fourteen remaining criteria are **accepted as derived**: `clothes` 1,407 ·
  `pose` 672 · `background` 214 · `expression` 115 · `body_shape` 93 · `hair_silhouette` 66 ·
  `eye_colour` 49 · `framing` 27 · `hair_colour` 26 · `skin_ancestry` 25 · `gaze` 24, with `age_band`,
  `lips` and `marks` empty. **The table is `revision: 3`.**
- **`EXCLUDED` gains `photorealistic`.** It describes how the picture was rendered and not the person
  in it, so no identity criterion can hold it — and the router drops it either way. What the entry buys
  is the **record**: the absence is now a decision somebody took rather than a gap nobody had looked
  at. It lives in `scripts/derive_field_map.py` and not in the table, because the table is regenerated
  and a hand-edit to it would be erased by the next run. `realistic` 19,111 is the same kind of tag and
  appeared on all eight v0.20 photographs; it is deliberately **not** here, because one was named.
- **`lips` ships with zero primaries, knowingly.** All thirteen of its tags lose to `expression`'s
  `lips` stem, which is what the operator's own sheets say — he filed `lips` twice and `parted lips`
  four times under `expression`. The criterion browses all thirteen through `also` and routes none, and
  on `conjure-v1`, which declares `lips` as a field of its own, nothing will route to it. One
  vocabulary-keyed assignment cannot serve both flows (design.md D4); this is which way it was pointed.

### Removed

- **Both sorter implementations, and the seam they lived behind.** `Sorting`, `Sorter`, `FakeSorter`,
  `ClaudeSorter`, `OllamaSorter`, `output_shape`, `sorter_prompt`, `answers_from`, `SORTER_OPTIONS` and
  `SORTER_REMEDY` leave `isekai/pipeline/sheet.py`, with the **nine names it imported from
  `boundary/claude_cli.py`**. `CLAUDE.md` says a selectable implementation *"is removed only by the
  version that retires it"* — this is that version: with one implementation left, `implementation` for
  this stage would be a key that could hold one value, which the same rule calls not a declaration.
- **Ten scenarios, with their tests and their bindings.** Five `sheet:selection:*` describe choosing
  between implementations, refusing an unknown one, constraining each one's output shape, reading an
  answer out of a response body and naming a truncated one; `sheet:seam:offline-double-satisfies-the-interface`,
  `sheet:seam:structure-constrained-content-free` and `sheet:failure:structural-mismatch-is-permanent`
  describe a failure mode a deterministic router cannot have. **`CLAUDE.md:158` states there is no
  spec↔test binding checker**, so a marker naming a deleted scenario passes the gate green — every key
  was therefore grepped by name rather than trusted to surface.
- **`tests/transports.py`'s `sorted_answer`**, which built a sorter response envelope and now has no
  caller.
- **The free-text mapping cascade — twelve names, not the five the record listed.** `map_phrase`,
  `CURATED`, `CURATED_SPANS`, `_curated_pass`, `_index_of`, `contained_in`, `Vocabulary.words`,
  `Vocabulary.by_word`, `asserts_absence`, `_ABSENCE`, `_spans` and `_in_order` leave
  `isekai/shared/vocabulary.py`, and `fill()` leaves `isekai/pipeline/sheet.py` with them. There is no
  phrase to map: the four passes existed to turn a language model's free text into canonical tags, and
  a tagger's output is canonical on arrival — 8,069 of the vocabulary's 8,106 tags would terminate at
  the first pass and the other three would never run.
- **Deleting the absence guard is a repair as much as a retirement.** `asserts_absence` fired *before*
  any pass and, swept over the whole provisioned vocabulary, dropped **37 of 8,106 canonical tags**,
  `no bra` and `no panties` among them — both in the operator's own approved sheets. A prompt still
  carries no negation; what enforced it was a text rule on prose, and prose is no longer an input.
- **`normalise()` stays, and it is not a near miss.** It is called by `Vocabulary.__contains__`,
  `count`, `search` — the UI autocomplete, pinned by `ui:vocabulary:matches-are-ranked-by-post-count` —
  and `read_tags`, and by `isekai/shared/fields.py`'s `validate()` on the **approval** path, where it
  enforces the *written in the vocabulary's own spelling* refusal. A sheet's spelling refusal is
  unchanged by this version.
- **Six more scenarios, with 16 test functions (21 collected) and four more in `test_sheet_schema.py`.**
  Five `sheet:mapping:*` describe the cascade's passes; `sheet:purity:absence-clause-is-dropped` is
  implemented wholly by the guard that eats `no bra`, and after this change a canonical tag stream
  cannot contain a clause — so the scenario would be **unreachable** rather than merely unneeded.
- **Four of the five `sheet.briefing.md` tests.** One called `map_phrase`; three asserted sentences in
  instructions nothing follows. The fifth is kept: *every field name the briefing mentions exists in the
  schema* is still a real consistency check, and the file itself stays, unread, because `load_flow`
  refuses a flow missing it and deleting it would move all three flow digests.
- **`Field.suffix` now has no consumer anywhere in the tree.** Its only live read was `fill()`. The key
  stays in all three frozen `schema.json` files, because editing them means new flow identifiers
  (design.md D28), and `scripts/derive_field_map.py` authors its own suffix table rather than reading it
  — resurrecting the consumer to build the artifact that replaced it would be the wrong kind of tidy.
- **Not removed, and deliberately: `hosted.sorter`.** It is a *required* key of the manifest's `hosted`
  block (`flow.py:234`, read unguarded at `:429`, asserted by three tests), and dropping
  `"sorter": "qwen3:8b"` from `flows/summon-open-v1/flow.json` would move that flow's `manifest_digest`
  — which `CLAUDE.md` makes a **new flow identifier** rather than an edit. It is carried dead, unread,
  exactly as `sheet.briefing.md` is, and both have the same trigger: the version that deletes the flows
  they belong to (design.md D22).

### Fixed

- **The router dropped every multi-word tag, silently.** `boundary/wd14.py` stores the label index's
  own Danbooru spelling — `blonde_hair` — because `tagging`'s rule is that neither tag list is
  narrowed or canonicalised; the vocabulary and the field map are normalised at their own read.
  `route()` did a bare dict lookup between the two, so `blonde_hair`, `long_hair`, `brown_eyes` and
  `open_mouth` matched nothing and were indistinguishable from a tag no criterion claims. **Measured
  over the eight v0.20 photographs: 112 tags routed, 230 with `normalise()` applied — 118 lost**, and
  the survivors were the single-word tags, so a sheet still looked plausible while losing the
  identity-bearing half. The normalised spelling is what is written, because `shared/fields.py`'s
  `validate()` refuses a sheet whose tags are not in the vocabulary's own spelling.
- **The fixture encoded the bug.** `tests/stages.write_wd14` wrote space-spelled tags, so the whole
  suite was green on a case production cannot produce. The routing test now writes the underscore.

- **`CLAUDE.md` gains the `event.code` rule, with a corrected reason.** *An Option-modified keybinding
  matches `event.code` and calls `preventDefault()`, because Option is a character-producing modifier on
  macOS.* Not a layout rule: on plain US ABC, `Option+Space` emits **U+00A0** and `Option+F` emits `ƒ`,
  so an `event.key` handler inserts an invisible non-breaking space into a tag field — the silent dead
  end the cheatsheet exists to remove. `event.code` appears **nowhere** in this repository today, so
  v0.21's two bindings are the **first** such matches and not the second. `Cmd+Z` at `ReviewApp.vue:243`
  is recorded as a known live violation rather than fixed here.
- **Four sentences in `CLAUDE.md` that this version makes false.** *"a missing tag artifact is an absent
  aid, never a refusal"* narrows to the **hosted** tagger. *"prose first because it is the only one
  anything downstream reads"* — it is the WD14 list, and the ordering stays as it is for the reason it
  was chosen. *"ten capabilities today"* was already stale: `ls -d openspec/specs/*/` returns **eleven**
  since `0020` archived, and this change's delta makes it twelve only when it is archived. And the seam
  paragraph now reads the rule the other way — stage ② has no seam because there is nothing left to pass
  through the parameter.
- **The call-graph sentence, corrected past what the record predicted.** D29 said deleting `ClaudeSorter`
  would leave `caption.py` the sole `pipeline/` importer of `boundary/claude_cli.py`. It does not:
  `tagging.py` imports `CliFailure`, `constant_record` and `refusal_for` from it and has since v0.20.
  `CLAUDE.md` names **two** importers.
- **`CHANGELOG.md`'s `[0.18.0]` entry claimed a suffix-anchored `Space` picker that never shipped.** The
  feature lived on a prop named `hint` and was deleted in **`8aa6fb0`, *"feat(ui): rework the keyboard
  model"*, an ancestor of the `v0.18.0` tag** — introduced and removed inside one version. It could not
  have worked either: `ui/app.py` sends `list(batch.flow.schema.names)`, names only, so a field's suffix
  has never reached the browser in any version. The entry is **corrected in place, not deleted**.
- **The design documents written around *"the sorter is mediocre"*.** `ui/design/README.md`'s brief,
  its ② draft-diff and caption bullets, `ui/design/states.md`'s screen descriptions, and
  `ui/design/ux-flow.md`'s claim that *"out-of-vocabulary tags only arrive from the sorter"* — that
  refusal kind is now **unreachable** and is kept as a guard on a future producer rather than as a state
  this surface can reach.
- **`ReviewApp.vue` said `draft from the sorter` on screen.** It says `draft from the tagger`.
- **The group `README.md` files, `README.md` and `boundary/ollama.py`'s docstring.**
  `isekai/shared/README.md` gains `field_map.py` with its importers; `isekai/pipeline/README.md`'s
  `sheet.py` row costs **free** rather than *a model call*; `isekai/interface/README.md` stops naming a
  sorter in `wiring.py`; `README.md` says the local tag list is what fills the sheet, and that
  `ollama pull qwen3:8b` is no longer used by any stage. `CLAUDE.md`'s `scripts/` paragraph gains
  `field_map.json` and `derive_field_map.py` — the first tracked artifact there that is **authored**
  rather than fetched, which is why it carries its own monotonic revision.

## [0.20.0] - 2026-09-21

### Added

- **The gate gains a sixth command — `bash scripts/typecheck_ui.sh`, the browser half.** The Vue
  frontend has no automated tests of any kind, and `vue-tsc --noEmit` was declared in
  `ui/package.json` and named by no gate command, so a phase whose whole product is browser code
  could end green while the bundle did not compile. It sits beside `uv run ty check` because it is
  the same axis in the other language, and it is added **before** any browser code is written so
  every later phase runs under it (design.md D22). It is a script rather than a bare `npm run`
  because the array's entries run from the repository root and because a missing `ui/node_modules/`
  has to refuse **by name** — `isekai/interface/ui/bundle.py`'s shape, say what is absent and what
  installs it — rather than exit 127 with `vue-tsc: command not found`. `npm install` is still never
  run for you: it fetches third-party packages, which is why `ui/node_modules/` is an ignored root.
- **`.github/workflows/ci.yml` restores that toolchain, and it is the only place that does.** CI
  invokes `make gate`, so the sixth command would refuse on a bare checkout. A `setup-node` step and
  an `npm ci` from the tracked `ui/package-lock.json` install exactly the pinned tree — deterministic,
  and failing rather than resolving a new one. The gate array's four mirrors — the array,
  `Makefile`, `README.md` and CI — are updated in this one commit, as the contract requires.
- **A `tagging` extra — `onnxruntime`, `numpy`, `Pillow`.** Deliberately **not** the `eval` extra,
  which resolves the same three names and also carries `torch` and `transformers`: roughly 2 GB the
  local tagger never imports, which would make the cheap half of stage ③ cost the expensive half's
  download (design.md D19). The `ui` extra is the precedent for a narrow one. `dependencies = []`
  does not move, `uv.lock` gains only the extra's own three entries because the pins already
  existed, and the three stdlib-only runtime guards still pass under `python -S`.

- **Two stage directories and two budgets, in `isekai/foundation/run.py`.** `WD14 = "wd14"` and
  `TAGS = "tags"` join the layout names, between `CAPTIONS` and `SHEETS` — the order a run passes
  through them. The run owns the layout, so the two tagging stages name their directories the same
  way every other stage does, through `run.directory(flow, CONSTANT)`.
- **`BUDGETS` gains `"wd14": 1` and `"tags": 3`, split on the axis every other entry is split on.**
  The hosted tagger is a model over HTTP and is flaky exactly as `caption` and `sheet` are, so it
  gets their three; the local tagger is a deterministic matrix multiply against a digest-verified
  file, so a second attempt cannot succeed where the first failed and it gets `assemble`'s and
  `render`'s one. This is not bookkeeping: `BUDGETS[stage]` is a bare dict lookup and both
  `across()` and `main()` catch only `Refusal`, so a stage with no entry would escape as a raw
  traceback in a package where every failure is named (design.md D6). Sharing `caption`'s entry
  would have worked and would have made the refusal say *caption failed permanently* about the
  `wd14/` directory.

- **`scripts/vocabulary.json` gains `wd14/model.onnx`** — same publisher, same revision as the CSV
  already there, 467,460,978 bytes, digest read from its LFS object id so pinning it costs no
  download. **The two are one artifact split in two**: row N of `selected_tags.csv` names output
  neuron N of the graph, so a pair from different revisions mislabels every tag — silently, because
  the vector has the right length and every name in it is a real tag. A test asserts both entries
  resolve one revision of one repository, and a second asserts a mismatched pair fails it.
- **`scripts/eval_licences.md` gains a record for the model**, read and dated on its own rather than
  inherited from the CSV's row above it: Apache-2.0, the same grant, re-read 2026-09-20. The
  section that said *"the tagger it is published beside is not pinned and is not loaded"* is
  rewritten rather than left standing.
- **Two guards on `scripts/manifest.py`'s `digest_of_url`, one of which fired during this phase.**
  Twice, a connection dropped mid-body and the partial read was hashed and written to the tracked
  manifest — 143049 and 64311 bytes of a 308468-byte file, each a real SHA-256 over the wrong bytes.
  `curl` catches this and exits 18; `urllib` returns it without complaint. So a body shorter than
  the response's declared `Content-Length` is now refused naming the shortfall, and the request
  additionally accepts only the identity coding — latent rather than observed, and not subsumed by
  the first, because a coded response declares its *coded* length. `models.json` and
  `eval_models.json` are **not** re-derived here.

- **`isekai/boundary/wd14.py` — the local tagger's boundary, and the only module in the package
  that touches the `tagging` extra.** A `Session` Protocol whose real implementation is
  `OnnxSession` and whose double is what keeps the suite offline, the pad-and-resize preparation
  rule, the label index, and the two-digest verification. The arrangement `ollama.py` already has:
  the transport here, the adapter in `pipeline/`. **All three wheel imports are function-local**, so
  `python -m isekai`'s import graph stays stdlib-only and a test asserts none of them sits at module
  scope.
- **The label index is read in file order and nothing is dropped from it.** Row N of
  `selected_tags.csv` names output neuron N, so the vector is indexed **before** anything is
  filtered — character (category 4) and rating (category 9) rows are excluded from the *result* and
  never from the index. `shared/vocabulary.py` reads the same file and discards the order, which is
  correct for mapping a phrase and would be silently wrong here.
- **The pure half is separated from the half that needs a wheel, deliberately.** `select()` turns a
  probability vector into sorted tags and imports nothing; `prepare()` is the only place `numpy` and
  `Pillow` appear. The `tagging` extra is not installed in the environment the gate runs in, so a
  suite that could not test the ordering without it would be a suite that silently stops covering
  this capability. `test_wd14.py` runs with no wheel and no model file.
- **A vector whose length disagrees with the index refuses rather than zipping short**, which is the
  one mismatch that is otherwise undetectable: `zip` without `strict` would truncate to the shorter
  of the two and produce a quietly shorter tag list instead of a message.
- **Both digests are verified before 467 MB is opened**, through the scorer's resolver rather than a
  second copy of it — the repository's single enforcement site for the containment and digest rules.
  An absent half is a `Refusal` naming `bash scripts/download_models.sh scripts/vocabulary.json`; a
  half whose bytes disagree is left to `DigestMismatch`, whose message already names the file and
  both digests. A test proves the *model* is checked and not only the 300 KB list.
- **The input dimension is read off the session, not hard-coded.** A sibling tagger in the same
  family declares a different edge, and a constant would resize correctly against the one graph it
  was written for and silently wrongly against every other.

- **`isekai/pipeline/tagging.py` — `caption_wd14()` and `caption_tags()`, two functions and two
  seams.** Deliberately **not** one `Tagger` Protocol with two implementations: one resolves through
  the manifest's `hosted.implementation` and the other through nothing at all, so a shared name
  would be a shared name rather than a seam (design.md D3). Each has `caption()`'s guard against its
  own directory, its own `BUDGETS` entry and its own `latest()` check, so a complete caption and a
  complete WD14 list beside a failed hosted one is an ordinary resumable state.
- **`caption()` is byte-identical to `main`**, asserted by `git diff` rather than by a test. It is
  the one function in this change whose behaviour has to be provably unchanged, and a function with
  no edit is provably unchanged.
- **Nothing is narrowed.** Neither stage canonicalises, maps to the vocabulary, deduplicates or
  re-orders on anything but confidence. The hosted list is roughly three-quarters unusable — stock
  photo keywording, and it contradicts its own prose on the same photograph — and it is stored
  exactly as it came, because narrowing is stage ②'s job and seeing behind it is the point.
- **A response containing no comma is a permanent failure**, recorded like any other. That is the
  whole content check, and it separates *not a list at all* from *wrong*: the operator asked for the
  raw list knowing it is wrong, so wrongness is not what is being guarded. Anything richer starts
  filtering (design.md D15).
- **`constant_record(text)` in `isekai/boundary/claude_cli.py`, beside `instructions_record(path)`.**
  Digest only and **no `path` key**: `instructions_record` resolves a path and hashes the file behind
  it, which a producer whose instructions are a module constant cannot use, and a record that
  invented a path would assert a location that does not exist (design.md D16).
- **The WD14 producer records `pinned: true` and both digests** — the first artifact in this
  repository that can honestly claim a pin, and the first thing `show` will report without the word
  *unpinned* (design.md D17).

- **`isekai/interface/wiring.py` gains two tagging seams, and they are deliberately not one.**
  `tagger_for(flow)` takes a `Flow` and **reads nothing from it** — the local tagger resolves through
  no manifest key at all, because it is a file this build pins, it costs nothing, it reaches no
  network, and there is no flow for which it would be wrong. Requiring a key would have meant
  re-pinning three frozen flow directories to state an opinion none of them has.
  `hosted_tagger_for(flow)` answers `None` where a flow declares no arm this build can tag on, and
  that is the one resolver allowed to: `_resolve`'s argument — an unrecognised implementation must
  refuse rather than default — holds where a wrong model would silently produce a complete run whose
  provenance disagrees with the manifest, and here there is no wrong model to fall back to.
- **`isekai/interface/cli.py`'s `caption` branch says three times, in one order and no other.**
  Prose → WD14 → JoyCaption. `across()` catches `Refusal` per *input* rather than per stage, so the
  ordering **is** the failure isolation: the one stage with a port, a timeout and a retry budget runs
  last, and its refusal blocks nothing that would have succeeded (design.md D7). A test proves it —
  a hosted tagger rigged to fail leaves the caption and the WD14 list on disk and complete.
- **The local tagger is opened once per flow per invocation, not once per photograph.** The reader
  and the sorter are resolved inside the per-photograph loop because constructing one is
  constructing a dataclass; this opens a 467 MB graph and reads a 10,861-row index, so it is
  memoised beside the vocabulary thunk that exists for the same reason.

- **`run_view.STAGES` gains `WD14` and `TAGS`**, in the order a run passes through them —
  `(captions, wd14, tags, sheets, review, prompts)`. The tuple is explicit, so a new stage directory
  is invisible to `show` until it is named in it. By the standing rule that a version does not open
  files it never touches this would be out of scope, and **the rule does not apply**: v0.20 does not
  inherit this gap, it creates it, and shipping a stage `show` cannot see is shipping a verb that
  lies about what a run holds (design.md D23).
- **`show` prints a WD14 artifact without the word `unpinned` — the first one in this repository
  that it can.** `run_view.py` appends it for `pinned is False`, and every artifact in the tree
  recorded exactly that until now. A test asserts the absence *and* asserts the hosted tag list is
  still marked, so the absence means something.
- **A run captioned before these stages existed lists them empty rather than refusing.** No
  migration and nothing to detect: an old run simply lacks the two directories, which is the same
  state as a run whose caption has not been produced.

- **The source pane shows the caption one sentence to a block, and two read-only tag lists under
  it.** `sentencesOf()` joins `paragraphsOf()` in `ui/src/caption.ts` — the split is the browser's,
  because sending prose to the server to be split and back would be a round trip for a regex
  (design.md D10). It is **naive against abbreviations** and knowingly so: the prose is constrained
  by briefing to plain description of a person, and the acceptance names the edge rather than
  guarding it with a list of exceptions nobody can test.
- **WD14 first, JoyCaption second** — the order the pipeline produces them in, which also puts the
  usable list nearer the prose. WD14 chips carry the confidence to two digits, so `black hair 0.31`
  arrives under `brown hair 0.91` and refutes itself. JoyCaption chips carry the post count where
  the tag is in the vocabulary and **nothing where it is not**; the missing number is the mark,
  because a chip with no count reads as the model's word rather than Danbooru's.
- **Membership is decided server-side**, in `read_input`'s payload. `/api/tags` answers a *fragment*
  query and there is no membership endpoint, so marking N tags from the browser would be N round
  trips against a surface whose job is to be instant — and the vocabulary is already loaded in that
  process. No new endpoint; both lists ride on `inputDetail()`.
- **An absent tag artifact is `null` and draws nothing** — no panel, no message, never a refusal.
  Three legitimate absences (a run captioned before v0.20, a flow with no `hosted` block, a failed
  tagger), and a line explaining one the operator caused would be chrome on the busiest pane.
  `batch.py`'s startup refusal order does not change: nothing new can block the port being bound.
- **No new component, colour, spacing or type step** (design.md D21). Both lists are `TagChip` and
  `SourcePanel` already owned the column; the chip rows reuse `row__tags`, the sheet row's own
  layout, rather than restating a flex-wrap rule five pixels away from it.

### Acceptance — read live, on eight fresh photographs

Run through `caption` → `sheet` → `ui` on `summon-open-v1`, then rendered. The three claims were
recorded separately because they can fail independently, and one of them did.

- **④ — yes, unqualified.** *"Reading the caption one sentence made it easier indeed."* No sentence
  was reported split in the wrong place; the abbreviation edge the splitter is naive about did not
  appear in eight captions of constrained descriptive prose.
- **③a — WD14, yes, and it is the version's strongest half.** *"Works just awesome… better than
  expected,"* and *"the highest impact is the WD14 danbooru tags."* Every tag it returns is
  committable by construction, and the confidences made the wrong ones dismissible at a glance.
- **③b — JoyCaption, a qualified no.** *"The JoyCaption danbooru tags do not work really well…
  makes sense only for those that have a number in the chip."* The marking worked — the unusable
  ones were obvious — but obvious-and-present is still nine unusable rows in ten. D1's argument that
  *a wrong tag costs a glance* held for one wrong tag and not for nine, and the hosted list is now
  filtered to the vocabulary on its way to the page (design.md D29).

**③ earned its keep before the acceptance question was even asked.** Reading the panel against the
assembled prompt caught two stage-② defects at zero cost, with no pod running: `skin_ancestry: light`
and `eyebrows: dark` were reaching the prompt as the bare tags `light` and `dark` — both canonical
Danbooru tags meaning *lighting* and *darkness*, so they passed every guard and would have been
drawn, and `light, brown hair` would likely have encoded as *light brown hair*; and one sheet had lost
`1girl` from its `count` field. Four sheets were corrected and re-approved before rendering.

### Verified — the three artifacts end to end, on two synthetic portraits

Run on `synthetic_portrait_00003` and `synthetic_portrait_00035` through `summon-open-v1`, against a
throwaway runs root. Free: two local models on `127.0.0.1:11434`, one local ONNX pass, no render.

- **`caption` writes three artifacts and says three times**, in the designed order — *caption ·
  wd14 · tags* — 58 s cold for both inputs.
- **`show` lists `captions · wd14 · tags`, and the `wd14` line is the first artifact in this
  repository it prints without the word `unpinned`.** The other two still carry it, so the absence
  means something.
- **Re-running changes nothing and opens nothing**: six *already complete* lines, the run tree's
  content digest **and every mtime** identical, in **0.25 s** against the first pass's 58 s — which
  is the thunk working, since opening the graph alone costs ~0.9 s plus a 467 MB hash.
- **`summon-v1` produced two lines, not three** — `wd14/` present and `tags/` absent, because the
  flow declares no arm to tag on.
- **The measurements behind D1 reproduced on a photograph nobody had run them against.** WD14
  returned 44 general tags and recovered `1girl 1.00`, `solo 0.95`, `looking_at_viewer 0.69` and
  `navel_piercing 0.56`. JoyCaption returned 35, of which **4 are in the vocabulary** — the low end
  of the measured 9–26% band — and it answered `blue eyes` for a subject whose caption reads *light
  brown*, which is the contradiction D1 recorded, live.
- **The surface renders all three panes**: the caption one sentence to a block, the scored list with
  its confidences, the offered list with a post count on the four committable tags and none on the
  thirty-one that are not.

### Changed

- **The hosted tag list is filtered to the vocabulary before it reaches the page** (design.md D29),
  which overturns part of D1 on the acceptance's own evidence. It shipped unfiltered on the argument
  that *a wrong tag costs a glance*; at 4 usable tags in 35 the operator's verdict was that only the
  marked ones carried value. **The artifact is untouched** — it still stores every tag the model
  returned, because narrowing the record would make it disagree with what the model said. The local
  list stays whole, and the asymmetry is the point: WD14 is scored against the vocabulary it emits,
  so all of its tags are committable by construction. `OfferedTag` loses `in_vocabulary` and its
  `posts` is no longer nullable — every tag that reaches the page is in the vocabulary now.

### Fixed

- **`isekai ui` served a stale bundle, and nothing could have caught it but running the surface.**
  `ensure_built` returned any non-empty `ui/dist/`, so a bundle built by an earlier version went on
  being served while `ui/src/` had moved under it — with a green gate, because `npm run typecheck`
  compiles the source and the server reads the build, and nothing compared them. The gap dates from
  v0.18's on-demand build and was unobservable until now because **no version had changed `ui/src/`
  since**; v0.20 is the first in which a stale bundle and a fresh checkout disagree, which is
  `run_view.STAGES`'s case exactly — a defect made reachable rather than inherited (design.md D28).
  The bundle is now rebuilt when any source file is newer than the newest built file.
- **`baseline/build_contact_sheets.py` used `Image.LANCZOS`, removed in Pillow 10.** Exposed by this
  version's own `tagging` extra putting Pillow in the environment for the first time: CI never
  installs the extra so CI stayed green, but every operator following v0.20's setup instructions
  would meet a red `ty check`. Corrected to `Image.Resampling.LANCZOS`, the spelling
  `boundary/wd14.py` already uses.

### Changed

- **`README.md` and `CLAUDE.md`: `caption` produces three artifacts.** The run layout gains
  `wd14` and `tags`, `isekai/boundary/wd14.py` and `isekai/pipeline/tagging.py` join the layout
  paragraphs, `tagging` joins the extras, and `models/wd14/` is named as a pinned artifact the
  operator fetches — the tag list **and** the 467 MB graph it is the output layer of, at one
  revision.
- **Three stale counts, fixed by counting rather than by trusting the sentence.** `CLAUDE.md` said
  the living spec held *nine* capabilities and it had held ten since v0.18 — it now states ten,
  names all ten, and says outright that a capability enters the living spec on **archive**, so the
  number is always the count on disk and never the one a pending change implies. `isekai/README.md`
  said `boundary/` held 5 files against 6 and `interface/ui/` 4 against 3; both were wrong before
  this version touched either.
- **`pipeline/` is described as four verbs and five modules**, rather than making the count wrong in
  the other direction: `tagging.py` is a file in that directory and is not a verb. `CLAUDE.md`'s
  *"driven in four staged verbs"* is unchanged and still correct — v0.20 adds no verb.
- Each group `README.md` names its new file and who imports it, and `isekai/interface/README.md`'s
  one-line description of `wiring.py` names the two taggers beside the reader and the sorter.
- **The resume assertion now counts five doubles, not three**, and two of them are the taggers.
  A second pass that re-opened the graph would cost ~0.9 s a photograph while making no request, so
  an assertion that only counted network calls would have called that inert.
- **The `Session` seam takes the photograph rather than a prepared array** (design.md D26, a
  build-time correction to `tasks.md` 4.1). Built the other way the boundary tests pass and the
  **stage** is untestable: `caption_wd14()` would reach `prepare()`, which imports `numpy` and
  `Pillow`, which the gate's environment deliberately does not install — leaving
  `tagging:seam:offline-double-satisfies-the-interface` unprovable. Preparation goes behind the seam,
  where `ollama.Transport`'s precedent already puts request encoding. The cost is stated rather than
  discovered: `prepare()` is now reachable only through `OnnxSession`, so no gate command executes
  it and its acceptance is the live run.
- **`pyproject.toml`, `README.md` and `CLAUDE.md` stop saying the gate is five commands.** Three
  separate prose claims counted it; all three now say six.
- **`derive_vocabulary.py`'s docstring argued the opposite of what this version does**, in as many
  words: *"the tagger is not here: this repository does not run it… a manifest that carried both
  would make swapping the vocabulary a decision about a model nobody loads."* Rewritten to D18's
  reason, with the retired argument kept rather than deleted — it names the case the new rule does
  not cover.
- **The living spec's `model-provisioning:vocabulary:tagger-model-is-not-included` is retired, and
  inverted rather than dropped.** It forbade exactly this version's pin. Its successor,
  `label-index-and-model-share-a-revision`, is a strictly stronger claim: the old scenario permitted
  a `model.onnx` at any revision by any route and forbade only the manifest that could check it. The
  two tests bound to the retired key are rebound to the new one, not deleted. The change's
  `specs/model-provisioning/` delta was authored during the build; the cut omitted it (design.md
  D24).

### Fixed

- **`README.md`'s `isekai ui` section described the hosted tag list as phase 11 deleted it.** It said
  the pane shows the model's *raw* list *"with a post count on the tags the vocabulary actually
  carries and nothing on the ones it does not"* — the marked-but-whole list D29 replaced with a
  filtered one, written into the phase-9 entry before the acceptance overturned it. Those tags do not
  reach the page at all now, so an operator following that sentence would count four chips against
  thirty-five and go looking in `caption_tags` for a loss that never happened — where the artifact
  holds all thirty-five, exactly as `tagging:output:the-list-is-stored-unnarrowed` requires. The
  sentence now states the split the spec and D29 already state: the local list whole, the hosted list
  filtered to the vocabulary, and the filter on the way to the page and never on the way to disk.

## [0.19.0] - 2026-09-20

### Release notes — two things this version does not check, and hands to the operator

**① Read the first caption against the photograph.** Nothing here detects a reader whose vision
projector is missing. Such a model loads, reports no error, answers fluently and **describes nothing**
— it writes a plausible portrait because that is what the prompt implies, and a digest cannot catch it
because the file is the file that was pinned. After `ollama create`, `ollama show` must list `vision`
under Capabilities **and** print a Projector block; after the first `caption`, read the prose against
the picture. It is also the only check on the two briefings, which are **authored rather than ported**:
the prompt that produced the measured captions is gitignored and was never on this branch, and how an
8B fine-tune follows a long structured briefing is the untested variable of this version.

**② Pass an explicit `--seed` for any run meant to be compared.** Each flow draws its own seed, **even
at `--count 1`**, so the same photograph through `summon-v1` and `summon-open-v1` renders at two
different seeds and the difference between the two images is not attributable to the arms. This
version deliberately measures nothing and claims nothing about which arm is better; a comparison that
matters needs the seed fixed by hand.

### Acceptance — run live, on three photographs

**The open arm runs end to end and reaches Claude by no path.** Three of the operator's photographs
through `caption` → `sheet` → `ui`/`approve` → `generate` on `summon-open-v1`, on his own machine for
①② and one RunPod session for ④.

- **Stages ① and ② ran on localhost and cost nothing.** A cold caption takes ~21 s and a cold sheet
  ~25 s, the two models evicting each other between stages exactly as `design.md` D10 predicts — which
  is why one 900 s ceiling serves both rather than two tuned numbers.
- **Re-running every verb reports already-complete in well under a second** and makes no call. A model
  call could not hide inside that: the cold load alone is twenty times longer.
- **The briefings and the sheets were judged good by the operator.** The authored caption briefing — the
  named risk of this change, an 8B fine-tune against a long structured briefing — held.
- **`claude` genuinely absent from `PATH`, and a fresh caption and sheet were still written.** Running
  the already-complete batch that way proves nothing, because nothing calls a model on a resumed run;
  the evidence is a *new* run, from a copy of a photograph, into a fresh runs root. This is the real
  twin of the suite's monkeypatched isolation test.
- **Every artifact's `producer` names what produced it**: captions `ollama · joycaption-beta-one-q4k`,
  sheets `ollama · qwen3:8b`, and **`pinned` is `false` throughout** — which is what this version
  deliberately does not deliver.
- **Three PNGs rendered at an explicit `--seed 20190`** in 2 m 39 s total, downloaded before teardown.

**Cost.** Pod `q9q2h3qhkbywfo`, RTX PRO 4500 Blackwell in EU-RO-1, **7 m 50 s of uptime** against the
45-minute ceiling. Teardown confirmed by the RunPod MCP: `list-pods` returns `[]` and the pod id returns
404. The first creation attempt failed with a transient 500 and created nothing, so it billed nothing.

**This version measures nothing and claims nothing about which arm is better.** No comparison against
`summon-v1` was run; that is the next version's, and it needs the instrument that prices it.

### Added

- **`scripts/joycaption.Modelfile` — the open reader's `ollama create` recipe, recovered from the
  operator's live model because it was never committed.** The two-`FROM` projector pairing is
  undocumented in Ollama's own import and modelfile docs, and the model is a machine-local alias rather
  than a registry tag, so the recipe is the only thing that makes the name in a flow manifest mean
  something. It sits beside `models.json` and `download_models.sh`, where provisioning artifacts already
  live, rather than inside a flow directory — a flow is **five flat files** and that structural
  requirement is not weakened to house a file nothing reads.

  Recovered with `ollama show --modelfile`, and the recovery found one thing the on-disk original did not
  state: **`TEMPLATE {{ .Prompt }}`**. The quantisation ships no chat template, so Ollama passed the
  prompt through verbatim and every measured caption was produced under that default. The committed file
  states it, pinning the behaviour to the recipe instead of to a version of Ollama. The two `FROM` lines
  name the GGUFs by repository-relative path — **the `ollama show` output addresses them through the
  operator's own content-addressed blob store, and a real absolute path from the machine a run is on is
  not committed here.** Both forms build a byte-identical model: same two layer digests, same config
  layer `b507b9c2f6ca…`.

  Its header carries the two commands the release notes will repeat — `ollama create` for the reader,
  `ollama pull qwen3:8b` for the sorter — with both artifacts' sha256 and byte counts, their pinned
  source revision, and the silent failure to check for: a LLaVA-family model whose vision projector is
  missing loads, answers fluently and cannot see the photograph.

- **`tests/test_isolation.py` — the proof that a flow declaring one implementation reaches no name from
  the other, built so it cannot pass vacuously.** The obvious form of this test — monkeypatch
  `shutil.which` to `None`, as the absent-binary test already does — only fires if `require_binary` is
  *called*, so a run touching no Claude path is green **for the wrong reason**, which is precisely the
  thing under test. Instead `claude_cli.spawn` **and** `claude_cli.require_binary` are both replaced with
  functions that raise, and the open flow is run through both stages against them.

  **The falsification is resident rather than performed once by hand.** A second test points the same
  sealed fixture at `summon-v1`, which declares no `hosted` block and so resolves to the CLI arm, and
  asserts the seal fires. Without it the first test would stay green if the seal ever stopped sealing,
  and would go on looking like a proof. A third covers the failure path, where a fallback would be added:
  a permanent open failure records its kind, writes no artifact, and reaches no other implementation.

  This is the CI-resident twin of the operator's `claude`-off-`PATH` acceptance run, and strictly
  stronger than the PATH removal it stands in for.

- **A test in that module briefly reached the live Ollama on the developer's machine, and the fix is
  structural.** Monkeypatching `isekai.boundary.ollama.post` does nothing: `OllamaReader` is a frozen
  dataclass, so `ollama.post` is captured as an `__init__` default at class-creation time and the patched
  module attribute is never consulted. The failure is silent — the call simply goes to the real host. The
  transport is now injected at the seam the adapter declares for it, via `dataclasses.replace` on what
  `reader_for` actually returned, so the **resolution is still exercised and the socket is not**. Checked
  by running the whole suite with `socket.socket.connect` rigged to raise: **749 passed**, nothing opened.

- **`flows/summon-open-v1/` — the third tracked flow, and the first to declare a `hosted` block.** Five
  flat files, as every flow is. `graph.json` and `schema.json` are **byte-identical copies** of
  `summon-v1`'s, verified by `cmp`, and `flow.json` differs from that manifest in **exactly two places**
  — the identifier and the block naming `joycaption-beta-one-q4k` and `qwen3:8b`. The render is the same
  render; only the two hosted stages change.

  **Both briefings are authored, not ported**, because the prompt that produced the measured captions is
  gitignored and was never on this branch. The caption briefing carries `summon-v1`'s absence-licence
  paragraph **byte for byte** — licensing absence is what stopped a reader confabulating nineteen
  identity marks across seven of ten subjects, and a paraphrase would be an untested briefing wearing a
  tested one's reasoning. The rest is written for a reader that is handed raw bytes under
  `TEMPLATE {{ .Prompt }}` with no chat template: it opens on the shape of the one-sentence instruction
  that was actually measured, keeps its coverage list as prose rather than bullets so an 8B model does
  not echo the formatting back, and adds one sentence pressing on the skin, which is where the scored
  identity marks live.

  The sheet briefing ports both worked examples and all seven rules, and adds the two things Qwen3-8B was
  measured getting wrong: **write the whole label, not the bare adjective** — `blonde hair`, not
  `blonde`; `brown eyes`, not `brown`, which was 68 of 88 out-of-vocabulary tags — and do not repeat a
  phrase within a field, which is the failure `repeat_penalty` also guards.

  **The flow is pinned by whole-directory digest** at `e035d227…`, the designed cost of adding a flow.
  And one assertion closes the last hole `design.md` D12 names: an absent `hosted` block has no key for
  the allowlist to refuse and a digest cannot tell a correct manifest from a wrong one, so
  `load_flow("summon-open-v1").hosted.implementation == "ollama"` is asserted directly — verified
  non-vacuous by deleting the block and watching it go red.

- **Five test bindings named scenarios that do not exist.** Nothing in this repository checks that a
  `@pytest.mark.spec(...)` key resolves — pytest accepts any string — so five invented keys looked
  exactly like bindings while binding nothing. All five now name real scenarios, and every key this
  change adds was audited against the living spec and this change's delta.

- **`Wiring.reader` and `Wiring.sorter` become resolvers — `Callable[[Flow], …] | None`, the shape
  `vocabulary` already had — and the resolution moves inside `cli.py`'s per-flow loop.** It was hoisted
  above it, so one invocation naming flows on both arms resolved a single reader and handed it to both:
  one of the two captions would have recorded a producer that did not produce it, with the whole gate
  green. A test drives one command over two flows on two implementations and asserts each artifact names
  its own, through a resolver that reports what each flow declared — a double that ignored the flow would
  make that test pass for the bug it exists to catch.

  **`READERS` and `SORTERS` are tables, not two-branch conditionals, and the argument is the refusal.** A
  conditional hands an unrecognised implementation the default one, producing a complete run on the wrong
  models with the artifact's provenance disagreeing with the manifest that asked for it — silent, and it
  corrupts any later comparison between the arms. The table makes that a refusal naming both
  implementations this build carries. A further test holds each registry's **keys equal to the strings
  the artifacts record**, so the duplication cannot drift; changing `OllamaReader.implementation` to
  `"ollama-x"` turns it red.

  **Nothing is constructed until a flow asks**, which is what lets a machine with one implementation
  available never touch the other: composing a wiring with `shutil.which` and `urllib.request.urlopen`
  both monkeypatched to raise still succeeds. `_seam` is unchanged, and the two front ends that compose
  a wiring with no reader and no sorter — the ③-only UI — still pass `None` and still refuse by name.

  `tests/stages.py` gains `Always`, a resolver handing every flow the same double, so the counting
  assertions still reach the object that did the counting.

- **`OllamaSorter`, in `isekai/pipeline/sheet.py`** — beside `ClaudeSorter` and `FakeSorter`. Its
  `format` **equals `output_shape(schema)`** rather than resembling it, which is the same object the
  Claude arm puts behind `--json-schema`: the transport differs and the constraint does not. That
  equality is what keeps a malformed answer classified **permanent** for either arm — the structure is
  required server-side, where Ollama compiles it into a grammar, so a second attempt would spend for
  nothing. An adapter carrying its own near-copy would have drifted from the Claude arm silently.

  `think: false` and `repeat_penalty: 1.15` ride with it, and both are load-bearing by measurement: a
  hybrid reasoner's thinking tokens come out of the answer's budget and truncated the JSON mid-string on
  the third subject, and at temperature 0 there is no sampling noise to break a loop, so one field came
  back with `"white robe"` forty times. Those two absences are the whole reason this repository speaks
  `/api/generate` rather than the OpenAI-compatible endpoint.

  The answer arrives **as the response body** rather than as a separate structured field, which is the
  path `answers_from` already falls back to — unchanged, and now held by a test, so a later edit cannot
  break the only path an Ollama answer takes. A truncated answer is permanent **and the record carries
  `done_reason`**, because truncated and malformed are indistinguishable from outside and only one of
  them is fixed by raising the output budget.

  **Everything downstream of the seam is shared and provably unmoved.** Two tests drive the open sorter
  through the same cascade the Claude arm uses: an absence clause becomes an empty field, and a tag
  outside the vocabulary is dropped. `isekai/shared/vocabulary.py` and `isekai/shared/fields.py` are
  byte-identical in the diff, and the open arm gets no exemption from either.

- **`OllamaReader`, in `isekai/pipeline/caption.py`** — beside `ClaudeReader` and the `FakeReader` they
  share a Protocol with, rather than in `boundary/`, because two implementations of one Protocol in two
  different layers is the arrangement that avoids. It carries `implementation = "ollama"`, an injectable
  transport, and a `body()` method the way `ClaudeReader` has `argv()` — so the request is assertable
  without a call.

  **The photograph goes as its own bytes, base64, unresized**, which is D7 built rather than assumed: the
  prototype's encoder downscaled through PIL, and PIL is in the `eval` extra and unreachable from a module
  `isekai.__main__` imports. Nothing is resampled and nothing needs to be — the vision tower encodes at
  patch14-384 whatever it is handed. **No runtime dependency is added.**

  **No `format` and no schema**, asserted as an absence. Pressing a reader into a field list is measured
  to make it invent — told never to leave a field blank, one manufactured nineteen identity marks across
  seven of ten subjects and its score fell from 0.518 to 0.307. Structure is stage ②'s to require, and
  `format` is the field that would have required it here.

  **No path from this machine reaches the model either.** The Claude adapter names the photograph's path
  because its reader opens the file with a `Read` tool; this one is handed the bytes, so a path would be
  an instruction it cannot act on and a detail about the operator's machine sent for nothing. The
  `workspace` argument stays in the signature — one `Reader` Protocol, not two — and is inert, asserted
  with a workspace the photograph is nowhere inside.

- **An unreachable host and an absent model refuse without spending an attempt**, and the tests assert
  the error-record directory is **empty** rather than merely that a refusal was raised. A spent attempt
  leaves a run whose records must be deleted by hand before it resumes, and neither of these is a model
  tried and failed. The reader's remedy names `ollama create … -f scripts/joycaption.Modelfile`, not
  `ollama pull`: the two hosted models are not the same kind of name, and the registry command would send
  the operator after a tag that does not exist. Two further tests hold the distinction honest — a 503
  *does* record a transient attempt, and a `done_reason: length` records a permanent one with
  `done_reason` in the detail and no caption written — so the "records no attempt" assertions cannot pass
  for a stage that records nothing at all.

- **`tests/transports.py`** — `FakeTransport`, hand-written and shared by the boundary's tests and both
  adapters', rather than imported from one test module by another, which would make that module
  undeletable. The same rule `tests/images.py` and `tests/stages.py` are under.

- **`isekai/boundary/ollama.py` — the third network boundary, and the second the pipeline has.** One
  POST to a local runtime over stdlib `urllib`, an injectable `Transport` protocol, and the
  classification of what comes back. **It imports nothing from `claude_cli.py`**, and it imports nothing
  outside the standard library — asserted by `python -S`, with site-packages off `sys.path`.

  `/api/generate` rather than the OpenAI-compatible endpoint, because that endpoint expresses neither
  `think` nor `repeat_penalty` and both are load-bearing *by measurement*: a hybrid reasoner's thinking
  tokens come out of the same budget as its answer and truncated the sorter's JSON mid-string, and at
  temperature 0 there is no sampling noise to break a loop, so one field came back with `"white robe"`
  forty times. Using the compatible endpoint would re-measure the two known failure modes of the model
  being adopted.

  **The address is a module constant — no flag, no environment variable.** The runtime reads no
  environment at all, a fixed local address is what `interface/ui/` and `interface/cli.py` already do,
  and making the destination of a photograph operator-controlled is a security surface this version
  declines to open. `--server`'s deliberate no-default exists because rendering costs money; a free
  loopback call does not inherit that reason.

- **The failure classification, one test per row, all through an injected transport.** A missing model
  (404) and an unreachable host (`URLError`) are **refusals that spend no attempt** — both are the
  operator's one-command fix, and a retry budget counts models tried and failed, which neither of them
  is; spending an attempt on one leaves a run whose error records must be deleted by hand before it can
  resume. That is the posture `require_binary()` already takes for an absent binary, applied to a port
  rather than to a `PATH` entry. A 5xx and a timeout are transient; an unparseable body, a body that is
  not an object, an answerless body, and any other non-200 are permanent.

  **`HTTPError` is caught before `URLError`, because it is a subclass of it** — the prototype's single
  handler mislabelled every 404 and every 502 as "did not answer". It is caught inside `post` and turned
  into a returned status, so a fake transport states one the way a real host does. A **timeout arriving
  wrapped in a `URLError`** is read as transient rather than as an unreachable host: otherwise a
  retryable failure is spent as a refusal and the operator is told to start a server already running.

  `done_reason == "length"` is permanent **and the detail carries `done_reason`**, because a truncated
  answer and a malformed one are indistinguishable from outside and only one of them is fixed by raising
  the output budget.

  The kind is carried by `OllamaFailure`, which is deliberately neither `CliFailure` — this module may
  not import it — nor a third vocabulary: it holds the same `Kind` the run directory already records, so
  an adapter translates it in one line and the stage that catches it is untouched.

- **A flow manifest may declare the hosted models its first two stages call — `hosted`, one optional
  top-level key.** It carries the implementation the reader and sorter are reached through and the model
  name each of them runs, parsed into a frozen `Hosted` on the loaded flow. Deliberately **not** `models`,
  which is required and holds the twelve pinned render weights a rented GPU loads: one names a file on
  disk with a digest behind it, the other a name a host resolves at call time, and nothing behind either
  hosted name is verified — stated in `Hosted`'s own docstring rather than implied away by sitting beside
  a digest.

  The implementation is declared **once for both stages, not once per stage**, so *this flow is wholly one
  implementation* is a property of the document rather than of two lookups that happen to agree. Declaring
  a block that names fewer than all three is refused naming what is absent, the shape `prompt`'s fragments
  are already checked in — otherwise it reaches the registry as a `KeyError` three frames later.

  **Optional, and that is what keeps `MANIFEST_VERSION` at `2`.** A required key plus a version bump was
  this change's first shape: it would have re-cut two frozen manifests to record a value already implied.
  Both incumbent flows are untouched and carry the digests they had — `summon-v1` at `1d3c206b…`,
  `conjure-v1` at `260ea7a3…`.

- **A manifest key this build does not read is now refused naming it, rather than silently ignored.**
  `load_flow` checked for *missing* keys only. Because `hosted` is optional and its absence means the
  default implementation, a misspelling — `hostd`, `Hosted`, `host` — was **indistinguishable from a
  deliberate omission**: a flow meant to run one implementation would have run the other and produced a
  complete, correct-looking run on the wrong models. Every other way of getting that block wrong already
  fails, an unknown implementation having no entry to resolve and an unreachable one refusing at first
  call, which left the typo as the only silent path. The refusal names the offending key and lists the
  nine this build reads, and it fires from reading the manifest alone — asserted with the graph file
  deleted, so nothing executed the flow to catch it.

- **D7 is decided and stands: the photograph is sent as its own bytes, base64, unresized.** The caveat
  behind this change's `feasible-with-caveats` verdict was that no real photograph had ever been sent
  unresized — the prototype always downscaled through PIL first. One of the operator's own photographs,
  3.08 MB on disk, made a **4.11 MB** POST that `/api/generate` **accepted, HTTP 200 in 12.3 s**, with
  `done_reason` `stop` and a caption that describes the photograph. **No runtime dependency is added**,
  and D7's contingency — PIL as a function-local import — is not taken.

### Changed

- **`README.md` and `CLAUDE.md`: Ollama is named as the third system dependency**, beside `claude` and
  `node`, with the two commands that create both models, the `scripts/joycaption.Modelfile` path, and
  the projector check to make after the first. README's work-in-progress banner is replaced: the first
  two stages **are** open now, on the flow that declares them, and a clone with no Anthropic
  subscription can run the whole pipeline. Three further CLAUDE.md claims this version falsified are
  corrected — `ComfyTransport` is no longer *"the network boundary, and the only one"*, `boundary/`
  lists `ollama.py`, and `flows/summon-v1/` is no longer *"the only one"* (it had not been since
  `conjure-v1`).

- **The roadmap's v0.19 claims are struck where this version does not deliver them.** *"Both readers
  pinned"* is **withdrawn**: `hosted` names two models and verifies no bytes behind either, which is
  recorded as a deferral rather than left looking like an omission, and deliberately asymmetric with
  `models`, which pairs all twelve render weights with a digest. The Qwen revision and `--model` /
  `--effort` for the Claude arm move to the **provisioning** version, which opens the file that does
  byte verification anyway. The argument that v0.19 is the first version with two implementations to
  choose between held — and what it bought was **selection**, through the manifest key and the
  registry, which is a different mechanism from pinning.

- **`both stdlib over HTTPS` is corrected wherever it appeared.** It is **plain HTTP to
  `127.0.0.1:11434`**. There is no TLS on a loopback call to a process on the same machine and there
  should not be.

### Fixed

- **The photograph could be sent to whatever `http_proxy` named.** `boundary/ollama.py`'s `post()` used
  `urllib.request.urlopen`, whose default opener builds a `ProxyHandler` from the environment — and
  urllib does **not** auto-bypass loopback, only an explicit `no_proxy` entry does. On a machine with
  `http_proxy` exported, every base64-encoded photograph was addressed to the proxy instead of to
  `127.0.0.1:11434`: precisely the operator-controlled destination D4 says this version will not open,
  opened by a variable nobody chose. Worse, the proxy's own failure then fell into the *"nothing is
  listening … start the runtime (`ollama serve`)"* refusal, which points away from the leak. The module
  now owns its opener — `build_opener(ProxyHandler({}))`, which reads no environment at all — so `HOST`
  is reachable by no configuration rather than merely undocumented. Held by a test that drives `post()`
  against a stand-in connection with a proxy exported and asserts the address urllib resolved, with a
  falsification twin proving the same environment *would* have captured a default opener.

- **A connection dropped mid-answer escaped classification and killed the batch.** `ask()` caught
  `(TimeoutError, URLError)`, and urllib wraps only what the *send* raised — anything `getresponse()` or
  `read()` raises surfaces as an `http.client` exception or a bare socket error, neither of which is a
  `URLError`. Uncaught, such a failure was not an `OllamaFailure`, so no adapter translated it, not a
  `CliFailure`, so no stage recorded it, and not a `Refusal`, so `run.across()` did not collect it: the
  command died in a traceback, the remaining photographs were never attempted, and nothing on disk said
  why — breaking `run-directory:budget:one-failure-does-not-halt-the-batch`. The host being OOM-killed
  between two models that D10 already states **do not co-reside in 16 GiB** is the designed-in
  condition, not an exotic one. The handler now covers `OSError` and `http.client.HTTPException`, keeps
  the timeout discrimination first, keeps the "nothing is listening" refusal for `URLError` alone — a
  connection that was never made — and classifies a host that answered and then died as **transient**.
  Three rows added to the `FakeTransport(error=…)` seam that already existed and had only ever been
  asked three exception types: `RemoteDisconnected`, `IncompleteRead`, `ConnectionResetError`.

## [0.18.0] - 2026-09-19

### Fixed

- **Four `ui` scenarios were bound to a test the gate never ran.** `tests/test_ui_api.py` opens with
  `pytest.importorskip("fastapi")`, FastAPI lived only in the optional `ui` extra, and CI runs
  `make gate` with no extra — so `uv sync --locked` never installed it, the module skipped in CI and on
  a clean checkout alike, and `ui:vocabulary:matches-are-ranked-by-post-count`,
  `ui:vocabulary:an-unmatched-fragment-commits-nothing`, `ui:approval:approved-input-refuses-a-draft-update`
  and `ui:approval:approved-input-opens-read-only` were proved by nothing while looking exactly like
  bindings. `fastapi` and `uvicorn` are now pinned in the **`dev` dependency group** as well, which the
  gate installs by default: `dependencies = []` is untouched and the runtime stays stdlib-only. The
  suite goes from **671 passed, 1 skipped** to **682 passed, 0 skipped**. Two structural tests hold it:
  one asserts the framework is present, so its absence is a failure rather than a skip, and one holds
  the extra's pins and the group's equal. `isekai/interface/ui/app.py`'s `[[tool.ty.overrides]]` block
  is **removed** rather than kept — the import resolves in the environment the gate runs in, so there
  was nothing left to ignore.
- **The autosave `PUT` raced the approve `POST`, and the loser was the operator's last correction.**
  `flush()` returned `void` and discarded its promise, so the comment claiming the write landed first
  stated an ordering the code did not enforce: approving inside the 400 ms debounce either built the
  artifact from the *previous* draft and unlinked the correction with it, or left a `has no draft to
  update` refusal on the header line immediately after a successful approve. `flush()` now returns its
  write and `approve()` awaits it. **This was the one place in the change where work could be lost.**
- **`⌘↩` committed a tag nobody chose, then approved the sheet containing it.** `TagInput`'s Enter
  branch tested no modifier and did not stop propagating, so approving with the dropdown open committed
  row 0 into the field and *then* ran the window handler's approve. The branch is now guarded with
  `!metaKey && !ctrlKey`, and a bare `↩` that commits stops there — the same reasoning the `Esc` branch
  three lines below already carried.
- **A failed input read left the page on the skeleton for ever, saying nothing.** `useSheet.open()`
  awaited `GET /api/inputs/{id}` with no `try`, and every caller is fire-and-forget, so a 409 or a 500
  left `loading` true, `refusal` empty and the rejection unhandled. It now catches, writes the reason
  verbatim to the header line and clears the skeleton, mirroring what `flush()` already did — which is
  where design D6 says a `Refusal` lands.

### Verified

- **The acceptance run: three photographs through ①②③④, corrected in the browser, rendered from one
  boot — and the corrections reached the images.** Six hosted-model calls (three captions, three
  sorts), every sheet corrected and approved on the review surface, then three renders at one named
  seed. **All three sheets record `edited: true`**, and the corrections were substantive rather than
  cosmetic: `cowboy-shoot` lost eight wrong `background` tags — `meadow`, `white`/`yellow`/`pink`/
  `purple`/`grey background`, `forest`, `clear sky` — for `outdoors`, `flower field`, `mountain`, and
  gained `lace trim` for `lace` and `denim shorts` for `denim`. **The operator's judgement on 13.6:
  the renders reflect the corrections and not the sorter's draft.**
- **13.4, the abort check, answered yes.** Correcting on this surface was faster and better informed
  than `$EDITOR`: the autocomplete makes it clear which tag to reach for, and the post count and the
  live token number changed decisions that would otherwise have been made blind. The version's claim —
  *a sheet is corrected on a surface that knows the vocabulary* — is earned rather than asserted.
- **Metered: two pod sessions, `19m19s` + `13m50s`, ~$0.23 + ~$0.17 ≈ ~$0.40 at $0.72/hr**, both
  confirmed torn down through the RunPod MCP (`list-pods` → `[]`, `get-pod` → `404 pod not found`).
  **The first session produced nothing and is recorded because it is the measurement.** A fresh 20 GB
  network volume had to be provisioned, and the mirror `download_models.sh` drew the 6.94 GB
  checkpoint from ran at **7.6 MB/s** — against the ~37 MB/s the v0.17 acceptance measured for the
  same manifest from the same datacenter. At that rate the fetch alone was 32 minutes, which no longer fit
  a 45-minute ceiling after a 6m35s boot, so the session was **halted at the projection rather than at
  the wall** and torn down at 19m19s.
- **The second session drew at ~48 MB/s and did everything in one boot**: 3m41s to SSH, 14.47 GB
  provisioned and ComfyUI answering at 6m21s, three renders in 3m31s, torn down at 13m50s — inside the
  original ceiling. Same datacenter, same manifest, twenty minutes apart, so **the first session's rate
  was a slow mirror and not the account or the link**.
- **A provisioning fetch is not resumable, and that is what made the first failure total.**
  `scripts/download_models.sh:65` is `wget -q -O "${target}.partial"` with no `-c`; the checkpoint is
  the manifest's first and largest entry, so nothing had landed and verified when the session was cut
  and all 4.61 GB was lost. Recorded rather than fixed: it is a one-flag change to a tracked script
  with a test of its own, and it is outside this change's scope.

### Added

- **The keyboard model the operator asked for, which separates the two axes.** `Alt+↑`/`Alt+↓` move
  through the batch; `Alt+←`/`Alt+→` move focus across the three panes — rail, photograph, sheet — and
  inside a pane the plain arrows do that pane's own thing: change the input, scroll the caption, walk
  the rows. Returning to the sheet lands on the row it was left on. **This overturns one line of
  `ux-flow.md`**, which gave `Alt+←/→` to the batch: the rail is a vertical list, so vertical is the
  batch, and horizontal is the one movement the design had no binding for at all — getting to the
  caption to read it and back to the field being typed.
- **A spinner on the draft receipt while a save is in flight**, and the saved time to the minute. The
  slot is a fixed width, so the line never shifts between the two. It is counted rather than flagged: a
  second `PUT` can start before the first answers, so it clears when the last one lands. The approved
  receipt keeps its seconds — it is written once and is the one a human would quote, while the draft's
  is rewritten every few seconds under the eye. `prefers-reduced-motion` stops the rotation. **This is
  the one piece of motion on the page**; the design's *no spinner, no shimmer* is written about the
  page-level load, and an in-flight save has no drawn state at all.
- **The photo overlay, the loading state and the run manifest.** `PhotoOverlay` is teleported to body on
  a ground of `color-mix(in srgb, var(--color-bg) 72%, black)`, with **no `.lighten` blend** — this is the
  one place the photograph must be seen as it is, because it is where colour is judged. `Fit` / `1:1
  pixels` with the percentage stated, because a judgement made at 64% is not the same judgement; `esc`,
  a click anywhere or the × leave it, and **the arrow keys still move through the batch without
  closing**, so the overlay doubles as a way to compare inputs. It sits below the 41px header rather
  than over it, so the run line and the receipts still read — not dimmed with an opacity wrapper, which
  is how that header first became illegible.
- **Loading is counted, not spun, and no photograph appears until it has decoded.** 135° striped
  placeholders at each photograph's true aspect ratio, all sixteen schema keys rendered immediately with
  flat 9px bars and dashed gutter rings so nothing reflows on arrival, the token total as `—`, and
  `vocabulary 8,106 tags · loaded` from a real `len()`. **No shimmer** — an animated skeleton pulls the
  eye off the photograph. The line names the input being read rather than counting `2 of 3`: the browser
  reads one input at a time, so a count would say `1 of 3` forever, while the stated reason for counting
  at all is *if it does not finish, the operator wants to know which file it is stuck on*.
- **`RunManifest`, reached by approving the last input or from the rail at any time.** One row per
  approved sheet — its path, its token count, the time it was written — with over-budget totals in
  `accent-300` and stated once more at the exit. It names the artifact and gives no order: the operator
  wrote the CLI and does not need to be told to run `generate`. Real paths throughout:
  `<run>/<flow>/review/` and `NNN.approved.json`, never the frames' invented `runs/2026-09-17/`.
- **`Alt+↑` / `Alt+↓` move through the batch too.** The rail is a vertical list and the photographs read
  left to right, so both readings of *next* are true and both now work.
- ~~**Space on an empty field types the word the schema says that field is spelled with**~~ — **this
  entry was wrong when it was written, and is corrected here in v0.21 rather than deleted.** The
  feature existed on a prop named `hint` and was **removed in `8aa6fb0`, *"feat(ui): rework the
  keyboard model"*, which is an ancestor of the `v0.18.0` tag** — so it was introduced and deleted
  inside this very version and never shipped in any release. It could not have worked either:
  `ui/app.py` sends `list(batch.flow.schema.names)`, names only, so a field's suffix has never
  reached the browser in any version. What did ship, and still does, is the autocomplete: the rows
  are `vocabulary.search()`'s, in `vocabulary.search()`'s order, for every fragment, which leaves the
  design's *ranking is global* rule untouched.
- **Approve, read-only, and the one line a `Refusal` lands on.** `ApproveBar` is accent-outlined and
  **always live** — no scroll gate, no dwell timer, no confirmation step, no disabled twin, and no
  empties action: the only thing that stops an approve is a refusal, never a ritual. On success the
  header shows **both receipts**, the approved one in `accent-300`, and the button becomes the fact
  `Approved HH:MM:SS` rather than a greyed-out copy of itself. **The input then goes read-only** (Design
  D5): `approve()` deletes the draft and reopening writes no replacement, so there is nothing on disk
  for an edit after approval to be written into — the footer states that and names the file, and offers
  no exit affordance, because a surface that offered editing anyway would either appear to save and not,
  or spend a version number on a keystroke with no confirm step to attribute it to.
- **The refusal line.** One header-level line carrying the `Refusal` string verbatim, in the design's
  own voice for states it specified and deliberately did not draw: blunt, no modal, and it never implies
  the operator's work was lost. Verified with two real tabs on one input — one approves, the other's
  autosave fires on the next keystroke, the line appears and **nothing on disk changed**.
- **`↑`/`↓` walk the sheet when no dropdown is open**, clamped at both ends. Not in the design's keyboard
  model, which leaves the vertical keys unassigned outside the dropdown; an operator who has just
  clicked a row should not have to reach for the mouse again to reach the next one.

### Documentation

- **Three claims this repository makes about itself that v0.18 falsifies, corrected.** `CLAUDE.md`'s
  *"there is nothing generated outside it to get wrong"* named one ignored root; there are now **four**,
  and the boundary paragraph states how each fails differently — `.data/` is the loss of work, `models/`
  a byte-identical re-download, `ui/dist/` a deterministic rebuild, `ui/node_modules/` an `npm install`.
  Only the first is work; the other three are derivable, which is why none of them lives under `.data/`.
  And *"`openspec` 1.11 ships no `new`/`scaffold` command"* was **false** — `openspec new change <name>`
  exists; this repo scaffolds by hand because it keeps no `openspec/config.yaml` and because the id rule
  is not one the CLI knows.
- **node is recorded as this repository's second system dependency**, after the `claude` binary, needed
  by `isekai ui` alone. `CLAUDE.md`, `README.md` and `isekai/interface/README.md` gain the `ui` verb and
  the surface's four modules; the living `cli` spec's gloss stops saying *six verbs*. `baseline/labels/`
  stops calling `.data/` *the one ignored root*.

### Fixed

- **A click anywhere in a row focuses that field, `↑`/`↓` walk the rows, and `Esc` keeps the focus.**
  The fragment input is sized to its content so the caret sits immediately after the text, which left
  an empty field with a click target one character wide. `Esc` now also stops propagating, so nothing
  above the input acts on an `Esc` the dropdown already answered.
- **The manifest's `approved` column was blank.** `saved` reports the draft's own time and `approve()`
  unlinks the draft, so `GET /api/inputs/{id}` now reports `approved_at` beside it.
- **One caret, not two.** The fragment carried a 1px accent `border-right` *and* the browser's own
  recoloured caret — two marks for one insertion point, which is the *committed and in-flight never
  look alike* rule read backwards. The border is gone; the caret is the caret.

### Added

- **Editing, autosave and undo — and the page stops reading a fixture.** `useBatch()` and `useSheet()`
  replace it: the batch is the invocation's argument list held in memory, the draft is read from
  `GET /api/inputs/{id}`, and every edit schedules a debounced 400 ms `PUT` of the whole draft. **There
  is no Save control anywhere** — the two receipts are the only thing on the page that talks about
  saving, and the last-saved timestamp comes back from the server rather than the client clock, because
  a receipt the browser wrote for itself is a claim about a save and not a record of one. Verified on
  disk: `001.draft.json` changes in place, keeps its version and the sheet it records, and **no `002`
  appears**.
- **The keyboard model, less the two bindings that went with the refusal surface.** Tab through the
  fields in schema order, `Alt+←/→` between inputs, `←/→` to move chip selection, any character to open
  the autocomplete, `↑↓⏎` to commit, `Backspace` to remove the last chip or the selected one, and
  `Cmd/Ctrl+Z`/`Shift+Z` to undo and redo. **Replacing a selected chip by typing is three keystrokes**
  — `→`, type, `⏎` — because it is the single commonest edit in the job; measured live, `long hair` →
  `very long hair` in one step, and one undo puts it back without disturbing an earlier edit in another
  field. Undo is a stack of **edit operations** rather than sheet snapshots, it crosses every field, and
  it is cleared when the operator changes input.
- **The tag autocomplete — the piece that decides whether the tool is fast.** `useVocabulary()` queries
  `GET /api/tags?q=` debounced at 120 ms and **ranks nothing**: the server's order is the order, because
  a second copy of the ranking rule in TypeScript is the duplication that endpoint exists to delete. A
  stale answer can never overwrite a newer one. `TagAutocomplete.vue` is 430px on `--color-surface` at
  `top: 30px`, **absolutely positioned so it overlays the rows below and never displaces them** — if
  they moved, the operator would lose their place mid-word. Row 1 is preselected, so the highest post
  count is one ⏎ away and a rare tag takes a deliberate ↓; counts are right-aligned mono `tabular-nums`,
  because a post count is read by digit count and that only works if the digits align; ` · rare` in
  `accent-300` below 2,000 posts. **Measured against the real prediction set, not the design's:**
  `blonde` returns `blonde hair` (1,311,581) and `blonde pubic hair` (1,634 · rare) — two tags, not the
  frames' four, since `platinum blonde hair` is absent. A fragment matching nothing shows no rows and
  cannot be committed.
- **A click anywhere in a row focuses that field.** The fragment input is sized to its content, because
  the 1px accent caret must sit immediately after the text rather than at the row's right edge — which
  left an empty field with a click target one character wide. The row is what the operator aims at.
- **`ui/` — the Vue 3 app, its shell and the read-only sheet.** Vite, no router, dark theme only,
  desktop from 1280px. `AppHeader`, `BatchRail`, `StatusMark`, `SourcePanel`, `PhotoFrame`,
  `CaptionPanel`, `SheetForm`, `SheetHeader`, `TokenBudget`, `FieldRow` and `TagChip`, built against a
  static fixture so the marks and the rows are right before a fetch can be blamed for them. **Six of
  the ten frame deltas land here**: no `Show ② draft` pill (its ON state is drawn nowhere); the run
  line reads `summon-v1 · 3 inputs · 0 approved`, because a run id is `<12 hex>_<slug>` and carries no
  date; receipts name `<flow>/review/001.draft.json`; the caption shows paragraphs only, because
  `sheet.py` discards the phrases a highlight would need; no empties action anywhere; and above 77 the
  budget bar clamps at 100% with the total in the accent, since counting the assembled prompt puts
  every real sheet over.
- **Inter is vendored and the token sheet is copied, not imported.** `ui/design/` is read-only, so
  `ui/src/styles.css` is a copy of it with exactly two deltas: its Google Fonts `@import` deleted, and
  four local `@font-face` rules over woff2 files in `ui/src/assets/fonts/`. A private tool over a
  directory of personal photographs must not reach a third party on every load, and offline it would
  have rendered in the wrong typeface — on an interface whose type sizes are load-bearing.
- **`isekai ui <ids…> --flow F` — the review surface, and the pipeline's seventh verb.** One FastAPI
  process on `127.0.0.1` serving a built Vue bundle and six endpoints. It resolves the flow, every named
  input, a draft for each, each photograph's dimensions, the vocabulary and the bundle **before a port
  is bound**, and prints an address only once all of them have succeeded — every input's failure
  reported together, because ten photographs with two missing sheets must name both rather than be
  discovered one restart at a time. `--flow` is required and takes **exactly one**: the surface shows
  one schema's fields in one fixed order, so a second flow would be a second page rather than a wider
  one, and a repeat is refused at the command line rather than kept silently as argparse would.
  **Scope is stage ③ alone** — no upload, no captioning, no generate button — so nothing in the browser
  spends money.
- **`isekai/interface/ui/`, four modules, and the split is what keeps the suite offline.** `batch.py`
  holds the batch and the whole startup refusal order and imports no web framework, so that order is
  exercised by the main suite with the `ui` extra uninstalled; `bundle.py` builds the browser bundle or
  refuses naming the command; `app.py` is the only module that imports the extra at all; `__init__.py`
  composes the three. **The batch lives in memory and nothing writes it down** — nothing on disk says
  ten photographs belong together — and the approved count is read from the directory, so it stays true
  when something is approved by the verb beside the running surface.
- **The invariant that replaces a structural guarantee.** Both front ends now call the stage functions
  in process, so the surface is no longer stopped from writing its own artifact by the shape of the
  system. `tests/test_ui.py` greps `isekai/interface/ui/` for `envelope(`, `artifact_name(` and
  `write_json(`, and its docstring states that it is a **tripwire and not a proof**: an aliased import
  walks past it and a hand-built f-string is invisible to it. Three write functions reach a run
  directory and all three are stage ③'s — `review()` at startup, `save_draft()` on autosave, `approve()`
  on the button.
- **`[project.optional-dependencies] ui = ["fastapi", "uvicorn"]`, pinned exactly, with
  `dependencies = []` untouched.** The runtime stays stdlib-only and the `-S` guard stays green,
  because `cli.py`'s `ui` handler imports the package **inside the function**. Both packages are named
  explicitly rather than taking `fastapi[standard]`, which pulls a much wider tree for one localhost
  server. `httpx2` joins the dev group — it is starlette's test client, not a server dependency.
  CI installs neither, so `isekai/interface/ui/app.py` and `tests/test_ui_api.py` get a
  `[[tool.ty.overrides]]` block for `unresolved-import` alone; an override is green whether or not the
  extra is installed, which per-line `ty: ignore` comments cannot be.
- **`review.save_draft(run, flow, fields)` — one owner for an in-place draft update.** It replaces the
  highest draft's field values, keeps the version number and the sheet the draft records, and **does
  not create**: `review()` owns that, and a second creator would spend a version number on a stray
  keypress. It refuses an update whose field-name set differs from the draft's, which turns two of the
  four ways a sheet can be invalid at approval — a missing field, and a field the schema does not have
  — from a property the editing surface is trusted to have into a property of the write path, for one
  comparison and without opening the validator. It refuses when no draft exists, which is also what a
  stale tab meets after an input has been approved.
- **`review.token_budget(fields, schema, flow)` → `TokenBudget(total, per_field, overhead)`.** The
  total is counted over `assemble()`'s own positive prompt, so the flow's prefix, its trailer and the
  separators that join them fall out of one rule instead of being added back by hand. Measured on a
  real sheet: **100 against `estimate_tokens`' 81** — the tags-alone count understates what the text
  encoder reads by nineteen tokens against a window of seventy-seven, so a sheet reported comfortably
  inside the budget was in fact past it and silently chunked. The per-field shares and the overhead sum
  to the total by construction, because the operator's question while correcting is never *how many
  tokens* but *which tag goes*. `estimate_tokens` and `approve()`'s warning are **untouched**, so all
  26 `approve` call sites stand.
- **`wiring_from(*, runs, server=None)` — the argv-free half of the composition root.** `wiring(args)`
  is now one line over it. A second front end cannot reach a `Wiring` without passing through
  `_check_run_root`: building the dataclass directly, the way the suite does in three modules, walks
  straight past the one guard that bounds where a copy of the photograph may be written, and a server
  is exactly the thing that should not be able to. Asserted, not assumed — `wiring_from(runs=<in-tree
  path>)` refuses.

### Changed

- **`reader` and `sorter` are optional on `Wiring`, following `client`'s precedent.** A front end that
  serves stage ③ alone reaches no hosted model, and fabricating a `ClaudeReader()` it never calls would
  be a lie in the code. The two verbs that do reach one — `caption` and `sheet` — say so at their own
  call site and refuse naming the missing seam, rather than the dataclass insisting for everyone.

### Fixed

- **Two refusal strings in `review.py` that named something that does not work.** `review()`'s
  no-sheet refusal told the operator to run `python -m isekai sheet`, which exits 2 because `--flow` is
  required — and the review surface calls `review()` once per input at startup, so *you forgot to run
  `isekai sheet`* is this version's likeliest message. It now names `python -m isekai sheet --flow
  <flow>`, verified through `build_parser()` rather than by running the verb, which would call a paid
  model. And `approve()`'s already-approved refusal named `review/<flow>/`, the stage-first layout v0.16
  deleted; it now names `<flow>/review/`.
- **`security/S1`: the run-root containment guard is decided by directory identity, not by the text of
  a path.** `Path.resolve()` follows symlinks and drops `..` segments but does **not** fold case, so on
  the case-insensitive filesystem this project is developed on, `--runs` naming a directory inside the
  working tree with one letter of its own path in the wrong case compared as a different path and was
  **accepted** — the exact outcome the rule exists to refuse, reached by a typing mistake rather than by
  an adversary, leaving a directory of personal photographs somewhere `.gitignore` does not cover.
  `_check_run_root` now walks the resolved root and its parents comparing `(st_dev, st_ino)` against the
  repository and the ignored data root; an ancestor that does not exist yet has no identity, so the
  textual test stands in for it, where there is no second name to be fooled by either. The refusal
  message is unchanged. `os.path.normcase` would not have closed this: it is a no-op on darwin. The fix
  lands **before** the extraction that exposes it, so no commit carries a broken guard through a new
  door.

- **The nine living specs gain `## Purpose`, and the tooling stops answering from an empty parse.**
  Every one of `caption`, `cli`, `comfy-transport`, `evaluation`, `image-generation`,
  `model-provisioning`, `review`, `run-directory` and `sheet` failed
  `openspec validate --specs --strict` on a missing `Purpose` section and reported `requirements 0`,
  so every `openspec` query against 174 scenario keys had been reading nothing. The heading is added
  above prose that was already in each file — **no prose is written**; the fold that created these
  specs kept the paragraph and dropped the heading. `0 passed, 9 failed` becomes `9 passed, 0 failed`,
  and `review` now reports its 6 requirements. This lands first because v0.18 is the first change
  since the rule was set to add a capability, and the fold rule that would create it is the same rule
  that broke the nine.

## [0.17.0] - 2026-09-18

### Verified

- **The acceptance run: two flows, one invocation, one boot, seven renders — and it needed no code
  change.** The first end-to-end execution of the multi-flow path, which no test had ever run:
  `tests/test_pipeline_cli.py`'s `_two_flows` stops at `_flows_for`, so the multi-flow loops,
  `prepare`'s multi-entry return and `report` over two flows were untested end to end until this
  session.
  - **Locally and for free:** `caption` → `sheet` → `review` → edit → `approve` for three
    photographs across both flows, then `generate` with no `--server`. Seven approved sheets, seven
    assembled prompts, **zero outputs** — no endpoint contacted.
  - **Metered:** one pod, `19m42s` boot to confirmed teardown, **~$0.236** at the RTX PRO 4500
    Blackwell's live $0.72/hr — inside the ~$0.30 and 45-minute ceilings. The volume was empty, so
    this session also paid for provisioning: 14 G of the manifest fetched in ~6m25s, ComfyUI up at
    11m36s, seven renders in ~7m25s (~67s each). Teardown confirmed through the RunPod MCP:
    `list-pods` returned `[]` and `get-pod` returned `404 pod not found`.
  - **`--seed` was passed explicitly**, as `design.md`'s risk register requires: two flows in one
    invocation draw different seeds from one shared `Random`, so the pair is only comparable when the
    seed is named. Every render is `20260917.png` under both flows.
  - **`show` survives two flows** — never run before this change. Two flow subtrees, nothing refused,
    exit 0, and it distinguishes `001 unedited` from `002 edited`.
  - **`conjure-v1` renders a recognisable anime character from the sheet alone**, at a flatness the
    operator accepts. Every sheet tag landed. Against `summon-v1` on the same subject and seed it is
    the **flatter** of the two — flat cel shading and visible linework where `summon` is painterly,
    which is InstantID pulling toward likeness. **Parked entry P9 (`hires_denoise` 0.50 as
    `conjure-v2`) is therefore not triggered**; it stays parked with its trigger unfired.
  - **Four of the five new schema fields were exercised** across the subjects — `eyelashes`, `lips`,
    `nose` and `bangs`. `facial_hair` stayed `[]` throughout, correctly: no subject had any, and
    writing a negation into a sheet is what rule 3 forbids.

### Documentation

- **The version's verdict is recorded as a measurement, in the change's `design.md` under
  `## Verdict, measured`.** `git diff --stat v0.16.0..HEAD` over `isekai/`, `scripts/`, `Dockerfile`,
  `start.sh`, `infra/`, `Makefile`, `pyproject.toml`, `.github/` and `openspec/specs/` is **empty**:
  `conjure-v1` loads, assembles and renders through v0.16's code unchanged, and the two checks no
  second flow had ever exercised — `REQUIRED_NODES` and `TRANSFERRED_INPUTS` — both held. The test
  surface is one module, `tests/test_flow.py`, in **two edits across six lines**: the designed pin and
  its mandated comment, and the widened vacuity guard. **The verdict's own "two lines" prediction was
  a line count of an edit count**, and the four extra lines are the comment this change's own plan
  required — written down rather than reconciled. No fourth bucket appeared, so **v0.16 was complete
  on the claim this version tested**: adding a flow cost a directory plus one deliberate pin.

### Added

- **`flows/conjure-v1/` — a second flow, and the first test of the claim that adding one is a
  directory and nothing else.** An anime character drawn from an approved sheet of canonical tags
  alone: no identity node, no ControlNet, no photograph in the graph. **It makes no identity claim
  and is not evaluated.** Five flat files, like `summon-v1`:
  - `graph.json` — 14 nodes, `summon-v1`'s 23 less the photograph loader, the InstantID leg, the
    OpenPose leg and the working-resolution scale. Six edges repoint on the two samplers, each back
    to the source InstantID displaced — `CheckpointLoaderSimple(1)` for `model`, `CLIPTextEncode(3)`
    and `(4)` for the conditioning — so the rewiring restores rather than invents. The hires chain is
    untouched.
  - `flow.json` — `inputs: ["sheet"]`, with `photo` declared on **neither** side, which is the
    sheet-only case `TRANSFERRED_INPUTS` permits. Seven node roles, two models, and `summon`'s dials
    less `ip_weight`, `identity_cn_strength` and `openpose_strength`: a dial whose node was deleted
    is a declaration nothing reads.
  - `schema.json` — 21 fields, `summon-v1`'s sixteen plus `bangs`, `eyelashes`, `nose`, `lips` and
    `facial_hair`, all `scored: false`. In `summon` the identity and pose legs supply the face;
    `conjure` has neither, so the face reaches the render only as tags. Every new field is reachable
    by the vocabulary's suffix or containment pass, so no shared routing was touched.
  - `caption.briefing.md` — richer on the face, naming all 21 attributes, and licensing inference on
    **expression and the scene's light only**. *"Do not interpret"* is kept and narrowed to the
    identity-bearing fields — skin, hair, eyes, marks, build — and the absence licence is verbatim.
  - `sheet.briefing.md` — the five new fields in `## The fields` and in both worked sheets, each
    illustrated only with phrases the pinned vocabulary actually carries.
- **`conjure-v1` pinned in `tests/test_flow.py`'s `PINNED`.** This is the freeze working, not a
  defect: the pin list is what makes adding or removing a flow deliberate.
- **The dial provenance table** in the change's `design.md`: every dial against
  WAI-Illustrious-SDXL's own published recommendation, separating what the publisher states from what
  sits inside a range it bounds from what it does not address at all. `clip_skip` `-2`, `scheduler`
  `normal` and the VAE and base resolution are named as inference.

### Fixed

- **`test_every_tracked_flow_parses` no longer hard-codes the registry's contents.** Its opening
  `assert tracked_flows() == ["summon-v1"]` was a vacuity guard — it exists so the loop beneath it
  cannot pass on an empty registry — wearing a registry assertion's clothes. It is now
  `assert tracked_flows()`, which keeps the guard and drops the single-flow assumption. Every other
  test in the module already iterates `tracked_flows()` rather than naming its length, so this was an
  incidental assumption rather than a designed freeze; the designed freeze is `PINNED`, which stays.
- **Both `conjure-v1` briefings stop eliciting two attributes the vocabulary cannot hold, and the
  flow is re-pinned.** Converge round 1's finding R1: `caption.briefing.md` asked for the skin's
  *tone* and for whether the brows are *darker or lighter than the hair*, and the exact-match pass
  routes the answers to `light` (13,918 — a light source) and `dark` (12,729 — a dark image) rather
  than to `pale skin` (44,564) and to nothing. Four of the seven approved acceptance sheets carried
  `skin_ancestry: ["light"]` and one carried `eyebrows: ["dark"]`, and those reached rendered
  positives whose own negative carries `lens flare, light particles`. The caption briefing now names
  the three words that land — *pale, tan, or dark* — and drops the brow-lightness ask, per
  `design.md` D4's own reasoning that an axis which cannot be filled makes a sheet look more complete
  than it is; `sheet.briefing.md` enumerates `skin_ancestry`'s canonical terms and states that a
  brow's colour is dropped. **The change's `### Added` claim that every *new* field is
  cascade-reachable stands** — the trigger was `skin_ancestry`, a field `summon-v1` already had and
  whose briefing never mentioned it — and `design.md`'s risk register now says so.
- **`PINNED["conjure-v1"]` re-pinned to `260ea7a3…`**, because the digest covers every regular file
  in the flow's directory and a briefing is one of them. **The metered acceptance render therefore
  tested the prior bytes** — `38698396…` — and its claims are recorded against those: the multi-flow
  path, `show` over two subtrees, the pod and teardown numbers, and P9's unfired trigger are all
  about code and graph that this fix does not touch, while the seven sheets and renders it produced
  are the *evidence for* R1 rather than a measurement of the corrected briefings. `conjure-v1` makes
  no identity claim and is scored against nothing, so nothing measured is invalidated; the exception
  that permits the re-pin is written beside the constant.

## [0.16.0] - 2026-09-17

### Documentation

- **The living spec's `Source:` lines, `README.md`, `CLAUDE.md` and the group READMEs follow the
  version.** `sheet`'s named `schemas/identity.v1.json` and `schemas/identity.v1.briefing.md`, which
  no longer exist; a flow is described as five flat files rather than two; the repository tree, the
  run layout and every worked `python -m isekai` invocation carry `--flow`; `pipeline/README.md` no
  longer claims one stage imports another; `shared/README.md` gains `fields.py`. The blast-radius
  sweep is a `git grep` over every tracked file except `CHANGELOG.md` and the change directory —
  v0.15 shipped a broken `Dockerfile` COPY by hunting only the files being renamed.
- **`tests/test_package_paths.py`'s anchor table drops to six constants across five files**, and its
  prose says so. Two anchors left with the fold: a schema and a briefing are a flow's now, and a flow
  is reached through `FLOWS_DIR`.

### Fixed

- **A manifest that declares the photograph on one side only is refused at load.** The transfer is
  gated on `inputs` and the `LoadImage` patch on `nodes`, and nothing held the two in agreement once
  both became conditional: a flow naming `nodes.photo` but omitting `photo` from `inputs` uploaded
  nothing and rendered the filename committed inside `graph.json` — a paid render of the wrong
  person, with the whole gate green — while the mirror case uploaded a photograph no node reads.
  `load_flow` now refuses the disagreement beside the required-roles check, naming the flow and the
  half of the manifest the declaration is missing from, so it costs a test run rather than a boot.
  Identity preservation is the product; a check that can only be made after the render is not one.
- **Resume no longer assumes a render is a PNG.** `rendered_seeds` filtered `iterdir()` on
  `path.suffix == ".png"`, so a flow whose output is not a still image would have had its finished work
  reported as missing and rendered again — on the one stage that costs money on every pass. The
  predicate now takes what the flow says it produces, and `Flow.output_suffix` is the one line a video
  flow changes when it arrives; the render path writes through the same answer, so the writer and the
  resume check cannot disagree (design.md D11). This change owes exactly that and no more.

### Changed

- **BREAKING — the run layout is input above, flow below.** A run is now
  `runs/<input-id>/<flow-id>/{captions,sheets,review,prompts,outputs}/`. Above the flow split sits only
  what every flow shares, and after this change that is the input itself and its frame. Nesting
  stage-first meant adding a flow scattered four entries across four stage directories; flow-first,
  adding a flow adds one subtree and retiring one flow's work is removing one directory. Captions move
  below the split too, which is what makes a flow's briefing binding: a caption written under one
  flow's instructions can never be picked up by a flow whose instructions differ, because the two never
  name the same directory (design.md D5, D6).
- **BREAKING — the run id's separator is an underscore**: `<12 hex>_<slug>`. `slug()` maps every unsafe
  character to a hyphen, so `0bfdc0612d98-cowboy-shoot-1` gave a reader no way to see where the digest
  ended; a slug can never contain an underscore, which makes the boundary unambiguous. Twelve hex
  characters stay — six is a birthday collision at roughly 4,800 inputs, and the remedy for a collision
  is a human renaming a directory by hand. Nothing parses the id, so this is readability alone
  (design.md D10).
- **BREAKING — the sheet stage writes one sheet for one flow.** `sheet()` took a list of destinations
  and fanned one fill out across them, which is the sharing v0.16 deletes; it now takes the flow whose
  directory it reads the caption from and writes the sheet to, and returns one path or none. The
  caption stage takes its flow for the same reason. Neither the reader nor the sorter learns anything
  about flows: the flow decides which directory is touched, not what is asked.
- **The inspection command lists per flow then per stage.** `run_view`'s per-flow-ness table is gone —
  every stage is a flow's own now, so there is nothing left for that column to say — and its bespoke
  outputs walk is one listing of the run's flow subdirectories. `approved_flows` reads the same
  listing.

### Added

- **`--flow` is required and repeatable on every stage verb.** It reached three of six verbs, was a
  single string that silently kept the last occurrence, fell back to every tracked flow, and had no
  test coverage at all — one hit in the suite, asserting a refusal string. It is now
  `action="append"`, `required=True` on `caption`, `sheet`, `review`, `approve` and `generate`; `show`
  is the only verb that does not take it. A stage cannot act without knowing which flow asked, because
  the flow is what supplies its briefing, its schema, its graph and its dials.
- **A flow named on the line is resolved against `flows/` before any run is opened**, and an untracked
  one is refused naming it and listing the flows that are tracked. At `generate` the flow's first use
  used to be after a photograph had been uploaded, so resolving at selection is what keeps the refusal
  free. `dispatch` reports that refusal rather than letting it escape.
- **A flow is asked which node roles it declares, instead of being assumed to have eleven.**
  `positive`, `negative`, `latent` and `sampler` are required and checked in `load_flow` the way the
  prompt's fragments already are; the other seven — `photo`, `scale`, `identity`, `openpose`,
  `clip_skip`, `hires_resize`, `hires_sampler` — are guarded at the patch site. `build_graph` performed
  eleven lookups across ten call sites with none guarded, and `load_flow` checked only that the key
  `nodes` existed, so a flow declaring fewer passed the entire gate and died on a rented GPU — after
  `upload_image` had already spent it (design.md D9). The refusal now happens offline, naming the role.
- **`flow.inputs` gets its first production reader.** The photograph is transferred only where the flow
  declares a `photo` input; a flow that does not declare one uploads nothing. The field was declared,
  populated and read by one test.

### Changed

- **A flow is five flat files, and its manifest names none of them.**
  `schemas/identity.v1.json`, `schemas/identity.v1.briefing.md` and `briefings/caption.md` move into
  `flows/summon-v1/` as `schema.json`, `sheet.briefing.md` and `caption.briefing.md`; the two
  repository-root directories are gone. Flat rather than nested because `manifest_digest` filters
  `iterdir()` through `path.is_file()` — a sub-directory would have left the schema and both briefings
  outside the freeze with the gate green (design.md D1). A briefing decides what enters the caption, the
  caption decides the sheet and the sheet decides the render, so a changed briefing is a changed image
  and must be a new flow; the digest now proves that.
- **BREAKING — `flow.json` is eight keys.** `"schema"` and `"graph"` are deleted — a key that can only
  ever hold one value is not a declaration — and `schema_version` becomes `manifest_version`, bumped to
  `2`, because it never meant the schema's version but the manifest's own format (design.md D3). The
  five filenames are constants in `isekai/foundation/flow.py`, and `load_flow` refuses a flow missing
  any of its four siblings, naming the file.
- **BREAKING — a flow pins its model artifacts by digest.** `"models"` is now `[{dest, sha256}, …]`, and
  a new gate check holds every digest equal to `scripts/models.json`'s entry for the same destination,
  failing by name. A bare destination path does not pin bytes: re-pinning a checkpoint would otherwise
  have made `summon-v1` render differently under the same identifier with the gate green, on the 6.9 GB
  that decides what the image looks like (design.md D4).
- **`Schema` loses its version and its vocabulary.** Inside a frozen flow directory a version protects
  nothing — the flow's digest proves the field list byte for byte, and a changed field list is a new
  flow. The vocabulary is the flow's declaration, so the schema document is `{name, fields}` and
  `load_schema` takes the path of the flow that owns it. `sheet.SCHEMA_VERSION`, `schema_path()`,
  `SCHEMAS_DIR`, `BRIEFINGS_DIR` and both `BRIEFING_PATH` constants are deleted; the sheet and caption
  stages take their briefing as an argument.
- **BREAKING — sheet sharing is removed with `_matching_flows`.** It was the only mechanism, had one
  caller, and was the only production reader of `Flow.schema` and `Schema.version`. Every stage verb is
  now driven per flow, each one handed that flow's own schema and briefing: `load_schema` moves beside
  `Schema` in `isekai/foundation/flow.py`, and a loaded `Flow` answers for its own schema through a
  cached property, so `Wiring` carries no schema at all. Sharing bought a selector and a class of
  silent cross-flow inheritance in exchange for a rounding error — a caption is $0.0159 per photograph
  at worst against a $0.036 boot (design.md D5).
- **`summon-v1`'s committed digest is re-pinned once**, under the exception design.md D2 records: the
  flow's configuration did not change, its manifest's format did, and `manifest_version: 2` is that
  distinction in data. The failure message in `tests/test_flow.py` gains no "unless" clause — a test
  message that explains how to evade itself is one that gets evaded.

- **`validate` moves from `pipeline/sheet.py` to `shared/fields.py`, and the last stage→stage
  import goes with it.** `review.py` imported and called `sheet.validate` — the sixth of six such
  edges and the only one v0.15 did not close, so `grep -rn 'from isekai.pipeline'
  isekai/pipeline/` now returns nothing. It lands in `shared/` rather than in `foundation/` beside
  `Schema` because it depends on a `Vocabulary`, and `shared/vocabulary.py` already imports
  `foundation/refusal.py`; putting a vocabulary-dependent function in `foundation` would make the
  two groups import each other in both directions, where `shared → foundation` adds no new
  direction (design.md D8).

### Fixed

- **Two tests that pin a path the flow fold is about to change can now fail.**
  `tests/test_run_directory.py` asserted `briefings/caption.md` against a producer record it
  **built inline**, so it would have stayed green while the code wrote
  `flows/summon-v1/caption.briefing.md` — a silent anchor, the one edit in v0.16 that fails
  quietly (design.md D7). The record under assertion is now produced by
  `claude_cli.instructions_record` off the briefing the stage actually reads, and the detector was
  confirmed red against a moved briefing before anything moves. This is the shape v0.15 used for
  `DATA_ROOT`: write the detector while the anchor is still correct.
- **`test_no_second_ordering_is_defined_anywhere_else` was vacuously true.** It globbed
  `isekai/*.py`, which since v0.15's six-group restructure reaches only `__init__.py` and
  `__main__.py` — so the assertion that no module carries a second copy of the sixteen field names
  held over an empty list. It now uses `rglob`, covering all 31 modules, and still passes.

## [0.15.0] - 2026-09-17

### Added

- **The eight repo-root anchors are pinned to the repository root, before anything moves.**
  Seven files compute a repo-root path as `Path(__file__).resolve().parent.parent`, and v0.15's
  restructure moves every one of them a directory deeper — where that expression yields `isekai/`
  instead of the repository. Six of the eight constants would fail loudly; **`DATA_ROOT` would
  not.** It would become `isekai/.data`, `RUNS_ROOT` would move with it, and every test asserting
  the *relationship* between the two would still pass, while the guard that keeps a run directory
  — which holds a copy of a photograph by construction — out of one `git add` quietly narrowed to
  refuse only paths inside the package (design.md D7). `tests/test_package_paths.py` asserts the
  **absolute** property instead: strip each anchor's own suffix and what remains must be the
  directory holding `pyproject.toml`, never another constant that would move alongside it. It
  carries **one** falsification twin, because a check that cannot fail is not a check — each anchor's
  suffix cancels against its own hops, so all eight reduce to the same path and parametrizing would
  advertise per-anchor coverage that does not exist. Written while every anchor is still correct, so
  it passes today and goes red the moment a file moves without gaining its `.parent` — the detector,
  not the fix.

### Fixed

- **The image and the provisioning driver follow `provision.py` into `boundary/`.** The restructure
  moved `isekai/provision.py` and `Dockerfile`'s `COPY` and `scripts/download_models.sh`'s `PROVISION`
  still named the old path — the first breaks `docker build` outright, the second is a dead path on a
  clone. **No gate command reads either file**: `bash -n` and `docker build --check` are the
  image-phase convention and v0.15 is not an image phase, and `tests/test_infra.py` asserts on
  `start.sh`'s shape but not on these paths. The destination matters as much as the source —
  `provision.py` resolves its manifest as `parent.parent.parent / "scripts"`, so it must land at
  `/opt/isekai/isekai/boundary/provision.py` for `/opt/isekai/scripts/models.json` to resolve; the
  `Dockerfile` comment that makes the layout load-bearing now says so.

### Changed

- **`known-first-party = ["isekai"]` is declared to `ruff`'s isort.** It decided first-party per
  *submodule* by asking whether the path existed on disk, so once `isekai/pipeline/` became a package
  directory the archived v0.10 probe's single import block split across two sections — `isekai.pipeline`
  resolved, `isekai.comfy_client` and `isekai.workflow` (deleted at v0.14) did not — and `I001` fired
  on a file untouched since v0.10. Naming the package states the fact directly, so classification no
  longer depends on what happens to exist in the tree today. **Not a suppression**: an archived change
  is never repaired, and the alternatives were editing the archive or exempting a rule. Neither was
  needed, and no live file's import order changes.

- **The record catches up with the package.** All nine `openspec/specs/*/spec.md` `Source:`/`Tests:`
  lines now name files that exist — every path was invalidated at once by the restructure — and each
  gains what it omitted: `image-generation` gains `image.py` and its tests, `cli` gains `cli.py`,
  `wiring.py`, `run_view.py` and the three further test files holding `cli:*` keys, `run-directory`
  gains `atomic_write.py`, `model-provisioning` gains `test_derivation.py` and
  `test_vocabulary_manifest.py`, `sheet` gains `flow.py` now that it owns `Schema`. Two preambles are
  rewritten: `comfy-transport` pointed at a module and a test file **deleted together in `8baf2b3` at
  v0.14** — a stale pointer, redirected to `generate.py`'s polling loop and `tests/test_generate.py`,
  and `comfy_types.py` added because the `ComfyTransport` Protocol its own sentence depends on lives
  there; `cli` claimed a model selection and range-checked dial flags that **do not exist** — there
  are no dial flags, dials live in `flows/summon-v1/flow.json`, and only `--seed` and `--count`
  validate at parse time. `CLAUDE.md`'s layout section and `README.md`'s repository-layout tree, which
  attributed four modules' work to the entry point, describe the six groups.

- **The package becomes six directories.** `foundation/` · `pipeline/` · `shared/` · `boundary/` ·
  `evaluation/` · `interface/`, with `isekai/__main__.py` left at the package root because `runpy`
  pins that path. Contents are unchanged: only paths, the import lines naming them, and one `.parent`
  per repo-root anchor. Each group carries a `README.md` of its files and who imports them, plus
  `isekai/README.md` over the six — **files and importers only**, because what a seam *is* belongs to
  the design record and neither should restate the other (design.md D11). Each group's `__init__.py`
  holds a docstring and **no code**: re-exporting through one is how a nested package acquires the
  import cycles this one has none of (design.md D2). D2 asks for an *empty* file; `ruff`'s D104 makes
  a byte-empty package init a lint error, so each carries the same one-line form `isekai/__init__.py`
  already used — which is not a re-export, and is the constraint D2 actually states.
  `pyproject.toml`'s two `[[tool.ty.overrides]]` paths follow `eval_backends.py` to its new home.

- **Five of the six stage→stage imports stop existing.** The `Schema` type moves from `sheet.py` to
  `flow.py` — a flow is what decides which schema a run is sorted against, and holding the type in
  the sorter made the sorter a dependency of the renderer. The six stage directory names —
  `CAPTIONS`, `SHEETS`, `REVIEW`, `PROMPTS`, `OUTPUTS`, `APPROVED` — move to `run.py`, which owns the
  layout, so a stage that needs another stage's directory asks the run instead of importing the
  stage. **Exactly one stage→stage edge survives**, and it is the behavioural one: `review` importing
  and calling `sheet.validate` (design.md D6). **Only the type's home moves** — striking its
  `version`, de-duplicating the vocabulary pin and redefining what a schema *is* are v0.16's, because
  those are observable. Consequence banked for v0.16: it changes the directory values in one file
  instead of five.

- **`show.py` → `run_view.py`, `photo.py` → `image.py`.** `show` was the verb *and* the file, and
  half of `photo`'s callers hand it a render rather than a photograph. Both are `git mv`, so
  `--follow` reaches back past the rename, and their test files move with them. **The CLI verb `show`
  does not change** — it is pinned by the entry-point tests, so the rename cannot reach the user
  surface. Root `evaluate.py` is listed in the change's impact but imports neither module; nothing
  there needed editing.

- **The parser, the verb table and the dispatch functions move out of `__main__.py`, which becomes a
  shim** — to `isekai/interface/cli.py`, after the restructure below. `runpy` pins where the entry
  point's *path* is, not where the parser lives, and a package's largest interface surface has no
  business being the one module outside the filing scheme
  (design.md D3). **The shim keeps its `if __name__ == "__main__":` guard**, a one-line departure from
  the snippet in D3: without it, importing `isekai.__main__` runs the parser, which exits 2 on an
  empty argv — and the `-S` guard that proves the entry point needs no third-party import does
  exactly that import. D3 names that risk; this is the line that discharges it. Callers move rather
  than being re-exported: `VERBS`, `build_parser` and `dispatch` are imported from `isekai.cli`.

- **`Wiring`, `wiring()` and `_check_run_root` are their own module** — `isekai/interface/wiring.py`,
  after the restructure below. The
  composition root had a second consumer that never sees an argv: the suite builds a `Wiring`
  directly, with no parser at all, in fourteen tests. A parser is one way to fill that dataclass and
  not the only one, so the module that owns the parser is not its home. `_check_run_root` travels
  with `wiring()`, its only caller, and `REPOSITORY` with it. **No compatibility re-export is left in
  `__main__`** — the three test import sites moved, and the name did not stay behind.

- **`write_atomically` is its own module** — `isekai/shared/atomic_write.py`, after the restructure
  below. It takes a path and bytes and
  knows nothing about runs, and it already had a consumer outside `run.py`: `generate.py` writes the
  rendered PNG with it — a file that is neither JSON nor numbered by the run's artifact convention.
  **`write_json` stays in `run`**, because `indent=2` and a trailing newline are a run's artifact
  format rather than a write primitive (design.md D4). The new module imports nothing first-party,
  which is the whole claim it makes. The move is not mechanical: `tempfile` was used at exactly one
  place, inside the moved function, so `run.py`'s import of it is now dead and removed — and
  `tests/test_run_directory.py`'s `run_module.tempfile` monkeypatch is retargeted at the module that
  actually holds the import. That test failed on the move rather than sleeping through it, which is
  what a detector is for.

## [0.14.0] - 2026-09-15

### Added

- **The 4:1 target ceiling is restored to the surviving render path.**
  `MAX_TARGET_LONG_SIDE` was enforced only inside `inject`, via `sys.exit`, and `generate.py`'s
  `photo_resolution` never applied it — **a live gap on `main`, not a regression this version
  introduces**, which deleting `inject` would have made permanent. It moves as a `Refusal` rather
  than a `SystemExit`, so a batch survives one extreme photograph the same way it survives one
  unreadable header. It bounds the **working** target, not the hires one: hires scales both axes by
  the same factor and so does not change the aspect ratio, and bounding the hires value would
  silently tighten 4:1 to 2.67:1 for a reason unrelated to aspect (design.md D4).

- **`--runs` can no longer write inside the repository working tree.** It has been a free
  `type=Path` since it was introduced, while the comment beside it claimed a containment check that
  existed nowhere — and `run.py` copies the photograph into the run directory by construction, so
  such a directory holds personal photographs one `git add` from being published. The rule **bounds
  the working tree, not the filesystem**: a run root resolving inside this repository and outside
  `.data/` is refused before any run is created, naming the path given and what would be accepted,
  while any path outside the repository is still accepted, because version control cannot reach it
  and that is what keeps a run on another disk expressible (design.md D7). The repository root is
  taken from the module's own location rather than the process's working directory, so the same run
  root is not legal or illegal depending on where the operator was standing. **The requirement is
  the part that closes it** — the claim sat in a source comment for a whole version and was false
  that whole time because no scenario held it.

- **`infra/up.sh`'s readiness wait is bounded, and tears the pod down itself on timeout.** The poll
  was `while true … sleep 5` with **no deadline at all** — the one thing in this repository that
  could bill indefinitely while looking like it was working, which cost two sessions on 2026-09-08.
  It now has a 420 s deadline and calls `infra/down.sh` when it expires, because a bounded wait that
  leaves the meter running has not solved the problem it was added for: teardown is the act that
  stops the billing. 420 s rather than 180 s, because the pod is not usable until the image has
  pulled and ComfyUI has started — a shorter deadline tears down healthy pods mid-boot.
  **The prototype's companion HTTP-proxy fallback is deliberately not taken**: that proxy is a
  public, unauthenticated endpoint and ComfyUI has no auth, so a version adopting it must put
  authentication in front of ComfyUI first (design.md D10). The bounded wait only removes exposure,
  which is why one half crosses and the other does not. v0.14 is the only version in the arc with no
  GPU phase, so it is the one place this work does not compete with a version's own metered risk —
  and every version after it needs a pod to accept.

### Changed

- **`.data/` is now the only root anything is generated into, and `outputs/` is gone.** It had two
  producers: the render path this version deletes, and `baseline/build_contact_sheets.py`, which
  pastes the reference photograph beside the renders and is therefore pixels twice over. The
  labelling aid is repointed — `--renders` defaults to `.data/baseline` and its sheets are written
  under `.data/labels` — so D14's *"nothing generated is outside the one ignored root"* is literally
  true rather than true of the pipeline and not of the tool beside it. **`.inputs/` stays**: it holds
  source photographs an operator puts there by hand, which is an input rather than something
  generated, and v0.13's comment was wrong to schedule it for deletion.
- **`CLAUDE.md`'s one-path bullet is replaced by the entry gate, not restored**, discharging the
  second deviation v0.13 declared and never performed. *"A selectable implementation is a measured
  one"* — because a **count** would forbid the flow registry v0.16 adds, and, which is the reason the
  rule existed at all, a count also permits an *unmeasured* single path, exactly what the deleted
  graph was. Twelve further stale sites are corrected, including the living spec's description, which
  still read *"four capabilities… a fifth, `model-provisioning`, on the v0.9 branch"* and is nine,
  named.
- **The README's work-in-progress banner names no version**, because `openspec/` is already cited as
  authoritative for what is being built next and a forward reference here is one reordering away
  from being wrong — which it already was. Every runnable command in the file is now one of the six
  verbs, and each was **verified against the actual parser** rather than written from memory.
- **The standalone evaluator records, in its own docstring, that it cannot read a run this pipeline
  produces.** Its reader wants a `run.json` of v0.12's shape and the current run frame writes none of
  those fields, so it already could not read a v0.13 run; what this version removes is the last
  producer of the shape it *can* read. A pre-existing gap made total, owned by the version whose
  whole content is the evaluation tool (design.md D13). Nothing under `tests/` imports it, so it
  fails no gate command — which is exactly why it is written where a reader will hit it.
- **`isekai/workflow.py` is `isekai/photo.py`, minus injection.** `PIPELINE_PATH`, `find_node`,
  `find_nodes` and `inject` are gone; the JPEG/PNG header walk, the EXIF transpose,
  `image_dimensions` and `working_resolution` survive as what they always were — *what is this
  photograph, and what render target does it imply*. Nothing that remains touches a ComfyUI graph,
  so `workflow` was a name that would lie. `working_resolution`'s docstring no longer justifies the
  short-side rule by *"the line-art ControlNet's floor"*: `summon-v1` has no LineArt node, and the
  rule holds on SDXL's own trained scale — the reason written beside it belonged to the deleted path.
- **`scale-precedes-every-consumer` asserts by role, not by class.** `summon-v1` has two `ImageScale`
  nodes — one on the photograph, one on the hires pass — so a class lookup is ambiguous against it,
  and the flow manifest is what names the photograph's. The test now reads the shipped graph and
  asserts the scaling node sits between the loader and **both** the identity node and the pose
  preprocessor, with nothing else reaching the loader.
- **The archive's one `.py` file is exempted from three type-checker rules, by literal path and
  permanently, in a block of its own.** `openspec/changes/archive/0010-illustrious-base/controlnet_probe.py`
  imports `isekai.pipeline._render` plus six names from `isekai.workflow`; this version deletes four of
  them and moves the other two, which turns `ty check` red on a file the repository forbids editing. An
  archived change records what was true at a past commit, and these rules ask whether it is true today —
  which the archive makes no claim about — so the exemption is permanent rather than a TODO. **design.md
  D5 predicted one rule and the tree needed three**: its measurement was made against a missing *member*,
  where `unresolved-import` is the whole story, while deleting the whole module makes `find_nodes` resolve
  to `Unknown` and raises `invalid-argument-type` and `invalid-assignment` downstream. The decision is
  unchanged — by literal path, permanently, as narrowly as the rules allow — so the three rules sit in a
  **probe-only block**, leaving the shared block to mean exactly *"files that bridge to wheels the gate
  deliberately does not install"*, which has no claim to cover against type errors.
- **`comfy-transport`'s two orphaned scenarios are rebound rather than deleted.** Polling and
  retrieval lost their only tests with `tests/test_polling.py`, but the behaviour is live in
  `isekai/generate.py`. The two tests move into `tests/test_generate.py` with `pipeline.run` swapped
  for `render`, carrying their keys. Deleting them would have deleted a requirement that is still
  true — the worst outcome available, and the one that looks cheapest.
- **The `-S` stdlib guard's falsifiability twin moves to the entry point it now falsifies.** The
  guard on `import convert` died with its target; its twin — *a check that cannot fail is not a
  check* — would then have sat in a file whose guard had gone, so it moves beside
  `tests/test_pipeline_cli.py`'s guards on `isekai.__main__` and `isekai.run`.
- **The suite's shipped-graph fixture reads `flows/summon-v1/graph.json`**, reached through the flow
  that declares it rather than through a path constant, so the fixture and the render path agree on
  which file the shipped graph is by construction. Five assertions the new graph invalidates are
  corrected with it: `summon-v1` uses `DWPreprocessor` alone, so it has no unclassified node classes,
  names neither the Tile nor the mistoLine ControlNet, and yields two annotator checkpoints, not four.
### Removed

- **Four model artifacts the old graph orphaned are dropped from the manifest, ≈2 GB.** The Tile and
  mistoLine ControlNets and the two `sk_model` LineArt annotators go from `scripts/models.json` and
  from `scripts/derive_manifest.py`'s `PINNED`, with `TTPlanet`, `TheMistoAI` and `lllyasviel`
  dropped from `PUBLISHERS` — no surviving entry names them. `summon-v1` uses `DWPreprocessor`
  alone. Nothing would have failed the gate had they stayed (`test_flow.py` uses a subset check); it
  would just have downloaded 2 GB nothing reads.
- **BREAKING — the old render path is deleted.** `convert.py`, `isekai/cli.py`,
  `isekai/pipeline.py`, `isekai/mutate.py`, `isekai/overrides.py`, `workflows/pipeline.json`,
  `workflows/pipeline_ui.json` and `comfy_types.Overrides` are gone, with the five test files that
  drove them. There is one render path — `python -m isekai … generate`, flow `summon-v1` — which
  discharges the suspension v0.13 took on *"there is one path."* It is deleted under **L3**, not
  because the new path beat it: a selectable implementation is a measured one, and
  `workflows/pipeline.json` was measured on style and rejected (F24) and never measured on identity
  at all. **No identity comparison between the two paths exists, on either instrument** — the record
  says so rather than implying a head-to-head that was never run.
- **The evaluator's two `pipeline.run`-driven report tests are deleted** with their driver. The
  surviving render path writes no `pod_image` key, so nothing else moves: `pod_image_of` and
  `table()` keep their signatures and `evaluation:report:names-its-run` keeps three passing tests
  that build their inputs directly. That the standalone evaluator can no longer read any run this
  pipeline produces is a pre-existing gap this version makes total, recorded for v0.18 rather than
  repaired here (design.md D13).

### Fixed

- **`up.sh`'s timeout teardown is spelled from the repository root**, not re-derived from `$0` after
  the script has already moved there. The second `dirname "$0"` read a path relative to the
  *original* working directory against the new one, so `bash isekai/infra/up.sh` from a parent
  directory resolved the teardown to `<parent>/isekai/isekai/infra/down.sh` — which does not exist,
  and under `set -e` kills `up.sh` before its `exit 1`, leaving the pod billing. That is precisely
  the failure the bounded wait was added to prevent: teardown is the act that stops the meter, so a
  teardown call that cannot resolve is the whole feature missing. A structural test now pins the
  call to a path that does not depend on how the script was invoked.
- **Three spec defects the deletion left behind are closed in the change's delta.** The header tests
  for `image_dimensions` were rekeyed onto `dimensions-are-written-by-injection`, a scenario the
  delta itself says does not migrate — six parametrised cases that looked bound and were bound to
  nothing, in a repository with no binding checker. The surviving half of that scenario — that the
  dimensions are *read* from the photograph's own frame header, because nothing else can supply
  them — is stated as `image-generation:working-resolution:dimensions-come-from-the-header` and the
  tests carry it. `cli`'s pipeline-surface requirement, which mandated a *second* entry point
  standing beside the single-command render surface and leaving it unchanged, is modified and
  renamed to the only entry point. `model-provisioning`'s completeness rule, stated over the deleted
  `workflows/pipeline.json`, is restated over a tracked flow's graph — which is what its bound test
  already reads.

## [0.13.0] - 2026-09-15

### Fixed

- **`outputs/` and `.inputs/` are gitignored again, and a test says so.** D14's single ignored root
  replaced both lines, but the render path this version deliberately does *not* touch still writes
  them: `isekai/cli.py` defaults `--output` to `./outputs`, and `baseline/build_contact_sheets.py`
  reads renders from `outputs/baseline` and **source photographs** from `.inputs/baseline`. Both hold
  a person's likeness by construction, so for the length of one `git add .` the repository's hardest
  invariant depended on nobody typing it. The `.gitignore` route rather than repointing the producers,
  because this version promised not to touch them; the lines go in the commit that deletes them.
  `git check-ignore` is now run over one path per producing directory, so a rule that reads right
  while matching nothing fails the gate.
- **The rendered PNG was the one artifact written non-atomically.** `rendered_seeds` treats the
  presence of `<seed>.png` as proof the seed is done, so an interrupted write left a truncated image
  that resume skipped forever — on the single stage that costs money on every pass, and in direct
  contradiction of this version's own "written atomically or not at all" requirement. It goes through
  `write_atomically` like every other artifact now.
- **`generate` on a run approved for nothing printed nothing and exited 0.** `prepare` iterated only
  the flows a run was already approved for, so the refusal naming `review` → edit → `approve` was
  unreachable from the command line: the scenario was proved by a test calling one function directly
  while the shipped surface did the opposite. It refuses when none of the flows asked for has an
  approved sheet, and the binding is at the CLI now. Selecting among several approved flows still
  needs no flag — the refusal fires only when there is nothing at all to render.
- **One unreadable photograph header no longer kills the batch mid-render.** `image_dimensions`
  belongs to the untouched render path and stops the process with `sys.exit`; `across` collects
  `Refusal` and a `SystemExit` walks straight past it, so a truncated header ended the whole batch
  after the pod was rented and wrote no error record. The header is now read during *assembly*, which
  is the free pre-rental step, and the read inside the render loop is a refusal the stage records.
- **The vocabulary was manifested and verified but nothing fetched it**, which left the proposal's own
  motivating defect — "a fresh clone cannot fill a sheet at all" — open. `scripts/download_models.sh`
  takes the manifest as its one optional argument, so
  `bash scripts/download_models.sh scripts/vocabulary.json` provisions the tag list through the same
  plan → verify → land path as everything else; `provision.py` keeps the default so the shell has no
  second copy of it. An absent tag list is a refusal naming that command rather than a
  `FileNotFoundError` naming a path.

### Removed

- **The absent-models preflight, requirement and all** (design.md D15). It was real code bound to a
  real scenario that no production invocation could reach: `Wiring.present` was populated by nothing
  but tests, and nothing could populate it — a flow declares destinations like
  `insightface/models/antelopev2/glintr100.onnx`, and ComfyUI exposes no endpoint that lists a volume.
  `/object_info` reports each loader's enum per category folder, which cannot see the InsightFace
  models or the annotator checkpoints at all, and a preflight over the half it *can* see would report
  "present" for a flow about to fail on the half it cannot — a false guarantee on the stage that costs
  money. The check that catches the mistake a human actually makes stays and needs no endpoint: the
  gate binds every tracked flow's declared artifacts to `scripts/models.json` and to its own graph, in
  both directions.

### Added

- **The acceptance run: five photographs, end to end, on a rented GPU.** Photograph → prose →
  machine-filled sheet → approved artifact → assembled prompt → anime render, with nothing
  hand-captioned anywhere in the chain. **The seam this version exists to cross is crossed.**

  One pod session, `pi7jqpvla6daz6`, RTX PRO 4500 Blackwell (32 GB) in EU-RO-1 on
  `ghcr.io/alxb1t/isekai:latest`, with `scripts/models.json` copied up so the upscaler this version
  added was provisioned: **16/16 artifacts present and digest-verified**. Created 21:24:49,
  terminated 21:36:35 — **11 min 46 s**, and `infra/down.sh` reported billing stopped. Teardown
  confirmed through the RunPod MCP, which returned `{"pods": []}`.

  **Cost ≈ $0.141** at the type's $0.72/hr secure rate, against a planned $0.058 and a $0.30
  ceiling. The gap is the GPU type, not the duration: the preference list's first entry is a
  Blackwell at roughly twice the rate the estimate assumed, and it had capacity. Rendering itself
  was 6 min 39 s for five images — the first took 2 min 30 s cold, the rest about 45 s each once
  the checkpoint was resident.

  **What the renders show.** Every scored criterion survived on all five, including the two hard
  framings: `back` rendered `from behind` + `looking back` + `arm up` with `gradient hair`,
  `overall shorts` and `nail polish`, and `lying_side` rendered `lying` + `on side` +
  `arm over head` + `barefoot` at 3264x1536. `cowboy-shoot-2`'s `mole on cheek` is on the cheek.
  The 106-token prompt's tail survived the encoder window rather than being lost to it.

  **What they also show, and this is the finding worth keeping.** Every junk tag drew itself,
  exactly and without mercy. `collar` — meant as a blouse's stand collar — became a studded choker.
  `faucet`, `counter` and `chandelier` turned a bathroom into a ballroom. And a colour the reader
  *did* see was lost between stages: "black crop top" reached the sheet as `crop top` with no
  colour, and rendered teal. All five were approved **unedited**, recorded as `edited: false`, so
  this is the control arm the correction gets measured against — and it is the clearest possible
  argument for stage ③ existing at all.

### Fixed

- **`infra/up.sh` sent a comma-separated GPU preference list as one enum value**, so pod creation was
  rejected outright with the whole enum echoed back. `RUNPOD_GPU_TYPE` is an ordered preference — the
  API takes a list and picks the first with capacity, which is what stops a metered session dying
  because one model is sold out in one datacenter — and it is now split into an array, trimmed, with
  empty entries dropped. Found at the top of v0.13's metered phase; no pod was created and nothing
  was billed.

### Fixed

- **`generate` rendered before the batch was assembled, and a dead endpoint was a traceback.** Both
  found by v0.13's acceptance run. The CLI dispatched per photograph, so it assembled one prompt and
  immediately reached for the endpoint — which is exactly the failure the "assemble the whole batch
  first" rule exists to prevent, since a malformed third sheet would have been discovered after a
  machine was already rented. The unit test covered `prepare` per run and never the CLI's ordering;
  it does now, by asserting every "assembled" line precedes every "rendered" one.
  `--server` also no longer has a default. Assembly is free and rendering is not, so the invocation
  that costs money is the one that names where to spend it: `generate` without `--server` assembles
  every prompt and stops. And a transport-level network error is now a refusal naming the tunnel and
  `infra/up.sh`, rather than a `urllib` traceback naming a socket.

### Fixed

- **The sorting briefing taught two phrasings the mapping cascade drops.** Found by v0.13's own
  acceptance run, on five photographs out of five: `count` came back empty every time and `gaze`
  came back as `camera`. The cause was the briefing's own worked examples, which showed
  `count: ["one person"]` and `gaze: ["looking at the camera"]` — a worked example is the strongest
  instruction in a briefing, and both of those map to nothing usable. `camera` is worse than
  nothing: it is a canonical tag meaning *a camera is in the picture*, so every one of those renders
  would have had a camera drawn in it. An empty `count` also loses `solo`, the Danbooru mode
  selector.
  The examples are rewritten in the vocabulary's own spellings, taken from the prototype's
  hand-written sheets — `1girl, solo`, `looking at viewer`, `upper body` — and a test now walks every
  phrase the examples emit through the cascade and fails on any that maps to nothing. The field list
  gives the canonical vocabulary for the three fields where English and Danbooru diverge most, and
  the register rule is stated outright: write the label, not the sentence, and never name the
  photographer's equipment in place of the subject's attribute, because what is named is what gets
  drawn.
  Curated bridges catch the same cases where the briefing does not take — two defences, because one
  of them is a document nothing can test.

### Added

- **The six verbs now dispatch.** `isekai/__main__.py` gains a `Wiring` carrying the reader, the
  sorter, the transport, the schema, the vocabulary and the run root — every one of them a seam
  something is actually passed through, which is what makes the resume assertion provable with no
  GPU and no network. An argument is a photograph to open or a run id to resume, decided by what is
  on disk rather than by a flag. One bad identifier does not stop the rest of a batch; every refusal
  is collected, printed to the error stream, and the exit status says whether any fired.
- **The resume test: every command, twice.** Not one byte of the run directory differs and not one
  external call is made — a number, not a hope, because the doubles count their calls. A companion
  test asserts the first pass actually produced a caption, a sheet, an approved artifact, a prompt
  and a render, so the resume claim cannot pass vacuously.
- **A refusal audit across every stage.** Each refusal added in phases 2–7 is provoked and checked
  for a remedy this build can actually perform, and for the absence of ones it cannot — no
  `isekai migrate`, which is exactly the verb it would be most natural to promise and is deliberately
  absent, because only schema version 1 exists and its dispatch table would have no entries.

### Changed

- **`review` and `approve` are inert on a second pass.** Re-running `review` on an already-approved
  flow used to open a new draft, which made resume *write*. Both now do nothing without
  `--new-version`, and `approve` with nothing to approve reports completion rather than refusing —
  resume must not exit non-zero. Appending a corrected draft is still one flag away, and the approved
  artifact it starts from is untouched.

### Added

- **Stage ④ — `isekai/flow.py`, `isekai/generate.py` and `flows/summon-v1/`.** A flow is a directory
  whose manifest *declares* and never computes, which is what lets a broken flow be caught by the
  suite rather than after a pod boot and several minutes. It names its inputs, its schema, its
  vocabulary, its graph, its prompt fragments, its dials and every model artifact it needs.
- **The flow's dials are the measured ones, not its graph file's.** `summon-v1`'s graph carries the
  prototype's committed cfg 7 and identity strength 0.5; every measured run overrode them to 5 and
  0.8, and a test asserts the two disagree — a manifest transcribed from the graph would ship a
  configuration nothing measured.
- **A flow is immutable, pinned by equality.** The suite holds each tracked flow's whole directory
  against a committed digest. Changing a dial, a prompt fragment or the graph fails the gate naming
  the flow and saying that a changed dial means a new flow identifier — because an output's path
  identifies a configuration only if an identifier never silently means something else.
- **Assembly is pure, local and happens before any endpoint is acquired.** The prompt is the flow's
  prefix, the sheet's fields in the schema's order, and the flow's trailer; nothing is taken from the
  graph's own committed strings. A malformed sheet costs nothing instead of a boot, and one bad sheet
  does not stop the rest of a batch.
- **Only an approved sheet renders**, and every flow with an approved artifact renders without a
  flag. Seeds are drawn from an injected source or named explicitly, never both — one verb explores
  and the other reproduces — and the parser refuses the combination before any work begins. An output
  is named by its seed under its sheet version, which reproduces an *image* rather than an ordering.
- **Rendering is idempotent per image.** An existing seed is skipped from a directory listing, and a
  raised count renders only the shortfall. Provenance carries the flow, the seed, the sheet version,
  the submitted graph's digest and whether the sheet was edited. (A volume preflight shipped in this
  phase and was **withdrawn at converge** — see *Fixed*, below.)
- **`isekai show`** — the run's artifacts, the active version per stage, approval where it applies,
  and what produced each one. It reads files where control flow reads listings, which is why no
  progress file ships: nothing but a human is watching before a review UI exists.
- **`RealESRGAN_x4plus_anime_6B.pth` joins `scripts/models.json`.** The hires pass needs it and
  nothing provisioned it. Its publisher hosts no Hugging Face repo *and* publishes no digest — the
  release predates GitHub's asset-digest field — so the derivation fetches the publisher's own bytes,
  hashes them, and holds all four mirrors against that: derived, never transcribed, in the entry
  where a transcribed constant would be least checkable. Its BSD-3-Clause terms join the licence
  record. `scripts/eval_models.json` is unchanged.

### Added

- **Stage ③ — `isekai/review.py`: the correction, on a copy, approved by a rename.** `review` copies
  the highest sheet into `review/<flow>/` as a draft and records which sheet version it came from;
  `sheets/<flow>/` is never written to again by anything. That separation is what makes "the
  machine's sheet is never edited" a property of the layout rather than a rule a tool is trusted to
  follow — and the machine's raw sheet is the baseline the correction is measured against, since the
  unreviewed route carries 0.568 of a sheet's attributes into the render and the reviewed one 0.917.
  Reviewing again starts from the last thing the operator approved, not from the machine's first
  attempt, and leaves the approved artifact exactly as it was.
- **Saving is not approving.** A draft is parkable half-edited for as long as the operator wants, a
  repeat `review` does not overwrite it, and a draft is reported as *not* complete — approval is its
  own act and is what a directory listing reads.
- **Approval validates, then renames.** Every tag is checked against the vocabulary, because a tag
  that merely looks canonical passes every later check on its way into the prompt and this is the
  last place to catch it. The refusal says the tag is not in the vocabulary's *prediction set*,
  which is what is true — that set is a subset of the wider tag corpus, so calling an absent tag
  unreal would overclaim. An approved artifact is never overwritten; a correction is the next number.
- **The token window warns rather than refuses.** The assembled prompt is estimated against SDXL's
  77-token encoder window; over it, a warning states the estimate and the window and approval still
  succeeds. Sheets already ran past it with nothing saying so, so every one was being silently
  chunked and averaged — but the sheet is the record of what the render was *asked* to contain, and
  deleting fields to fit would make "did this criterion survive" unanswerable at the moment it is asked.
- **The approved artifact records whether a human changed anything**, computed against the source
  sheet rather than declared by the operator. Whether a sheet was actually corrected is the
  difference between the two routes above, and a flag somebody sets is an assumption in a fact's
  clothes. Approving unedited is a legitimate, recorded act — it is how the machine's raw draft gets
  rendered as a control.
- **This stage writes no error record and consumes no retry budget.** There is no batch and no
  unattended retry here: the operator is present by definition, and a refusal is a message to them
  rather than state for a later resume to reason about.

### Added

- **Stage ② — `isekai/sheet.py` gains the sorter, the fill and the write.** Prose, a schema and a
  vocabulary in; canonical fields out. The stage is never told which flow asked, which is what lets
  one fill serve every flow declaring the same schema and vocabulary — a second flow added later
  costs one call, not two, and the first flow's sheet is left exactly as it was. The sheet records
  the vocabulary's name, revision and digest, and its producer names the caption version it sorted.
- **`schemas/identity.v1.briefing.md`** — the routing rules and two worked examples, written in the
  schema's own identifier-safe field names. Both examples show absence clauses producing empty
  fields, and details with no field being dropped rather than forced somewhere.
- **The sorter's invocation constrains structure, not wording.** `--tools ""` and a `--json-schema`
  carrying exactly the schema's fields, required, with no additional properties and no `enum`.
  Constraining generation *to the vocabulary* was measured and rejected: token-prefix masking lands
  on the nearest tag sharing a prefix rather than the one the model meant, which turns a visible
  failure into an invisible one. A response that does not carry the schema's fields is a permanent
  failure — the structure was stated in the request, so another attempt would spend for nothing.
- **`isekai/claude_cli.py` — the pipeline's one network boundary.** The locked-down invocation, the
  envelope, the failure classification and the absent-binary refusal now live in one module that
  both stages reach through, rather than in the first stage that happened to need them.

### Fixed

- **The reader is now told where the photograph is.** Stage ①'s adapter passed the path as a
  trailing positional after `-p`, which the CLI's argument parser silently drops — the reader would
  have been told to describe a photograph and never told which one. The path travels in the prompt;
  `--add-dir` is what grants the read. Verified against the real binary, which also confirmed the
  envelope's shape: `api_error_status` and `permission_denials` now feed the classifier, and a
  single envelope really does report two models, as the design said it would.

### Added

- **Stage ① — `isekai/caption.py`, a photograph in and prose out.** The reader is handed exactly two
  things, the photograph and its standing instructions, and is told nothing about schemas, fields,
  vocabularies or flows: pressing a reader into a schema is measured to make it invent — told never
  to leave a field blank, one manufactured nineteen identity marks across seven of ten subjects and
  its score fell from 0.518 to 0.307. The reader is licensed to state absence and this stage does
  not strip it; turning a licensed absence into an empty field belongs to stage ②, and naming where
  that happens is the point of allowing it here.
- **`briefings/caption.md`** — prose only, with absence explicitly licensed, and no schema field
  name anywhere in it, asserted by a test rather than by intent.
- **The `claude -p` adapter, locked down.** `--safe-mode` (so the CLI does not inject sixteen
  kilobytes about *this repository* into the context that should describe a photograph),
  `--tools Read` (a stage that can run shell commands is not a stage),
  `--permission-prompts none` (so a misconfigured stage cannot wait for a human forever),
  `--strict-mcp-config`, `--no-session-persistence`, and the JSON envelope always — the envelope is
  what carries the error status, the stop reason and which models actually ran.
- **Failure classification read off the envelope.** A rate limit, a server error or a timeout is
  transient and spends the budget; a decline, a denied permission or a response that is not prose is
  permanent and is never retried. No fallback reader: substituting one would write an artifact whose
  provenance record is untrue. The producer records the models that *ran* rather than the flag that
  was passed, the digest of the briefing text, and `pinned: false`, because a hosted CLI exposes no
  revision and a revision field that would be untrue is worse than an honest absence.
- **An absent `claude` binary is a refusal naming the install command**, and it leaves the run
  directory exactly as it found it.

### Added

- **`isekai/vocabulary.py` — the tag list as an object, and the four-pass cascade over it.**
  `load` reads the provisioned `selected_tags.csv` with the stdlib `csv` module, keeps the general
  tags only, normalises underscores to spaces, and verifies the bytes against the manifest before
  parsing them. The cascade maps a phrase by exact match, then the *field's* suffix — passed in
  from the schema rather than looked up by field name, which is what makes the mapper genuinely
  independent of the field list — then a curated pass that consumes the span it matched and
  carries on, then containment requiring every word of a candidate tag. An empty result is a real
  answer: no nearest neighbour is ever substituted. Absence clauses are dropped whole, because a
  positive prompt has no negation and "no tattoos" passed through becomes tattoos drawn. No pass,
  the curated table included, can emit a tag the vocabulary does not carry.
- **`schemas/identity.v1.json` — the field list as a versioned data file.** Sixteen fields in
  prompt order, the seven that are scored, the per-field suffix convention, and the vocabulary the
  schema is written against. Field names are identifier-safe slugs because the structured-output
  flag becomes a tool input schema at the API, which enforces `^[a-zA-Z0-9_.-]{1,64}$` on property
  keys; a name that would fail it is refused at load.
- **`isekai/sheet.py` — the schema reader and the sheet's validation.** A sheet is fields and
  nothing else: an assembled prompt in it is refused, a missing field is refused and told to add an
  empty one, and an empty field is legal. A tag outside the vocabulary's prediction set is refused
  with that as the reason, because the base model was never trained to draw it.

### Added

- **`python -m isekai` — a second entry point, with the pipeline's six verbs.**
  `caption` · `sheet` · `review` · `approve` · `generate` · `show`, under one parser in
  `isekai/__main__.py`. It is additive: `convert.py` and `isekai/cli.py` are untouched, and a test
  asserts that importing the pipeline's entry point does not pull the render surface in. A second
  stdlib-only subprocess guard joins the existing one — the falsifiability twin that proves `-S`
  really refuses a third-party import is unchanged and now covers both.
- **`isekai/run.py` — the run directory, the only thing the four stages share.** A run is
  `.data/runs/<photo-id>/`, identified by a prefix of the photograph's SHA-256 plus a sanitised
  filename stem, with the photograph *copied in* rather than pointed at and its digest, size and
  media type recorded in the frame. Resumption keys on the bytes, not the id, so a renamed
  photograph resumes its own run and a digest-prefix collision is refused rather than silently
  mixing two people's photographs. The extension is derived from the header, so a PNG named `.jpg`
  is stored as what it is.
  Artifacts are numbered per directory, written temp-then-replace, and never overwritten; every
  "is this done?" test is a directory listing, with approval read from the filename. A failure is
  recorded as a *sibling* of the artifact it failed to produce — `001.error.1.transient.json` —
  so it never consumes the version number, and its kind and attempt ordinal are in the name so the
  retry decision stays a listing. Retry budgets are three for reading and sorting, one for
  assembling and one for rendering; a permanent failure is never retried, and one photograph's
  failure does not cost the rest of a batch their turn.

### Added

- **The tag vocabulary is a provisioned artifact with its own manifest.**
  `scripts/vocabulary.json` pins `wd14/selected_tags.csv` — 10,861 Danbooru tags with their post
  counts, 8,106 of them general — at an immutable revision, digested by fetching and hashing
  because at ~300 KB it is not stored as a large file and Hugging Face publishes no SHA-256 to
  read. It used to arrive as a side effect of downloading a tagger this repository does not load,
  on a mutable reference, so a fresh clone could not fill a sheet at all. Derived by
  `scripts/derive_vocabulary.py`, and held to the same pinning, digest and mirror checks as the
  other two manifests.
- **`scripts/manifest.py` — one derivation module behind all three manifests.** It carries the
  entry types, both digest strategies and the writer; each deriver is now a table of what to pin
  plus a `derive()`. The entry spec had been declared twice, under one name, with two different
  shapes, and a third deriver is how that becomes a defect rather than an oddity. Verifiable for
  nothing: `scripts/models.json` and `scripts/eval_models.json` are byte-identical after a re-run.
- **`isekai/refusal.py`.** `Refusal` moves out of the evaluator's module so the pipeline can raise
  it without loading several hundred lines of scoring rules; `isekai.evaluate` re-exports it, so
  both existing importers resolve unchanged.
- **The vocabulary's licence is recorded** in `scripts/eval_licences.md` — Apache-2.0, the URL it
  was read at, and the date. That record is now stated to be one note for every artifact this
  repository pins, rather than one per manifest.

## [0.12.0] - 2026-09-07

### Fixed

- **The pose reader's input now matches what the pinned artifacts are published to be fed.** Three
  deviations from `comfyui_controlnet_aux`'s reference pipeline — the one that publishes
  `dw-ll_ucoco_384_bs5.torchscript.pt` and `yolox_l.onnx`, and the same preprocessor the graph's own
  OpenPose branch runs on the pod: the person crop was **stretched** to 288x384 where the reference
  applies an aspect-preserving affine over a **1.25-padded** box; the crop was normalised
  `(x - 127.5) / 127.5` where the reference uses **ImageNet mean and standard deviation**, the same
  convention `SegformerParser` in that file already used; and `yolox_l` was fed **RGB** where its
  reference feeds **BGR**. All three are corrected, and the keypoints are mapped back through the
  inverse of the window they were read in.
- **The pose axis was recomputed over the thirty committed renders, locally and for nothing.** Only
  the pose axis moved: every other axis in all thirty `*.eval.json` records came back byte-identical,
  which is what makes this a recomputation rather than a new measurement. **The saturation finding
  stands** — PCK median **1.000**, twenty-one of thirty at exactly 1.000, min now 0.976 — and it is now
  attributable to the pipeline rather than to the reader. The correlation's pose row moves from
  **0.286 (4/14)** to **0.636 (14/22)**, *p* = 0.286, interval 0.427 – 0.845: still a coin flip, and
  every 95% interval in the table still contains 0.5. `baseline/correlation/agreement.json` and both
  `baseline` READMEs carry the recomputed figures.
- **A run records the container image it was rendered on, and the report reads it.** The table's
  fourth line read `manifest.get("image", ...)`, a key nothing ever wrote — `renders[].image` is a PNG
  filename — so every real table printed `image: unrecorded` while the unit test, handed a literal,
  printed a tag. `run.json` now carries `pod_image`, `convert.py` takes `--pod-image` (defaulting to
  `$RUNPOD_IMAGE`, the same variable `infra/up.sh` boots from), and the table is now proven against a
  manifest the pipeline actually wrote rather than against a literal. A run that was not told records
  `null` and the table says `unrecorded`: nothing guesses at a tag, and the required command line is
  still `convert.py photo.jpg`.
- **`run.json` now carries D14's other half: the ComfyUI commit.** D14 promised the manifest would
  record the image *and* the commit; only the image landed, and the commit existed solely as prose in
  `baseline/README.md`, which no run writes and nothing can read. `convert.py` takes `--comfy-commit`
  — what `git -C /opt/ComfyUI rev-parse HEAD` reports on the pod — and `run.json` records it beside
  `pod_image`. **No environment default**: nothing in `infra/` or `.env.example` exports a commit, and
  inventing a variable for it would be a second place to keep in step. A run that was not told records
  `null`; `/system_stats` reports a version string, not a commit, so nothing derives one. The tracked
  `baseline/runs/*.run.json` are **not** backfilled — they stand as the metered session's code wrote
  them.
- **Both provenance values are bounded and filtered where they enter.** `--pod-image` and
  `--comfy-commit` are recorded verbatim and printed verbatim, so a newline emitted a line into
  `eval.txt` indistinguishable from a real header and an escape sequence reached the terminal unread.
  Both now go through one argparse type at `parse_args` — printable ASCII, at most 256 characters —
  which `argparse` applies to the `$RUNPOD_IMAGE` default on the same line as the typed flag, so the
  source likeliest to arrive unreviewed is checked on the same rule.
- **The scorer's manifest destination goes through the provisioner's containment check.**
  `eval_models.resolve` joined `dest` onto the models root directly, a second enforcement site beside
  `provision.resolve_dest`, which exists precisely so the containment rule (design.md D7) has one. It
  now routes through `resolve_dest` and raises `EscapingDestination` rather than falling through. Not
  an exploit path closed — every caller passes a literal and `entry_for` matches by equality — but the
  invariant now has one site rather than two, with the traversal case bound in
  `tests/test_eval_manifest.py` as it is in `tests/test_provision.py`.
- **Three pieces of committed prose that described something other than what the code does.** The
  guard's persisted detail string said "landmark-centroid offset" for what is a face **bounding-box**
  centroid — no detector in this tree produces landmarks — so it now says "face-box centroid offset",
  and `baseline/README.md`'s row is relabelled with it; **no number moves and nothing is regenerated**.
  `eval_backends.py`'s module docstring documented per-line `ty: ignore[unresolved-import]` markers
  that a `[[tool.ty.overrides]]` block in `pyproject.toml` replaced, so a contributor following it
  would have turned the gate red; it now points at the override and says why the markers cannot be
  right in both environments. And the pose-saturation passages called metric ties "most" of the
  within-subject pairs when `agreement.json` records 18 of 40, a **minority** — both now say what
  `baseline/correlation/README.md` already said.
- **The v0.12 pod identifier is redacted from `baseline/README.md` to `<pod id>`.** Account-scoped
  rather than secret, and the pod is destroyed, but it carries no reader value. The timestamps, wall
  clock, rate and cost, and the RunPod MCP `list-pods` / `get-pod` 404 that **confirms teardown** all
  stay: those are what the metered-session protocol requires.

### Added

- **The guard's authoritative method is settled by measurement: box IoU.** Both methods were computed
  on all thirty baseline renders at the working denoise of 0.65 and **both hold** — IoU median 0.950
  against a 0.30 floor, face-box centroid offset median 0.012 against a 0.25 ceiling, 30/30 either
  way. So D9's pre-committed fallback, where neither holds and the region axes refuse, did not fire.
  IoU ships because it constrains **size** as well as position: a correctly-centred face at three
  times the scale passes the centroid test and fails IoU, and a test asserts exactly that. It is pinned as
  `AUTHORITATIVE_GUARD_METHOD` and the method not chosen is still computed and printed on every run, so
  the day the two disagree is visible rather than silent.
- **StyleID carries real signal but does not separate cleanly, and n=6 cannot license it.** Across 30
  same-subject and 150 different-subject pairs: AUC **0.847**, medians 0.467 against 0.207 — a long way
  from a coin flip. But 98 of 150 different-subject pairs score at or above the worst same-subject
  pair, and **two of six subjects are nearer somebody else's renders than their own**. The probe could
  have killed StyleID and did not; it cannot license it either, and no threshold is set. StyleID
  outscores ArcFace on both AUC and separation, consistent with the roles D8 assigns them.
- **DWPose reads all thirty renders — and the pose axis is saturated.** PCK median **1.000**, min
  **0.976** (recomputed at converge, see *Fixed*). The OpenPose ControlNet at strength 0.6 holds pose so
  tightly that at fixed dials this axis has **almost no variance** — twenty-one of thirty renders sit at
  exactly 1.000, so 18 of the 40 within-subject pairs are exact metric ties and only 22 could be
  scored at all. The axis is **not** removed: probe 3 asked whether DWPose could read these renders
  and it can, so nothing was killed by the probe it was given, and
  deleting the column would hide that it was measured. It should become informative the moment the pose
  strength is searched, which is v0.13's business.
- **No axis was removed and no dial was moved to make a meter work.** `denoise` stays at 0.65 and the
  guard was measured at the denoise the product actually uses.
- **`s5`'s refusal path was not exercised.** It was chosen as a refusal-path subject and the detector
  found its face in all five of its renders — the batch's lowest IoU at 0.857–0.898, but far above the
  floor. The absent-face and guard-failure paths remain covered by unit tests and by nothing in the
  baseline. Stated as a gap rather than papered over.
- **Thirty fixed-dial renders, from one metered pod session: 19 min 58 s, ~$0.24.** Six subjects × five
  seeds on the already-built `:v0.11-rc`, so rebuild drift is held constant rather than measured. These
  are **the first renders this project has ever produced with the graph's committed dials** — within a
  subject they differ in exactly one thing, which is what makes them a baseline rather than thirty
  samples of a distribution. Planned against 25 min against a 45 min ceiling; the estimate derived from
  v0.11's session was right to within a minute. Teardown confirmed through the RunPod MCP with the
  response transcribed in `baseline/README.md` — `list-pods` empty and `get-pod` a 404.
- **The landscape gap is closed on a GPU, not just on paper.** `s6` rendered at **1536×1024**, an aspect
  ratio this pipeline had never produced, and every one of the thirty renders' dimensions equals the
  target the injector computes from that subject's own photograph. Every `run.json`'s `photo_sha256`
  matches the digest the builder recorded, so each batch is provably the subject it claims to be.
- **`RUNPOD_IMAGE` was set to the release candidate for the session and cleared immediately after**, so
  no later pod silently boots an unreleased image. The renders arrive over the tunnel and are written
  locally by `convert.py`, so nothing ever lived only on the pod's ephemeral disk — and they were
  verified complete *before* teardown rather than after.
- **The run manifests are committed and the pixels are not**, following v0.10's and v0.11's precedent:
  this repository claims reproducibility over the submitted workflow JSON, never over pixels.
- **`baseline/build_subjects.py` and the six subjects it produces**, given `probe/build_inputs.py`'s
  treatment because one version does not silently reverse a convention the previous one wrote down: a
  tracked recipe, digests recorded in `baseline/README.md`, **pixels not committed**. Two consecutive
  runs produce byte-identical digests, which is the only thing that makes a recorded digest worth
  recording.
- **Each subject earns its slot adversarially, not representatively.** Two controls that differ in hair
  colour so they are not one case counted twice; two multi-tone subjects that stress the
  dominant-colour metric in *different* ways — one by extreme dark-root-to-blonde bimodality, one by a
  small hair region rather than a large one; one full-length figure whose face is ~1.3% of the canvas;
  and one landscape. Four are labelled in phase 9 (4 × 10 within-subject pairs = 40) and the two
  refusal-path subjects are not, because a subject whose axes are expected to refuse cannot calibrate
  anything.
- **The landscape gap v0.11 named is closed.** The source set is entirely portrait, so `s6` is derived
  by cropping, reusing v0.11's own 832×554 landscape geometry — the crop origin keeps the face in the
  band, since a centred crop of a standing figure is a crop of its chest. It resolves to a
  **1536×1024** target, an aspect ratio this pipeline has never rendered.
- **All six were read by the real scorer on CPU before any pod was created.** Hair areas span 0.0198 to
  0.3104 — a factor of fifteen, every one above the 0.005 floor — so no subject refuses its region axes
  for lack of pixels before the renders exist. **`s5`'s refusal is therefore not yet demonstrated**:
  what was measured is the anime detector against a *photograph*, and whether it locates a face in
  `s5`'s stylized renders is a phase-8 question, left unprejudged.
- **The sources deliberately unused are recorded with their reasons**, so the selection is reviewable
  rather than asserted — one candidate was the same person and shoot as `s5`, and two others repeated
  the easy uniform-blonde case a control already covers.
- **Residual risk stated rather than discovered later:** if the source photographs are lost this
  baseline becomes unreproducible and the labels are the only surviving artifact, with the digests
  proving that some file once existed and nothing about what it contained. That is the accepted cost of
  not committing derived faces, and there is no mitigation beyond keeping the sources.

### Notes

- **The correlation, which is what v0.12 actually ships. No axis is shown to track the operator's
  eye.** Forty blind pairwise judgements against each axis separately, never rolled up, with the count
  beside every figure: `face_styleid` **0.450** (18/40), `face_arcface` **0.625** (25/40), `pose_pck`
  **0.636** (14/22), `hair_colour_delta_e` **0.425** (17/40), `hair_mask_area` **undefined**. **Every
  95% interval contains 0.5 and every binomial *p* is ≥ 0.15.** At n=40 the interval is ±0.155 — ±0.209
  on the pose row, which only 22 pairs could be scored on — so this could only ever have detected a very
  strong effect, and there was not one.
- **The primary face axis lands below a coin flip.** StyleID separates *different people* well enough —
  AUC 0.847 in phase 8 — and still cannot say which of two renders **of the same person** looks more
  like them. Those are different questions, and this version is what established that the second is the
  hard one. The highest agreement over all forty pairs belongs to `face_arcface`, the channel permitted
  to claim the least;
  at *p* = 0.154 that licenses nothing, and it is recorded so a later version can go looking.
- **`hair_mask_area` cannot participate by construction — a design defect this table exposed.** It
  reports the photograph's own mask area, so it is identical for every render of a subject and every
  within-subject pair is a tie. It is left in the report rather than quietly dropped, because the
  report is what revealed the mistake.
- **This is a successful version by its own pre-committed criterion (D17): the correlation was
  computed, never that it was good.** Had v0.13 opened by searching `cn_strength` against
  `face_styleid`, it would have been optimising against a coin flip, at real money, and the result
  would have looked plausible. **This version cost ~$0.24 and prevented that.**

### What v0.12 does NOT establish

Drafted in `tasks.md` before any number existed, and reproduced here unchanged now that they do:

- **No metric here is shown to measure identity.** Four axes were built and none of them agrees with
  the operator's eye better than chance.
- **No score is comparable across bases or across batches.** An embedding cosine has no zero point
  across the photograph-to-drawing gap; it ranks within one batch on one base and nothing more.
- **No dial is shown to be better than another.** Nothing here compares dial settings at all.
- **`cn_strength` 0.5 is unsearched.** It is merely now *searchable* — settable, pinned, and recorded
  in every manifest.
- **Rebuild drift is recorded and unmeasured.** The baseline is pinned to `:v0.11-rc` so drift is held
  constant rather than quantified; `run.json` records the image so a later version can measure it.
- **There is no percentage, no verdict and no threshold**, and this version deliberately produces none.
- **Additionally, discovered rather than predicted:** the guard is shown not to produce false refusals,
  but is **not** shown to catch a recomposed render, because no render recomposed. And `s5`'s refusal
  path never fired.

### Fixed

- **Three real plumbing failures, found on the renders already on disk, before any pod was created.**
  Running the scorer against `outputs/final/`'s ten 1024-canvas PNGs cost nothing and paid for itself
  three times. This is what ordering the metered session *last* is for.
  - **StyleID returned a `ModelOutput`, not a tensor.** `get_image_features` gives a bare tensor in
    transformers 4.x and a `BaseModelOutputWithPooling` in 5.x, whose `pooler_output` is the same
    already-projected vector. Both are now accepted, and a shape that is neither refuses loudly —
    because the extra declares `transformers>=4.49` and a silent change here would surface as a cosine
    over the wrong axis rather than as an error.
  - **DWPose is top-down, fixed at batch five, and emits SimCC rather than heatmaps.** It was being
    handed a whole image at batch one, which raises — so the axis correctly reported its own absence,
    for entirely the wrong reason. It now uses the person detector that was already pinned but never
    called, repeats the crop to fill the traced batch of five, and decodes `(5, 133, 576)` x-logits
    against `(5, 133, 768)` y-logits over 133 whole-body keypoints.
  - **`yolox_l.onnx` emits undecoded predictions.** Its `(1, 8400, 85)` output carries per-anchor
    offsets, not coordinates; reading columns 0–3 as pixels produced a confident-looking box in
    entirely the wrong place, and the pose read inside it came back as 133 keypoints every one of which
    fell under confidence. Found by looking at the value ranges rather than the shapes — the columns
    were negative. The standard YOLOX grid/stride decode is now done here, over a letterboxed input
    rather than a stretched one, because the model was trained that way.
  - **After the three: the scorer runs to completion on both directories, all five axes reporting.**
    No claim is made about the numbers — the dials moved six ways per render and these are the wrong
    subjects. What was proven is the plumbing.
- **`ty check` is green whether or not the extra is installed.** `eval_backends.py`'s unresolvable
  imports are scoped with a `[[tool.ty.overrides]]` block rather than per-line `ty: ignore` comments,
  which cannot be right in both environments: absent the extra they are load-bearing, present it they
  are "unused directive" warnings, and ty exits non-zero on warnings. `make gate` must not depend on
  what the operator happens to have synced. Every other check still applies to that file, which is how
  a genuine `invalid-return-type` on `OnnxSession.run` was caught and fixed — `onnxruntime` returns a
  `Sequence`, not a `list` — rather than suppressed.

### Added

- **`evaluate.py`, a second entry point beside `convert.py` and never on its import graph.** Four axes
  over a canvas the photograph and the render provably share: face (StyleID, plus ArcFace tagged
  falsify-only), pose (PCK), hair colour (CIEDE2000), and a face-location guard. It is deliberately not
  a subcommand — a subcommand would put the `[eval]` extra one misplaced import away from breaking
  `convert.py`'s `dependencies = []`.
- **Every rule the scorer applies is stdlib-only and therefore tested in CI with the stack absent.**
  `isekai/evaluate.py` holds the canvas, the guard, the refusals and the report and imports nothing
  third-party; the models arrive through Protocols that `isekai/eval_backends.py` implements. That is
  the same seam `ComfyTransport` is under, for the same reason — 47 tests over the scorer's behaviour
  run offline against fakes.
- **The canvas comes from the injector, and a mismatched render is refused naming both sizes.**
  `canvas_for` calls `working_resolution` and `image_dimensions` rather than restating the rule, and
  the photograph's pixels are transposed for a rotating EXIF tag **before any region is parsed** — the
  header parser returns dimensions, and `LoadImage` transposes both codecs, so a photograph parsed
  upright against transposed pixels would place every region wrong with all four numbers still looking
  plausible. The canvas is settled before any model is asked anything, which a test asserts.
- **Regions come from the photograph only.** The render is sampled inside the photograph's own mask and
  never handed to a parser — a human parser is trained on photographs and its behaviour on a drawing is
  unknown. A region under a **measured area floor** refuses naming itself and its area, rather than
  reporting a number derived from too few pixels; the per-class accuracy filter is not here, because it
  would have discarded classes on someone else's test-set numbers.
- **The guard computes both methods on every run** — box IoU and face-box centroid offset — and
  names which one was authoritative. Which one ships is decided by measurement in phase 8, not by
  argument. A failed guard refuses every region axis naming the guard as the cause, while the pose axis,
  which needs no region, still reports: a guard failure does not deprive the operator of the
  measurements it does not invalidate.
- **Absence is its own field and never a low score.** `face_detected` and `render_face_detected` are
  separate from every value, a pose reader that read nothing reports its own absence rather than a
  zero, and low-confidence keypoints are dropped and counted rather than scored at a guessed
  coordinate.
- **A cross-base comparison refuses per axis, not globally.** The embedding axes refuse with the reason
  in the record while colour, area and keypoints still report. **A run recording no base is treated as
  unknown rather than as matching** — the case this exists for is an old manifest that predates the
  provenance keys, where assuming a match would compare across bases silently.
- **The report emits no combined score, no verdict and no percentage.** One JSON record per render and
  one table per run; every column states its direction and whether it is absolute or relative; the run,
  the base and the image are named so a table read months later can be attributed. Every claim the
  numbers do **not** support is printed beside them, including that no axis isolates one dial.
- **CIEDE2000 is implemented in-tree and checked against Sharma, Wu & Dalal (2005)'s own 34-pair
  reference table**, to four decimals, plus symmetry and the neutral-chroma cases. That table was
  constructed to catch exactly the discontinuities an implementation gets wrong, which makes it a
  stronger check than trusting a transitive dependency — and it keeps scipy, networkx and imageio out
  of the lock for one closed-form function of six numbers.
- **The `[eval]` extra is five packages and CI never installs it.** `torch` and `transformers` are
  unavoidable rather than convenient: StyleID publishes only a `CLIPModel` safetensors and the DWPose
  artifact `models.json` pins is a TorchScript `.pt`. `onnxruntime` (MIT) carries the region parser and
  the anime-face detector. The gate array stays five commands and `convert.py` keeps
  `dependencies = []`.
- **`ultralytics` is absent from `pyproject.toml`, from `uv.lock` and from the scorer's import graph**,
  asserted by three tests rather than left to a licence review nobody runs. Verified with the whole
  extra installed: it is not importable.
- **The stdlib guard uses `-S`, and the AST fallback was not needed.** `design.md` D12 left the
  mechanism open because `-S` inside a uv venv was unverified. It was verified here, both ways: `-S`
  leaves no site-packages on `sys.path`, `import convert` succeeds under it, and `import pytest` fails
  under it — so the guard is falsifiable rather than passing for the wrong reason.
- **`run.json` becomes a provenance record, not only a reproduction one.** It recorded `seed`,
  `variations`, `seeds` and `overrides`, and so could not name the photograph, the graph, the base or
  the resolution — the two batches in `outputs/final/` are identifiable only from this file's prose,
  and a baseline nothing can identify is not a baseline. It now also records the input photograph's
  SHA-256, the base checkpoint the graph loads, the resolved working resolution, and a `renders` list
  carrying, per variation, the image it was written to, its sampler seed, a digest of **the graph as
  submitted**, and the dial values that graph actually carried.
- **The dials are recorded per variation, not once**, because under jitter every variation carries its
  own and a single record would be a lie about all but one of them. They are read off the submitted
  graph rather than reconstructed from the seed and the overrides — reconstructing them would mean
  re-deriving the mutator in order to read it. The three ControlNet strengths are keyed by node id,
  since they are tuned differently and "tile, pose, lineart" is an ordering nothing in the graph
  states.
- **The photograph is recorded as a digest and never as pixels.** A digest of a face is not a face, so
  the rule that derived faces are not committed is untouched — and the digest is exactly what makes an
  uncommitted input checkable rather than merely trusted, as `probe/README.md` already does.
- **Keys are added and none removed**, so a manifest written by an earlier version stays readable and
  a reader written against the old shape keeps working; a test holds that. The digest helper is
  spelled in `pipeline.py` rather than imported from `isekai.provision`, which has one: that module is
  deliberately off `convert.py`'s import graph, and importing it for four lines would put it on.
- **A render with the graph's own dials is possible for the first time.** `pipeline.run` called
  `mutate` unconditionally on every variation, and `mutate` moves six dials at once — `denoise`,
  `cfg`, `ip_weight` and all three ControlNet strengths — so **nothing this repository has ever
  rendered differs from its neighbour in one thing**, and "same subject, one thing moved" was not a
  claim it could make. `run` gains `fixed_dials` and the CLI gains `--fixed-dials`, **off by default**,
  so every existing invocation behaves exactly as it did.
- **A held run still draws its own sampler seed per variation**, because otherwise it would be one
  render billed N times. The seed draw is split out of `mutate` as `draw_seed` and stays the *first*
  draw `mutate` makes, so a held run and a jittered run from the same run seed carry the **same**
  sampler seeds and differ in the jitter alone — which makes the two directly comparable rather than
  merely both reproducible. An override still applies under `--fixed-dials`: holding the dials means
  not jittering *around* the base, never ignoring the base the user set.
- **`cn_strength` becomes settable.** The identity node's second dial — the keypoint route, beside
  `ip_weight`'s embedding route — sat at 0.5 in the graph and was referenced nowhere else in the tree:
  not in `apply_overrides`, not in `mutate`, not in any test. It joins `apply_overrides` and the CLI as
  `--cn-strength`, range-checked at parse time in zero-to-one like its neighbours. It is set on
  `ApplyInstantIDAdvanced` and **never** on a `ControlNetApplyAdvanced`, which is a different dial that
  happens to share a word — setting it there would move pose and structure while claiming to move
  identity, and a test asserts every ControlNet strength is untouched.
- **`cn_strength` is pinned** beside `PROBE_DENOISE` and `PROBE_IP_WEIGHT`, so a silent re-tune becomes
  a deliberate test edit. Unlike those two it was never *chosen* by anybody — it is the value the graph
  arrived with — so the pin records where the baseline was rendered rather than a preference. **0.5 is
  unsearched: this version makes it searchable and deliberately does not search it**, because searching
  a dial with the same renders that validate the instrument would leave neither result clean.
- **Every model the evaluator will load is pinned, before a line of scorer code exists.**
  `scripts/eval_models.json` — twelve entries, each with an immutable-revision URL, a SHA-256 and a
  byte count — is a **sibling** of `scripts/models.json` and never a section of it: that file is what
  the pod provisions **the graph** from, and these run locally on the operator's machine. It is
  *derived*, not transcribed, by `scripts/derive_eval_manifest.py`, under the same rule its sibling is
  under: re-running it must leave the file byte-identical.
- **Three destinations are copied out of the graph's manifest byte for byte** —
  `insightface/models/antelopev2/glintr100.onnx` and the two DWPose artifacts. For `glintr100` that is
  load-bearing rather than tidy: the scorer's ArcFace has to be the artifact the generator injects
  identity *with*, or the whole claim about self-grading would be a claim about two different models.
  `shared_entries_that_differ` compares whole entries, not just digests, so the two files cannot drift
  apart unnoticed — a matching digest beside diverged sources would mean the same bytes arriving from
  different places, which is exactly the drift the copy exists to prevent.
- **`isekai/eval_models.py`**, the gate every scorer axis will reach its weights through. It refuses
  three ways: an artifact the manifest does not declare, an entry whose sources are not pinned
  revisions, and bytes on disk that do not hash to the pin — the last naming the file, the expected
  digest and the computed one, because a human reading a mismatch is deciding whether a pin is stale
  or a file has been swapped, and two of the three do not answer that. The pin check runs even though
  nothing is fetched: an entry pointing at `resolve/main/` says nothing about which bytes those were.
  Nothing here knows about an axis, and it stays off `convert.py`'s import graph.

### Notes

- **Every licence was read on 2026-09-06 and recorded in `scripts/eval_licences.md`**, each with the
  URL it was read at and quoted verbatim from the source. **None forbids this use.**
- **DWPose was the one entry left open, and it closes clean: Apache-2.0.** So the pose axis is
  unthreatened on licence grounds, and the contingency where it would have reported its own absence
  rather than a zero is not needed.
- **The conflict this version was cut believing in does not exist.** StyleID's CC BY-SA 4.0 is on
  **the website** — footer boilerplate from the academic project-page template it is built on. The
  repository and the model card agree with each other: *"StyleID is released for non-commercial
  research use."* The adjacent clause, *"Do not use FFHQ-derived data for biometric human
  recognition"*, governs the **dataset** and not the encoder; it is recorded because it is adjacent,
  not because it binds.
- **Four artifacts are non-commercial research and are carried as recorded deviations** — StyleID,
  `segformer_b2_clothes` (NVIDIA Source Code License, inherited from SegFormer), and `glintr100`, whose
  restriction this project has been shipping since v0.9 because InsightFace's library is MIT and its
  weights are not. **Stated rather than discovered later: if this project ever became commercial, all
  four would bite at once, and retroactively against a baseline already in git.** There is no
  mitigation beyond knowing it. The rule that survives is the load-bearing half — **a model whose
  licence is restrictive may not be the sole carrier of an axis**; StyleID ships beside ArcFace or not
  at all.
- **The AGPL detector was replaced, because the artifact the design named does not exist.** The plan
  was to load `Fuyucchi/yolov8_animeface` (AGPL-3.0) through `onnxruntime` and never import
  `ultralytics`, so that no AGPL *code* is combined with this Apache-2.0 public repository. Checked on
  2026-09-06: that repository publishes **no ONNX at all** — its Hugging Face tree and its sole GitHub
  release both carry only `yolov8x6_animeface.pt` — so the mechanism had nothing to point at.
  Exporting the `.pt` ourselves was rejected: it needs `ultralytics` installed and yields an artifact
  with no upstream revision to pin. Pinned instead: **`deepghs/anime_face_detection`,
  `face_detect_v1.4_s`, MIT** — a published ONNX, which **dissolves** the copyleft problem instead of
  routing around it, and which keeps the guard measurable both ways rather than collapsing it to one
  method. Recorded residual, not relied on silently: deepghs's MIT tag is their own declaration over
  weights trained with `ultralytics` tooling, and Ultralytics asserts AGPL over such weights — an
  assertion about *weights*, which this repository distributes none of and links no code from.
- **A pre-v0.12 `run.json` is refused by name, not guessed at.** Both directories in `outputs/final/`
  were rendered before the provenance record existed, and the scorer says exactly what it lacks — no
  `photo_sha256`, so the photograph supplied cannot be confirmed; no `base`; no `renders` — and exits
  1. Guessing would be worse than refusing: a comparison against the wrong photograph produces four
  plausible numbers and no way to notice one of them is about somebody else.
- **All twelve pinned eval artifacts were fetched and verified against `scripts/eval_models.json`**
  before anything was scored. Every digest matched.
- **No scorer code, no axis and no render change.** This phase pins artifacts and records licences;
  `workflows/pipeline.json`, `scripts/models.json` and the `Dockerfile` are untouched, no image is
  rebuilt and no volume is re-provisioned.

## [0.11.0] - 2026-09-06

### Fixed

- **The capacity floor is raised clear of the container disk as well as the volume disk.** Moving the
  floor from free space to capacity widened the passing set, and one wrong disk entered it: the case
  the pod-side guard exists for at all is the one `up.sh` cannot see — the volume id is set and the
  mount silently failed — where `/runpod-volume` falls through to the container overlay, whose backing
  disk is `containerDiskInGb: 30` (`infra/up.sh`). `avail` on that overlay, already carrying the
  image, was far under the old 20 GiB floor and refused; `size` reports ~27.9 GiB regardless of what
  the image occupies, and passed. The floor is now **40 GiB**, derived against both wrong disks —
  20 GB volume disk ≈ 18.6 GiB, 30 GB container overlay ≈ 27.9 GiB — and against the right one, the
  80 GB network volume ≈ 74.5 GiB. It is one measurement still, not two: the rejected alternative was
  a second free-space check beside it. The error text now names what it measured and which two
  ephemeral disks a reading that small means. `design.md` D5 and D5a and `tasks.md` are reworded off
  the free-space mechanism they still described.
- **A manifest destination is held to the same whitespace rule as a source, and one that resolves to
  the models root itself is refused rather than crashed on.** `resolve_dest` is the single site the
  containment rule is enforced at, and it had two holes: a `dest` containing `\n` or `\t` survived
  `normpath` into the tab-delimited plan line, where an embedded newline starts a fresh record whose
  target is absolute and whose URL never meets `PINNED_SOURCE` — that check lives in `decide`, which
  an injected record bypasses; and a `dest` normalising to `"."` (`"."`, `"./"`, `"a/.."`) raised
  `IndexError` off `PurePosixPath(".").parts` being empty, instead of returning `None` as the
  function's own contract says. `plan` additionally refuses to emit any target carrying `\n` or `\t`,
  which covers the half of the target that comes from `MODELS_DIR` rather than from the manifest.
- **The header-walk refusal names the codec that gave up.** `_HeaderTooDeep`'s message was
  JPEG-worded — "no frame header" — but the PNG chunk walk raises it too, from two places, so an
  operator handed a corrupt PNG was told the file lacks a structure PNG does not have. The exception
  now carries its codec and the message renders it, still naming the file and the byte budget.
- **`civitai_file` returns the digest alone.** Its size was read with a subscript where every sibling
  read uses `.get` with a `SystemExit`, so a record omitting `sizeKB` aborted derivation with a raw
  `KeyError` — for a number the one call site discarded and the manifest never used, its `bytes`
  coming from Hugging Face. Dropped rather than defended.
- **The probe's JPEG segment walk no longer indexes past the end of the file.** `segments()` read the
  marker's code byte having tested only that the marker byte itself was in range, so a JPEG ending on
  a lone `0xFF` raised `IndexError`. A file that ends there has no segment left to report.
- **The pod-side volume guard measures capacity, which is what it is trying to prove, rather than
  free space.** The 20 GiB floor was read off `df -k --output=avail` while its error text claimed to
  have proved *identity* — "this is not network volume ${RUNPOD_VOLUME_ID}". Free space on a
  correctly-attached volume is whatever this project's 16.5 GiB of models plus the second project
  sharing that volume have left of it, so the guard was coupled to fill level and degraded
  monotonically as the volume filled. A warm boot on which every manifest entry would `SKIP` — a pod
  that needed to download nothing — would have been refused, written the failure marker and billed
  the whole 900 s hold. The floor is now on `--output=size`: total capacity discriminates the pod's
  own 20 GB ephemeral disk from the network volume whatever either currently holds, and the message
  says what is measured. Free space is not checked at all; if it ever should be, it is a second check
  with its own message, which is why it is not smuggled into this one.
- **A PNG declaring an `eXIf` chunk longer than the header budget is refused by name.** The chunk
  walk seeks over every payload but one: the `eXIf` branch called `read(length)` on the raw uint32 out
  of the chunk header, bounded by nothing. `MAX_HEADER_BYTES` is tested at the top of the loop and
  that branch returns before the next iteration, so a chunk declaring 0xFFFFFFFF asked for a 4 GiB
  read whose `MemoryError` neither `except` clause catches — a traceback instead of the refusal that
  names the file and the budget. It was the fourth ceiling in a phase whose subject was stating the
  three the header parse left open. The length is now checked against the budget before the read, and
  a chunk that overruns it raises the same `_HeaderTooDeep` the other ceilings do rather than
  truncating to a silently wrong orientation.

- **A rotated PNG is measured as it will be loaded, in the codec every input this project has ever
  used.** v0.10 closed this for JPEG and left PNG open, because `_png_dimensions` read IHDR and
  stopped. PNG can carry an `eXIf` chunk holding the same TIFF stream JPEG's APP1 does, and the
  phase-6 loader probe measured the pinned build rather than reasoning about it: a portrait PNG
  tagged Orientation 6 came back from `LoadImage` as **1216×832**, transposed, against an untagged
  control that did not move. Injection was therefore measuring such a file as its header states while
  the loader handed the graph the transposed pixels — and `ImageScale` runs with `crop: "disabled"`,
  so the photo would be squashed non-uniformly into the wrong frame and the distorted face fed to
  InstantID, the VAE encoder and all three preprocessors at once. Exactly the defect v0.10 called
  blocking, in the branch that was not fixed. The parser now walks the PNG's chunks to the pixel data
  looking for `eXIf`, and both codecs share one TIFF orientation reader rather than each having its
  own. The scenario the fix is bound to now names both codecs, because the mismatch is a property of
  the loader and not of the container.

### Added

- **The base checkpoint's digest is derived from its publisher's own record, not transcribed.**
  `derive_manifest.py`'s docstring claimed the manifest is "derived, never transcribed" while the one
  digest that matters most was a constant a human typed — and it is the entry where the digest is not
  merely a check on the transfer but the **whole trust root**, because WAI has no first-party host
  and every source is a mirror. It existed in three places that compared against each other, which
  cross-checks the copying and not the value. The deriver now fetches it from Civitai's public
  model-version record (`https://civitai.com/api/v1/model-versions/2883731`, read 2026-09-06), like
  every other digest, and holds the mirrors against that. The parse is a pure function so the suite
  checks it offline; only the fetch touches the network.

  The residual is unchanged and stated: **Civitai is still the trust root**, it publishes no
  signature, and the digest is computed by the platform after upload — an independent cross-check of
  the mirrors, not an attestation by the author. **BLAKE3 is deliberately not recorded** although the
  same API publishes it: verifying it would need a wheel the stdlib-only runtime rule forbids, and a
  field nothing reads is the same smell as a one-entry registry. The hand-written copy in the suite
  stays, on purpose — it is the *offline* anchor the gate holds, and an anchor that fetches is not
  one.
- **CI enforces the `latest` protection its own header comment claims.** `build-image.yml` asserted
  that a manual run "can never clobber the image a rollback would reach for" while interpolating an
  unvalidated `workflow_dispatch` string straight into `tags` — so a dispatch naming `latest` did
  exactly that, and a newline in the input would have been honoured as a second tag by
  `docker/build-push-action`'s newline-separated `tags` field, which a `gh workflow run` or a REST
  dispatch can supply. A first step now fails unless the input matches `^[A-Za-z0-9._-]+$` and is not
  `latest`, and assigns the validated value to a step output the build step reads, so the raw input
  is never interpolated into `tags` at all. The dispatch default, still `v0.9-rc` two versions on,
  now names `v0.11-rc`.
- **Three stated ceilings on measuring a photo, each a refusal rather than a clamp.** The short-side
  rule bounds one axis and says nothing about the other, and a header field was an unverified number
  until something bounded it. The computed target's **long side** is capped at 4096 — 4:1 at a 1024
  short side, past any real photo, and 1024×4096 is already a heavy SDXL allocation. A
  **header-declared dimension** is capped at 65535, which JPEG's own two-byte frame field already
  enforces, so both codecs now refuse the same input. The **marker walk** stops after 4 MiB, so a
  file whose frame header sits arbitrarily deep is refused rather than read to its end. Each names
  the file and the limit. None clamps: a clamped target no longer preserves the aspect ratio, and
  would squash the photo the way the orientation rule exists to prevent.
- **A pod is refused before it is created if it was not told which network volume to use.**
  `infra/up.sh` now checks `RUNPOD_VOLUME_ID` before the create call and passes it into the
  container, so the entrypoint is told which volume to expect rather than inferring it. The failure
  this prevents — the full 16.5 GiB model stack downloaded onto storage that dies at teardown —
  renders correctly, bills fully, and is discovered only on the next metered session. The suggested
  pod-side fix, `mountpoint -q`, does **not** work: RunPod defaults `volumeInGb` to 20 and mounts the
  pod's own volume disk at `volumeMountPath` when no network volume is attached, so the path exists
  and *is* a mountpoint — the wrong one. The entrypoint therefore keeps a second check as defence in
  depth, with a free-space floor above what that 20 GB disk could ever report as the discriminator.
- **The provisioning guards moved from the suite into the module, where they can bite on a pod.**
  Four manifest checks had no caller outside `tests/test_manifest.py`: they constrain the manifest
  this repository tracks, and constrain nothing about a manifest the module is handed on the pod —
  which is what joins a destination onto the filesystem and hands a URL to a transfer. `decide` now
  refuses, before any byte moves and naming the entry, a destination that is absolute or resolves
  outside the models root, a source that is not a pinned URL free of whitespace, and an entry that
  declares no sources at all. The last is refused **by name** rather than reported as "every source
  was rejected" with an empty reason list: an entry that offered nothing and an entry whose every
  offer was refused are different failures with different fixes.
- **The plan line carries the already-resolved destination.** `provision.py` resolves it once and
  `scripts/download_models.sh` no longer assembles `"${MODELS_DIR}/${dest}"`, so a manifest-controlled
  field can no longer reach a path join and the containment rule has exactly one site. The resolution
  is lexical, because the models root on the pod *is* a symlink onto the namespace.
- **The driver reads its sources as an array rather than word-splitting a string.** `IFS=$'\t' read
  -r -a` makes the sources a list from the moment the line is read, so a source's own shape cannot
  change how many arguments `wget` is given. The `# shellcheck disable=SC2086` that made the split
  legal is gone with it — the suppression was the marker, and the split was contained only by an
  argument-parsing accident.
- **The graph↔manifest binding keys on an explicit set of class names, not a `*Preprocessor`
  suffix.** A suffix rule binds the nodes spelled that way and silently passes the ones that are not:
  `InstantIDFaceAnalysis` fetches the whole antelopev2 pack and matches no pattern at all. The
  mapping is now a census of every class the shipped graph uses, so a node added to the graph fails
  the check until someone answers whether it fetches for itself, and the five antelopev2 destinations
  are bound to the node that fetches them.
- **The provisioning hold is bounded and leaves a marker.** A provisioning abort used to hold the pod
  open with `tail -f /dev/null` — reachable, but reporting as running and healthy while it billed
  indefinitely. It now holds for 900 s (~$0.19 at the rate this project runs on, inside the ~$0.30
  per-session ceiling) and writes a failure marker to **container disk**, never into the models
  namespace: the namespace is exactly the thing that may have failed, and a marker a broken volume
  prevents you from writing does not make the failure legible.

### Changed

- **ComfyUI's core is pinned to a commit — the last unpinned link in the change whose thesis was
  pinning.** `Dockerfile` cloned the default branch head while both custom-node packs beside it were
  already pinned, so an image rebuilt a month later ran a different inference engine with no record
  that it had. The pin is `250b2e9551a7bc7a8ebb5beb07e0fecd2983e04a`, **recovered from
  `ghcr.io/alxb1t/isekai:v0.10-rc` itself** rather than taken from upstream today: it is a record of
  what already ran, so the core is not a new variable. Bumping it forward is a separate, deliberate
  act that must carry a render comparison at a fixed seed.
- **The reachability hold covers preparing the namespace, not only fetching into it.** Creating the
  namespace and relinking the models root now sit inside the same guarded step as the download, so a
  failure there reports and holds instead of terminating the entrypoint — which under `set -e` took
  the SSH daemon with it and left no way in. Preparing the volume is provisioning by any reading a
  human would give the word; the guarantee is about provisioning and not about one of its steps.
- **The `rm -rf` of the models root is guarded on its premise rather than on its proxy.** What made
  the delete safe was that the tree is the image's own, on container disk; the check was that the
  path is not yet a symlink. A non-empty tree someone has mounted there is a real models tree, and
  the entrypoint now refuses rather than deleting it. Deleting one is an explicit operator act.

- **A metered pod session exercised four input shapes v0.10 named as untested, and a loader probe
  settled a question exit codes cannot.** `probe/README.md` is the record. One session on
  `:v0.11-rc`, 9 min 33 s and ~$0.11 against a 45-minute, ~$0.30 ceiling; teardown confirmed through
  the RunPod MCP with its response recorded. All four renders exited 0, and each render's dimensions
  equal the target `working_resolution` computes from that file's own header — including 1536×1024,
  the first target produced by rounding on the **height** axis, and 1024×1152, an aspect no prior run
  produced. The pinned ComfyUI core was confirmed on the pod itself.

  **What the session did not establish is stated in the same breath**, in `probe/README.md` and here:
  nothing about identity, fidelity or quality, because no evaluator exists and none was run; **not**
  that renders are unchanged from v0.10, because the dependency closure was re-resolved at build and
  no v0.10 PNG baseline was kept, so there is nothing to diff against; **not** the volume guard and
  **not** the bounded hold, both of which ship suite-bound and were never reached on a healthy pod;
  and nothing about mutation, since each photo ran at one variation.

### Notes

- **The unreconciled 1152, recorded and left unverified.** v0.10's proposal says the working scale
  targets a short side of **1152**, on the reading that MistoLine's card requires *above* 1024;
  `WORKING_SCALE = 1024` shipped, under a comment calling 1024 "the floor MistoLine's card names".
  Two readings of one sentence, and one of them is wrong. The reading this repository runs on is
  1024, and every render it has ever shipped was made at it. **Which reading is right is a rendering
  question, so it waits for the evaluator and was not re-tested here** — nothing in this version
  should be read as saying the 1024 was validated. What changed is that the disagreement is written
  down where a reader following the version chain will hit it, rather than sitting unremarked between
  an archived proposal and a code comment. v0.10's own documents are not edited: an archived change
  records what was decided then.
- **The pose-grid sentence is corrected in both places it was written.** `workflow-injection`'s
  `scale-precedes-every-consumer` claimed "no control hint is registered against a different one",
  and `README.md` repeated it. It is false: `DWPreprocessor` derives its hint at `resolution: 512`
  where tile and lineart carry 1024, and the test bound to the scenario checks image links only — so
  the false clause was unenforced. The scenario is narrowed to what the suite proves, that every
  consumer is handed the same scaled image, with a preprocessor's own working resolution named as the
  separate dial it is. **The graph is unchanged**: moving that dial measurably changes the render, and
  rendering questions wait for the evaluator.
- **A `spec_exempt` label now says what it is.** `"structural: pins the dials the phase-5 probe
  chose"` described a by-eye value pin as structural, which is the opposite of what it is. It reads
  `"preference, not a scenario: holds the dials design.md D9 records as by-eye"`. No behaviour
  changes; the point is that a reader auditing the exemptions is told the truth about which ones are
  load-bearing.
- **Pinning the core moves the floating link rather than removing it, and this change does not claim
  otherwise.** `Dockerfile` still runs `uv pip install -r requirements.txt` against ComfyUI's own
  requirement file and against the preprocessor pack's, and neither is version-locked: both resolve
  at build time, so after this pin the core is fixed and its dependency closure is not, and two
  builds of an identical tracked `Dockerfile` still differ. **The image is not reproducible.** Locking
  both closures needs a new tracked artifact, a derive-and-verify step and a full rebuild to
  validate — its own change, and named here as the next pinning target.
- The comment above the models namespace no longer calls the tree it replaces empty. The ComfyUI
  clone tracks `models/configs/*.yaml`, so it is not; the delete drops them **knowingly**, because
  the graph uses `CheckpointLoaderSimple`, which takes no config. Copying them in would add a write
  at boot to be ordered against the new volume guard, and would restore a config dropdown only for
  loader classes this repository's one-path rule forbids ever using. The defect was a false comment,
  and the comment is what is fixed.
- **Both new guards ship suite-bound and unexercised on a pod.** Exercising the pod-side volume check
  would mean deliberately defeating the client check added beside it, in order to test a
  configuration this repository no longer produces; exercising the bounded hold would mean breaking
  provisioning on metered time. This is a real residual, and it is written down rather than smoothed
  over.

## [0.10.0] - 2026-09-05

### Fixed

- **A rotated phone photo is measured as it will be loaded, not as its header states.** ComfyUI's
  `LoadImage` applies the EXIF `Orientation` tag before any node sees the pixels, so for the ordinary
  case of a phone held upright the frame header's 4032x3024 is transposed to 3024x4032 by the time
  the graph has it. Injection computed its target from the untransposed pair and `ImageScale` runs
  with `crop: "disabled"`, which scales to the exact target rather than fitting to it — so the photo
  was squashed non-uniformly into a landscape frame, silently, and the distorted face was fed to
  InstantID, the VAE encoder and all three preprocessors at once. The header parser now reads the tag
  and swaps the pair on the four values that transpose.
- **A camera JPEG whose frame header sits past 64 KiB is read rather than refused.** The parser read
  a fixed 64 KiB prefix on the premise that the frame header is near the front; an EXIF segment
  carrying an embedded thumbnail may alone be 65 533 bytes, and cameras write ICC and XMP segments
  besides. Such a file walked off the end of the prefix and hard-exited with "cannot read the image
  dimensions from its header" — a well-formed photo reported as a defective one. The marker walk now
  runs against the open file, reading each segment's header and seeking over its payload, so it is
  bounded by the file rather than by a guess. Standalone markers and a segment length below 2 are
  now rejected in the same pass, both of which previously stepped the walk into a payload where
  arbitrary bytes could be read back as a frame header.

### Added

- **The publisher-stated digest of a mirror-only artifact is a spec'd requirement.** The base
  checkpoint's tie to the SHA-256 Civitai publishes was checked by the gate but bound to a scenario
  about digests being present, which it does not prove. `model-provisioning`'s immutable-pins
  requirement gains the case the base actually depends on — an artifact its publisher does not host
  is pinned to the digest the publisher states — and the one-checkpoint assertion is split into its
  own test against the one-path rule.

### Removed

- **Animagine XL 4.0 leaves the manifest.** It had been the rollback and the probe's comparison
  base since the WAI entry landed; with the swap proven, a declared checkpoint nothing renders with
  is a second path in everything but name, which this repository's one-path rule forbids
  (`design.md` D3). `cagliostrolab` leaves the `publishers` list with it. The manifest is now 15
  entries and 16.5 GiB, down from 16 and 23.0 GiB. **A re-provision after this point removes
  Animagine from the volume**, so rolling back to it means reverting the manifest, not just
  `ckpt_name`.

### Changed

- **`README.md` and `CLAUDE.md` describe an Illustrious base.** The path table and the "How it
  works" line name WAI-illustrious-SDXL v17.0, the working-resolution rule and the committed CLIP
  layer are written down, and the ControlNet stack is described as the strength-to-zero comparison
  left it — including that "changes the render" is not "improves the render", and that tile carries
  its publisher's animation disclaimer as a known deviation. `1girl`'s defect is recorded as
  **closed**, with the mechanism that closed it named: the identity node's face embedding, not a
  tagger. **Neither document makes any claim about identity or quality.**

### Notes

- **The path runs on WAI-illustrious-SDXL v17.0, at stated input resolutions.** Two photos of
  different aspect ratios through the unmodified `convert.py`, both exiting 0 and writing
  `0.png`–`4.png` plus `run.json`: 982×1559 rendered at **1024×1600** and 832×1216 at
  **1024×1472**, every variation. Each rendered dimension equals the target the injector computes
  from the photo's own header — the first live confirmation of the scale node on real files.
  Session 8 min 23 s at $0.72/hr = **$0.10**; teardown confirmed through the RunPod MCP (`get-pod`
  → 404 "pod not found", `list-pods` → 0 items). `RUNPOD_IMAGE` was cleared from `.env` afterwards.
- **What this version does not establish**, stated plainly because v0.8's Verified block implied a
  generality it never tested: **nothing** about identity, fidelity or quality — no evaluator exists
  and none was run; **not** that the chosen dials are good, let alone optimal; **not** that any
  ControlNet improves output, only that each retained one measurably changes it; **not** that the
  register improves anything. It also does not establish that the path runs at *any* resolution —
  both photos were portrait and both below the working scale, so a landscape input and a photo
  above 1024 on its short side remain untested on a GPU.
  What it establishes is that the path runs on WAI at the two stated input resolutions, and that a
  male photo yields a male-presenting output.

### Changed

- **The probe's verdicts are applied, and both are "no change to the graph".** The chosen
  `denoise` 0.65 and `ip_weight` 0.9 are the values already committed, and the tile ControlNet is
  kept because the strength-to-zero comparison found it strongly distinguishable from absent. They
  are now **pinned by the suite** rather than merely present, so the evaluator version inherits a
  baseline it can measure against and a silent re-tune becomes a deliberate test edit.
- **The stack walk is under test.** `KSampler.positive` may point at `ApplyInstantIDAdvanced`
  directly *or* through a stack of `ControlNetApplyAdvanced` nodes, so the encoder must be found by
  following the link and never by class lookup. The probe could have shortened that stack, which is
  exactly when the property would have broken unnoticed; a test now walks it end to end and asserts
  the hop count matches the number of ControlNets in the graph.
- **`scripts/models.json` is unchanged, so the image is not republished.** Nothing dropped out of
  the graph, so the manifest the pod provisions from still matches it and `:v0.10-rc` stays the
  image the final renders boot.

### Notes

- **The v0.10 probe ran on a pod and its results are recorded** in
  `openspec/changes/0010-illustrious-base/probe/`. WAI provisioned alongside Animagine at boot from
  the manifest, verified: 6,938,040,682 bytes, exactly the count the manifest declares. Session
  18 min 27 s at $0.72/hr = **$0.22**, inside the 45-minute / ~$0.30 ceiling; teardown confirmed
  through the RunPod MCP (`get-pod` → 404 "pod not found", `list-pods` → 0 items).
- **Every ControlNet is kept.** A strength-to-zero comparison at a fixed seed, with no mutation and
  every other dial held, asked one falsifiable question per ControlNet: does the conditioning reach
  the sampler at all? Tile is **strongly** distinguishable from absent — hair length, garment and
  framing all change — and OpenPose and MistoLine are distinguishable subtly. None is
  indistinguishable, so none is deleted, **including tile**, which `design.md` D7 named as the
  likely deletion and left to the comparison to decide. TTPlanet's own card disclaimer — "no comic,
  animation application are promised", recommended strength 0.9 against the 0.2 this graph runs —
  is therefore recorded against it as a **known deviation**, not resolved. This establishes only
  that each retained ControlNet measurably *changes* the render, never that it improves it.
- **`denoise` 0.65 and `ip_weight` 0.9 are chosen — a preference, not a measurement.** Found by eye
  against one photo at a fixed seed, over three denoise points and one ip_weight point. They are
  the values already in the graph: they were tuned on Animagine with no reason to expect they would
  transfer, so this is a real search with a null result. **Chosen is not best**, and the search was
  coarse — four renders inside a 25-minute budget.
- **The gender check passes.** A male-presenting input photo, at the new register with `1girl`
  removed and a fixed seed, produced an unambiguously male-presenting output. This is the one
  falsifiable acceptance criterion the register change gets and it could have failed. One photo is
  an existence proof that the identity embedding supplies the axis, not a rate.
- **The first thing to check next version.** As `design.md` D4 predicted, dropping `realistic,
  photorealistic` from the negative removed a push away from the photograph, and these outputs read
  as semi-realistic digital painting rather than flat anime screencap. Recorded as a finding for
  the evaluator version, not as a reason to reinstate a gender tag.

### Added

- **`ghcr.io/alxb1t/isekai:v0.10-rc` is published**, and it is the image both metered phases boot.
  The pod provisions from the manifest baked into whatever image it runs, and `:latest` is v0.9's
  — so a pod on `:latest` would provision v0.9's manifest and never fetch the checkpoint the graph
  now names. No `Dockerfile` change was needed: `ImageScale` and `CLIPSetLastLayer` are core
  ComfyUI, so this is a rebuild rather than a change. `:latest` is deliberately **not** touched;
  CI publishes it from a push to `main` and nowhere else, and the manual dispatch requires a tag
  and names it "never `latest`", precisely so a pre-release build cannot clobber the image a
  rollback reaches for. The tag becomes v0.10's on merge, by the mechanism that already exists
  (`design.md` D8). `RUNPOD_IMAGE` is set in the untracked `.env` and is cleared after the last
  metered phase, since a stale value would silently pin every later pod to an unreleased image.

### Changed

- **BREAKING — the base is WAI-illustrious-SDXL v17.0, and the register is its publisher's.** The
  positive is the content tags with WAI's own ladder appended last, where every published sample
  puts it; the negative is the publisher's own short form. WAI's page warns that too many quality
  tags and over-long negative prompts *reduce* image quality, so taking its positive while keeping
  v0.8's eighteen-token negative would have taken half the guidance and ignored the half stated as
  a warning (`design.md` D4). One consequence, recorded rather than absorbed: `realistic,
  photorealistic` is gone from the negative, which removes a push *away* from the photograph on a
  product whose whole subject is a photograph — if renders come back more photographic than v0.8's,
  that is the first place to look. Both literals stay pinned by equality, so changing either is a
  deliberate test edit.
- **The graph stops CLIP at the second-to-last layer.** Every one of WAI v17's published sample
  images carries `clipSkip: 2` and none of the publisher's prose mentions it, so a graph without a
  `CLIPSetLastLayer` ships a configuration the publisher never tested while looking identical to
  one that does (`design.md` D6). Both text encoders take their CLIP through it — routing only the
  positive would condition the two halves against different text towers. The value is pinned like
  the prompt: configuration, not a dial.

### Removed

- **`1girl` is out of the committed positive; `solo` stays.** `solo` is what does the Danbooru
  mode-selection work, while `1girl` additionally asserted a gender that the identity node's face
  embedding already carries — so that axis now belongs to a mechanism already in the graph rather
  than to a tagger that does not exist (`design.md` D5). This closes the defect v0.8 recorded and
  named a later version as the owner of. **It is not yet demonstrated**: whether a male photo
  yields a male-presenting output is this version's one falsifiable acceptance criterion for the
  register change, and it is checked on a pod, not here.

### Notes

- The negative carries one tag beyond the publisher's quoted short form: `nsfw`, which the same
  model page instructs users to add to filter its four safety-rating tags. On a product that
  converts photographs of real people, omitting an instruction the publisher gives by name would
  be a defect rather than fidelity to the quote.

### Added

- **The photo is scaled to a working resolution before any node reads it.** An `ImageScale` node
  sits between the image loader and every consumer — the latent encoder, the identity node and all
  three ControlNet preprocessors — so one pixel grid feeds the whole graph and no control hint is
  registered against a different one. Previously the render happened at whatever size the input
  happened to be, so "the path runs" was a claim about the photos that were tried.
- **`isekai.workflow` derives the render target from the photo's own header.** `image_dimensions`
  parses JPEG and PNG headers directly — stdlib only, nothing new enters `convert.py`'s import
  graph — and `working_resolution` preserves aspect, puts the short side at 1024 and rounds both
  dimensions to a multiple of 64, in **both** directions, so a small photo is scaled up as well as
  a large one down. A short side rather than a pixel budget: at a fixed megapixel count the short
  side moves with the aspect ratio, so a wide photo would land below MistoLine's floor while a
  squarer one cleared it, and nothing in the run would say so (`design.md` D2). An unreadable or
  truncated header stops the run naming the file; there is no default size, because a silently
  wrong resolution is a wrong render rather than an error.

### Changed

- **`inject` takes the photo's local path.** No node available to this pipeline can derive a target
  from the image it is given, so the dimensions are computed by injection and written into the
  scale node. The path is passed from the `input_path` `pipeline.run` already holds, so it stays an
  argument rather than becoming state.

### Added

- **WAI-illustrious-SDXL v17.0 is declared in the manifest**, alongside Animagine rather than in
  place of it. The bytes come from pinned Hugging Face mirror revisions — WAI has no first-party
  Hugging Face repo — and the digest verified against them is **the SHA-256 Civitai itself
  publishes** for the model version, checked mechanically by `derive_manifest.py` against the
  digest the primary mirror serves. That is what makes a mirror a CDN rather than a trust root:
  the digest is the acceptance test, so any host serving matching bytes is equally acceptable
  (`design.md` D1). Six byte-identical alternates are declared, so v0.9's fallback walking has
  somewhere to go if the primary disappears mid-version. Two things the record deliberately does
  **not** claim: the byte count discriminates nothing, since every published WAI version reports
  the identical one, and Civitai's digest is computed by the platform after upload — an
  independent cross-check of the mirrors, not a signature by the model's author. Civitai's own
  download is **not** declared as a source: `provision.py` accepts only a Hugging Face
  `resolve/<40-hex>/` URL, and widening that for one entry would weaken the no-mutable-ref check
  to buy availability six mirrors already supply.
- **Animagine's entry stays.** It is the rollback and the probe's comparison base until the swap
  is proven, and the graph↔manifest binding runs one way, so an extra entry is legal. It is
  removed in this change's final phase (`design.md` D3). Nothing is removed here.

## [0.9.0] - 2026-09-05

### Changed

- **The ordered fallback list is now walked at transfer time, not only at pre-flight.** A FETCH
  plan line carries every source that survived the pre-flight, in the manifest's order, and the
  driver walks them: a dead mirror or bytes that fail verification advance to the next source, and
  only exhausting all of them aborts the entry. Previously the plan named a single URL, so the one
  failure the alternates existed for — a mirror that has gone away, which the pre-flight cannot
  distinguish from "publishes no digest" — aborted the pod boot with the alternate untouched
  (`design.md` D16).
- **A provisioning abort now holds the pod open instead of stopping the container.** `start.sh`
  guards the provisioning call; on failure it prints the reason and `exec`s a foreground hold with
  `sshd` still alive, ComfyUI not started and nothing deleted. Under `set -e` the non-zero exit
  previously killed PID 1 and took the SSH daemon with it, so the file the abort policy leaves "on
  disk for a human to inspect" was unreachable and every re-boot died at the same line
  (`design.md` D17).
- **The stack now provisions from the manifest alone, and the unchanged path renders off it.**
  One pod, 23.3 minutes of wall clock, on a volume created empty for this purpose. All 15 entries
  were fetched from their pinned `resolve/<sha>/` URLs and SHA-256 verified before landing; the
  volume ended holding **exactly the manifest and nothing else** — 15 files, 16.51 GiB, every size
  byte-identical to its declared `bytes`, zero `.partial` files, zero unexpected extras. Then
  `convert.py` rendered the untouched Animagine path: exit 0, `0.png`–`4.png` and `run.json`.
  Cost: 23.3 minutes at the pod's quoted $0.72/hr is ~$0.28, and RunPod's billing aggregate had
  not settled at the time of writing — it still reported the pre-session figure. The operator
  raised this session's ceiling to ~$0.48 in advance; the wall-clock figure is inside it.
  **What this establishes is exactly two things**: that the stack is reproducible from a pinned
  manifest, and that the unchanged path renders from a volume whose entire contents were placed
  by the script. It establishes **nothing** about identity, fidelity, quality or the base —
  `ckpt_name` is still Animagine XL 4.0 and the graph, the CLI and the transport are untouched.
- **The skip path was proven on the warm volume, in the same session.** Re-running the driver
  printed `skip (present, verified)` for all 15 — each one re-hashed off the volume and compared,
  not accepted by name. That is the case a pinned manifest exists for and the one a
  download-path-only check would never reach.
- **The annotator redirect was confirmed on the filesystem, and the log did contradict it** —
  exactly as `design.md` D7 warned. `comfyui_controlnet_aux` printed
  `Using ckpts path: /opt/ComfyUI/custom_nodes/comfyui_controlnet_aux/ckpts`, its pre-override
  value, while `/proc/<pid>/environ` on the running ComfyUI showed
  `AUX_ANNOTATOR_CKPTS_PATH=/opt/ComfyUI/models/annotator_ckpts` and all four checkpoints sat on
  the volume under it. Trusting the log would have produced the wrong conclusion. Note also that
  the variable reads **empty in an SSH session**, because a login shell does not inherit Docker
  `ENV`; only the container's main process does, which is why `/proc` is the check and not `echo`.
- **The 80 GB volume was destroyed**, after and only after that render. Confirmed through the
  RunPod MCP: `204` on delete, absent from the volume list, `404 network volume not found` on
  lookup. The replacement is 40 GB, sized from both projects' manifests (~27.3 GiB together).

### Removed

- **`ghcr.io/alxb1t/isekai:latest` was not touched by this phase.** The metered pod ran
  `:v0.9-rc`, published by a manual CI run, and the two tags resolve to different digests — so the
  image a rollback would reach for is still the released v0.8 one.

### Added

- **The 62 GB models volume was inventoried, and nothing on it is unaccounted for.** One pod,
  read-only, 6.6 minutes of wall clock; teardown confirmed through the RunPod MCP, which returned
  an empty pod list and `404 pod not found` for the pod's id. On cost the two available figures
  disagree and both are recorded rather than one being chosen: 6.6 minutes at the pod's quoted
  $0.72/hr is $0.08, while RunPod's daily aggregate reports $0.19 of pod GPU for the day, and the
  per-pod hourly breakdown had not settled at the time of writing. Either figure is inside the
  ceiling. 48 files, 55.85 GiB, classified
  exhaustively:

  | class | files | size | |
  |---|---|---|---|
  | placed by this project's script | 11 | 16.15 GiB | every non-annotator entry of the v0.9 manifest |
  | placed by the sibling project | 10 | 10.81 GiB | nested one level deeper, under `models/` |
  | orphaned Qwen weights | 4 | 28.89 GiB | removed from the script by v0.8, never from disk |
  | staging and cache leftovers | 23 | ~1 KB | the `.hf` tree, three `.cache/huggingface` trees, one 0-byte `.partial` |
  | **unaccounted for** | **0** | **—** | **the gate on phase 9's destroy** |

  Both projects' scripts are pinned and checksummed, so everything the first two classes hold is
  re-downloadable; the remaining 28.89 GiB answers to nothing.
- **The annotator gap is confirmed empirically.** All four annotator checkpoints —
  `yolox_l.onnx`, `dw-ll_ucoco_384_bs5.torchscript.pt`, `sk_model.pth`, `sk_model2.pth` — are
  **absent from the volume**. They were being re-fetched to container disk on every pod's first
  render, exactly as the proposal argued from reading the graph.
- **The antelopev2 pin is confirmed from the volume itself.** The leftover cache tree names
  `ba0c3e10f4548361eb9a63265d87ce1140ab5a05` — the same DIAMONIK7777 revision the manifest pins,
  recorded independently by a download this change did not make.
- **The volume was extended from 62 GB to 80 GB** by the operator during this phase, so the
  "98% full" pressure recorded in `proposal.md` is relieved. It does not change the plan: the
  volume is still replaced rather than pruned, because pruning proves nothing about the manifest.
- **Correction to `proposal.md` and `design.md`: the two repositories' `.env` files do *not*
  disagree.** Both name the same volume id, and it is the account's only volume. What differs is
  the **key name** — this repo uses `RUNPOD_VOLUME_ID`, the sibling `RUNPOD_NETWORK_VOLUME_ID` —
  which is almost certainly what was mistaken for a stale id. There is no stale id to reconcile;
  phase 9 still updates both.
- **Phase 9's open question is answered.** Both manifests together are ~27.3 GiB
  (this project 16.5 GiB across 15 entries, the sibling 10.8 GiB), so the new volume needs
  roughly 40 GB for comfortable headroom — half of what the current one now carries, once the
  orphaned Qwen weights are gone.

- **`README.md` and `CLAUDE.md` describe a pinned stack.** The weights line now says the stack is
  provisioned from a pinned, checksummed manifest and that the volume is namespaced per project;
  the layout gains `scripts/models.json`, `scripts/derive_manifest.py` and `isekai/provision.py`;
  the pod-lifecycle diagram shows the `/runpod-volume` mount and the namespace symlink.
  `CLAUDE.md` records that the living spec goes to five capabilities when `model-provisioning` is
  archived, and that `provision.py` is not in `convert.py`'s import graph, so the stdlib-only
  runtime rule is untouched. **No claim is made about identity, quality or the base** — this
  version changed none of them. The five-command gate array is unchanged.

- **The volume mounts at `/runpod-volume` and the models directory is one symlink into this
  project's namespace.** `infra/up.sh`'s `volumeMountPath` moves off `/opt/ComfyUI/models`, and
  `start.sh` points `/opt/ComfyUI/models` at `/runpod-volume/isekai`. Because
  `folder_paths.models_dir` is then itself inside the namespace, **every** node resolves there —
  including the InstantID node and the Impact Subpack, which ignore `extra_model_paths.yaml` and,
  unredirected, auto-download a broken nested antelopev2 pack. One symlink also makes a scratch
  namespace and a rollback the same operation.
- **The volume is shared, so nothing here reaches outside `/runpod-volume/isekai`.** Artifacts
  the sibling project also uses are duplicated rather than shared: at $0.07/GB/month that is
  about 32¢/month, and it keeps this project's manifest describing bytes this project's pins
  control.

- **`AUX_ANNOTATOR_CKPTS_PATH` moves 386 MB of annotator checkpoints onto the volume.**
  `comfyui_controlnet_aux` writes them to `<node dir>/ckpts` — the pod's container disk, which
  does not survive the pod — so `yolox_l.onnx`, `dw-ll_ucoco_384_bs5.torchscript.pt`,
  `sk_model.pth` and `sk_model2.pth` were re-fetched from Hugging Face, unpinned, during the
  first render of every pod, on metered time. Redirected onto the models tree they are ordinary
  manifest entries, fetched and verified ahead of time. The pack reads the variable as
  `os.getenv(NAME, default)`, so the environment wins over its own `config.yaml`.
- **⚠️ The pack's own log cannot confirm this.** It prints `Using ckpts path: …` from the
  *config-derived* value, not from the override, so it will report the old path while writing to
  the new one. Confirmation is a directory listing on the pod, never a log line. A future reader
  will otherwise reach for the log and conclude the redirect failed.

### Added

- **The graph and the manifest are bound by a test.** Every model filename `pipeline.json` names
  in a node's input must have a manifest entry, matched against the tail of a destination so
  `instantid/diffusion_pytorch_model.safetensors` and `openpose/diffusion_pytorch_model.safetensors`
  stay two files rather than one. This is the only mechanism that would have caught the annotator
  gap, and the only one that stops it reopening when v0.10 edits the graph.
- **A tracked mapping from node class to the files that node fetches for itself**
  (`PREPROCESSOR_MODELS`), carrying the half of the binding the graph cannot supply.
  `LineArtPreprocessor` names no file and downloads two. A graph containing a preprocessor whose
  class is absent from the mapping **fails** rather than passing silently — an unmapped
  preprocessor is an unknown quantity, not a safe default. An empty tuple is a real answer:
  `TilePreprocessor` fetches nothing, and `DWPreprocessor` names its two files in its own inputs.
  The reverse direction is deliberately not asserted — the manifest legitimately carries the
  antelopev2 pack, which `InstantIDFaceAnalysis` resolves by directory and no graph field names.

### Changed

- **`scripts/download_models.sh` is a thin driver over the manifest.** It asks
  `provision.py` for a plan, runs `wget` for whatever URL it is handed, and asks the module to
  verify and land the result. Every entry is decided before any byte moves, so a mismatch on a
  warm volume stops the run instead of surfacing halfway through a 6.9 GB transfer. The inline
  per-model shell variables are gone — every source is now a URL string the manifest carries and
  the suite can inspect.
- **The image carries provisioning's three files, not one.** The `Dockerfile` copied only the
  script; it now also copies `scripts/models.json` and `isekai/provision.py`, preserving their
  relative layout because the module resolves the manifest relative to itself. `start.sh` invokes
  the driver at its new path.
- **`wget` is installed in the image.** The previous downloader used the `hf` CLI, so the image
  never needed it; the ported one does, and the image shipped `curl` alone.
- **Pre-flight does not follow the redirect.** `resolve/<sha>/<path>` answers 302 and carries
  `x-linked-etag` on *that* response — the CDN it points at does not repeat it — so following the
  redirect loses the header and silently degrades every entry to post-download verification. All
  fifteen entries were confirmed live to pre-flight and match.

### Removed

- **The `hf` CLI dependency.** Sources are plain `resolve/<commit-sha>/` URLs fetched with
  `wget`. The cost is `hf`'s resumable, parallel transfer; the `.partial` discipline means an
  interrupted transfer restarts from zero rather than being trusted.

### Added

- **The provisioning policy, in `isekai/provision.py` and reachable by `pytest`.** For each
  manifest entry the module returns exactly one decision: **skip** (present and its digest
  matches), **abort** (present and it does not — and the file is *left on disk*, because the
  volume is shared and a file this run did not write is not this run's to remove), or **fetch**
  from a named source. A file already at its destination is hashed, never taken on its name:
  verification that ran only on the download path would leave a warm volume permanently
  unchecked, which is the case the digest exists for. `land()` verifies a transferred file and
  only then moves it into place, so an interrupted or tampered transfer never occupies the final
  name — the next run sees the file as absent rather than as present-and-trusted.
- **A pre-flight seam.** Hugging Face publishes a file's SHA-256 in the `x-linked-etag` response
  header, so a source whose published digest already disagrees with the manifest is rejected in a
  second rather than after a multi-gigabyte transfer, and the entry's next declared source is
  offered instead. This is an optimisation, never a check: a source that publishes nothing — or
  a header that cannot be read — degrades to download-and-post-verify, never to trust. The seam
  is injected and `FakeFetcher` is what keeps the suite offline, the same argument and the same
  shape as `FakeComfyClient`.
- **`scripts/models.json`, a pinned and checksummed manifest of every model artifact the
  shipped graph needs — fifteen files across eleven sources.** Each entry names a destination
  under the models tree, a SHA-256, and an ordered list of `resolve/<commit-sha>/` URLs, so a
  source addresses bytes that cannot move. Four of the entries are the annotator checkpoints
  `DWPreprocessor` and `LineArtPreprocessor` fetched for themselves at graph-execution time —
  386 MB that nothing in this repository named, and that every fresh pod re-downloaded onto
  ephemeral disk during a metered render. `LineArtPreprocessor` fetches both `sk_model.pth` and
  `sk_model2.pth` unconditionally, regardless of the graph's `coarse: "disable"`, so both are
  declared.
- **`scripts/derive_manifest.py`, the helper that produced it.** Digests are *derived*, never
  transcribed: Hugging Face publishes each LFS object's SHA-256 as its object id, so no artifact
  is downloaded to learn its digest, and every alternate source is cross-checked against its
  primary at derivation time. Revisions are data in the helper rather than resolved from a
  branch, so re-running it is byte-identical — `git diff --exit-code scripts/models.json` is the
  check that the tool and the committed data have not diverged.
- **`isekai/provision.py`, the manifest's reader and its offline checks** — no source resolves a
  mutable ref, every entry carries a well-formed SHA-256, and every entry whose primary source is
  a mirror rather than the artifact's publisher declares an alternate. Each check is proven
  against a deliberately malformed entry as well as against the tracked file. The module is
  stdlib-only (`json`, `re`, `pathlib`) and is not in `convert.py`'s import graph.

## [0.8.0] - 2026-09-04

### Removed

- **The `qwen`, `animagine` and `animagine-i2i` paths.** All three are superseded by
  `animagine-i2i-cn`, which alone preserves identity, composition and pose. Gone with them:
  `workflows/qwen-image-edit.json`, `workflows/qwen-image-edit.reference.json`,
  `workflows/animagine-instantid.json`, `workflows/animagine-i2i.json`, their test fixtures,
  `inject_qwen`, and the four Qwen downloads in `scripts/download_models.sh`.
- **The `model-registry` capability.** Its three requirements — name resolution, injector
  pairing and mutation pairing — all describe a choice that no longer exists, so
  `openspec/specs/model-registry/` and `tests/test_model_dispatch.py` are deleted. The living
  spec goes from five capabilities to four.
- **Tests bound to the deleted paths**, including
  `test_run_without_overrides_is_byte_identical_to_v04`, which pinned v0.4's output for a path
  that is now gone, and the Qwen-only guards for a wired `cfg` dial and a graph with no identity
  node. Deleting them took the suite from v0.7's 114 tests to 81; the count going down is the
  work, not a weakened gate.
- **`tests/fixtures/`.** The fixtures were byte-identical copies of the shipped graphs with no
  drift check — a second thing to rename and a silent divergence waiting to happen.
  `tests/conftest.py` now loads `workflows/pipeline.json` directly.
- **`--model`, `--workflow` and `--prompt`.** The whole required surface becomes
  `convert.py photo.jpg`. `--prompt` was **required**, so this is **BREAKING** for every
  existing invocation: the positive prompt is now committed to the graph, which is what makes a
  render attributable. `--workflow` has no equivalent — edit `workflows/pipeline.json`.
- **Variation 0's verbatim-seed exemption.** Its stated reason was back-compat with releases
  this change deletes, and it left `--seed` with two meanings: a stream seed for variations
  1..N and a literal sampler seed for variation 0. **BREAKING**: `--seed 42` no longer
  reproduces v0.7's first render.
- **The conditioning trace in `inject`.** With no prompt to place, the walk from
  `KSampler.positive` to the first `CLIPTextEncode` has no caller. Its non-obvious insight —
  that the sampler's positive input may reach the encoder through a stack of ControlNet apply
  nodes, so it must be followed rather than looked up — is recorded in the change's `design.md`
  and in the `workflow-injection` capability header.
- **The model registry and every seam with nothing passing through it.**
  `isekai/models.py`, `Model` and `get_model` are deleted, and `Injector` and `Mutator` go with
  them from `isekai/comfy_types.py`. `pipeline.run` loses its `inject` and `mutate` parameters
  and imports them instead. `ComfyTransport` **stays** a parameter — `FakeComfyClient` is what
  makes the suite offline — and so does `workflow`, which keeps file I/O in the CLI. The rule
  this change learned: *a parameter is a seam only if something else is actually passed through
  it.*
- **Every branch with no reachable caller**: `overrides.py`'s silent no-op when a graph carries
  no `ApplyInstantIDAdvanced`, `mutate.py`'s wired-dial guard (it existed because Qwen wired
  `cfg`) and its `"102:14"` subgraph-id ordering, the `mutate is None` branch in `run`, and
  `find_node`'s `title` parameter — which no caller ever passed.
- **`arms crossed` from the committed positive prompt.** Pose is the OpenPose ControlNet's axis;
  a pose tag in the prompt competes with the mechanism that owns it. That is an architectural
  argument and needs no render to justify it — **this change makes no claim about what the graph
  now renders.**

### Changed

- **The surviving path is renamed to nothing.** `workflows/animagine-i2i-cn.json` →
  `workflows/pipeline.json`, `workflows/animagine-i2i-cn_ui.json` →
  `workflows/pipeline_ui.json`, `inject_animagine` → `inject`, and the one remaining `--model`
  value → `pipeline`. Every name available today describes the base or the technique, and v0.9
  replaces the base; the only name that version cannot invalidate is no name. The flag itself
  is then removed outright — see below.
- **Spec keys lose their model segment**:
  `workflow-injection:photo-wiring:controlnet-single-loader-across-stack` →
  `…:single-loader-fans-out`, and
  `workflow-injection:latent-init:img2img-inits-from-photo-below-one` →
  `…:inits-from-photo-below-one`.
- **BREAKING: `-o` names a directory, not a file**, defaulting to `./outputs`. A run writes
  `<output-dir>/<UTC instant>/0.png` … and a `run.json` beside them. An `-o` naming a file with
  an image extension is **rejected at parse time** — otherwise an upgrading caller silently gets
  a directory called `out.png`.
- **BREAKING: `--variations` defaults to 5**, capped at 25. Five renders to choose between is
  the product rather than an option; the ceiling exists because every variation is one billed
  GPU render, so an unbounded count bills a mistyped digit at GPU rates.
- **Every variation's seed is derived uniformly** from `--seed`, variation 0 included. The
  per-variation seed is still printed, and is now also recorded in `run.json`.
- `main()` resolves the run directory and hands the **resolved** path to `run`, which draws no
  clock of its own — which is what keeps the suite offline and deterministic.

### Added

- **Timestamped run directories and `run.json`.** The manifest records the seed the run was
  given, the per-variation seeds actually drawn and the dial values in force, so a run describes
  itself instead of depending on the operator still having the terminal it was printed to.
- **The positive prompt is pinned by equality** in the suite, and commented in
  `workflows/pipeline_ui.json` with the version that owns its register. "The string holds no
  subject text" has no mechanical form — a blacklist assertion is defeated silently by any
  rewrite — so equality makes every future prompt edit a deliberate test edit.
- **`README.md` and `CLAUDE.md` describe one path.** The four-row model table, `--model` and
  `--prompt` in the quickstart, and the "four selectable models" status line all go; the run
  directory layout is shown instead. `CLAUDE.md` retires the additive-models invariant — **"there
  is one path; a version may replace it, it may not add a second"** — and replaces the registry
  seam with the rule this change learned: *a parameter is a seam only if something else is
  actually passed through it.* The conditioning-trace insight the deleted code carried is
  preserved there by name.
- The `README.md` license line no longer claims to match a model license the repo does not ship;
  it states the repository's own licence and that weights are licensed by their publishers.
- **`CLAUDE.md`'s metered-work guardrail is rewritten.** Teardown confirmed through the RunPod
  MCP replaces the blanket "wait for an explicit human go". The new rule states all four things
  the old protocol got for free from a human being present: who **creates** (`infra/up.sh`), who
  **tears down** (`infra/down.sh` — teardown is the act), who **confirms** (the MCP — and
  confirmation is *not* the act), and what it **degrades to** when the MCP is unreachable (the
  human "go", unchanged, for the whole session). It carries a stated ceiling: **45 minutes,
  ~$0.30** per pod session. This is an authority *expansion* in an otherwise subtractive change,
  which is why it is its own entry rather than folded into the docs one.

### Verified

- **The one path was run live on a GPU pod on 2026-09-04**, on our own image against the
  persistent models volume: `convert.py <photo>` exited 0 for two separate input photos, each
  writing `outputs/<UTC instant>/` with `0.png`–`4.png` and a `run.json` carrying five seeds.
  This records that the path **runs**; it makes no claim about fidelity, identity or quality,
  for which this repository still has no evaluator.

### Known defects

- **`1girl` fixes the gender of every input photo**, in a product whose input is "a photo of a
  person". `1girl, solo` is the Danbooru mode selector for this base rather than subject text,
  and an empty positive is not neutral on a Danbooru-trained checkpoint, so removing it would be
  a register decision. v0.8 changes no base and therefore decides no register: the defect is
  stated here and owned by **v0.9**, the version that can probe a replacement against real
  renders.

## [0.7.0] - 2026-09-01

Adoption of the OpenSpec SDD repository standard, plus the defects that adopting it exposed.

### Added

- **The spec tree.** `openspec/specs/` across five capabilities — `model-registry`,
  `workflow-injection`, `workflow-mutation`, `comfy-transport`, `cli` — as keyed scenarios
  describing behaviour the repo already shipped. 91 scenarios across 22 requirements.
- **The change tree.** `openspec/changes/` with `archive/`, and `0001-mf-standard` carrying
  all four artifacts. The zero spec delta is declared with `skip_specs: true` in a tracked
  `.openspec.yaml`, so `openspec validate --strict` passes.
- **Spec-to-test binding.** `spec` and `spec_exempt` markers registered in
  `[tool.pytest.ini_options]`, and every test bound to the scenario it proves — 117 bindings,
  zero unmarked tests.
- **A root `Makefile`** with a `gate` target mirroring the declared gate array command for
  command, so the gate a human types cannot drift from the one the orchestrator runs.
- **`.python-version`**, pinning the interpreter to 3.12.
- **`## How a change is cut here` in `CLAUDE.md`** — the change contract stated in-tree for
  the first time: the four artifacts, the id scheme, the authoring commands, the `Change:`
  trailer, the version line.
- **Docstrings and type annotations throughout `isekai/`**, under a widened ruff selection.
- **This file.**

### Changed

- **The gate config moved to `.minions/minions.toml`**, the one path the orchestrator reads;
  `.gitignore` now excludes `.minions/*` while re-including that single tracked file.
- **CI invokes `make gate`** rather than keeping a third copy of the command list, which had
  already drifted — it was running `ruff format --check` and `ruff check` without the `.` the
  array names.
- **Ruff lint selection widened** from ruff's default to `["E", "F", "I"]`, then to
  `["E", "F", "I", "D", "ANN"]`. Selecting `E` whole enables `E501` line-length; `D` and `ANN`
  add docstrings and annotations.
- **`CLAUDE.md` rewritten** onto the repo's in-tree contract, and then onto the standard's
  template.
- **`README.md` rewritten.** It had duplicate `Quickstart` and `Setup` sections, marked
  shipped files `(planned)`, named one model where four ship, and mentioned the gate nowhere.
- **`.env.example` is now path-free**, declaring shape only.

### Fixed

- **`--variations N` billed N identical renders** on `qwen` and `animagine`. Both are
  registered without a mutation seam, so the graph never varied and N paid renders produced
  one image. Now refused before the photo is uploaded.
- **`--seed` was validated and then silently discarded** on those same models.
- **`--variations 0` uploaded the photo, rendered nothing and exited 0.** Now rejected at
  parse time.
- **`mutate` crashed with a bare `TypeError` on a linked dial.** In ComfyUI API format an
  input may legally be a `[node_id, slot]` link, and `workflows/qwen-image-edit.json` drives
  `cfg` that way — so a documented flag combination died on a raw arithmetic error. Now stops
  with a message naming the dial and the node driving it.
- **`--denoise 0.0` was silently discarded**, the value being falsy rather than absent.
- **`ValueError` on subgraph node ids.** Node ordering used `sorted(key=int)`, which cannot
  parse an id like `102:14`; the repo ships a graph containing exactly that.
- **A stray `$` in the unknown-model exit message.**

## [0.6.0] - 2026-08-15

### Added

- **`isekai/overrides.py`** — an `apply_overrides` seam setting user-chosen base dial values
  by `class_type`, and `--denoise` `[0, 1]`, `--cfg` `[0, 30]`, `--ip-weight` `[0, 1]` on the
  CLI, with a bounded-float argparse type factory turning an out-of-range value into a clean
  exit. `pipeline.run` applies overrides per variation **before** `mutate`, so
  `--denoise X --variations N` jitters around `X` and `--seed` reproduces the set.
- **`.minions/minions.toml`** (as `minions.toml` at the root), first declaring the gate array.

### Changed

- **Jitter is base-relative.** `mutate` reads a node's current value as the base and draws
  `uniform(base ± δ)` instead of an absolute `uniform(lo, hi)` — denoise ±0.05, cfg ±0.5,
  ip_weight ±0.05, each clamped to its valid bound. At the baked defaults this is
  byte-for-byte identical to the previous behaviour, pinned by a characterization test.

## [0.5.0]

Skipped — see the note at the top of this file.

## [0.4.0] - 2026-08-04

### Added

- **The workflow-mutation seam.** `mutate(workflow, rng)`, separate from `inject_*`: sets the
  KSampler seed and bounded-jitters `denoise` / `cfg` / `ip_weight`. `random.Random` is
  dependency-injected, so randomized code is deterministically unit-tested.
- **`--seed` and `--variations`**, validated at the boundary. Each variation's seed is
  printed — the reproducibility contract.
- **The `animagine-i2i-cn` model** — `animagine-i2i` plus a tile / OpenPose / lineart
  ControlNet stack, with `comfyui_controlnet_aux` and the SDXL ControlNet weights pinned into
  the image.
- **A generalized injection trace.** `inject_animagine` now walks `.positive` to the first
  `CLIPTextEncode`, so it lands through a ControlNet chain of any depth and serves the whole
  InstantID family.
- **ControlNet strength jitter** — every `ControlNetApplyAdvanced` strength varies ±0.1 around
  its tuned baseline, in deterministic node-id order so a seed reproduces the whole graph. A
  no-op on graphs without ControlNet nodes.

### Changed

- The default `--model` is now `animagine-i2i`.

## [0.3.0] - 2026-07-31

### Added

- **The `animagine-i2i` model** — the Animagine + InstantID base as img2img, taking its latent
  init from the photo via `VAEEncode` at `denoise < 1`, so the photo's composition survives.
  `denoise` becomes the identity-versus-style dial.
- The real exported Animagine img2img workflow, with the test fixtures locked to it.

## [0.2.0] - 2026-07-31

### Added

- **Model dispatch.** `--model {qwen,animagine}`, built test-first: each model owns a workflow
  JSON and an injection strategy, resolved through a name-to-`Model` registry.
  `pipeline.run` takes the strategy as a parameter rather than hardcoding Qwen.
- **The `animagine` model** — Animagine XL 4.0 with InstantID and InsightFace, where identity
  is an injected signal (face embedding and keypoints) on a from-noise SDXL base. InstantID
  nodes and weights added to the image.
- **The test harness and the transport seam** — a `uv` project with pytest, and a fake client
  standing in for ComfyUI so the suite runs offline.
- The real exported Animagine + InstantID workflow, with the test fixtures locked to it.

## [0.1.0] - 2026-07-28

### Added

- **The headless conversion pipeline.** `convert.py`, a zero-dependency CLI (stdlib `urllib`
  only) that uploads a photo, injects photo and prompt into a ComfyUI workflow by node
  `class_type` / title, submits to `/prompt`, polls `/history` and downloads from `/view`.
- **The container environment as code.** A CUDA base image with `uv`, PyTorch and ComfyUI
  serving on `:8188`, no model weights baked in; a compose file for local GPU passthrough;
  CI publishing the image to GHCR; and `scripts/download_models.sh` fetching Qwen-Image-Edit.
- **SSH into the pod image**, so `ssh -L` can reach ComfyUI privately: `start.sh` installs the
  injected public key, starts `sshd`, then runs ComfyUI in the foreground.
- **On-demand pod lifecycle.** `infra/up.sh` creates a pod from the GHCR image with the models
  volume and SSH attached, polls for its address and prints the tunnel command;
  `infra/down.sh` deletes it so per-second billing stops.
- **Self-provisioning models on boot** — `start.sh` downloads weights idempotently before
  launching ComfyUI, so a fresh pod populates the volume without manual setup.
- The validated API-format Qwen-Image-Edit workflow, and the runbook to drive it.

### Fixed

- **Blackwell (sm_120) GPUs could not run the image.** cu124 kernels gave "no kernel image is
  available"; PyTorch is pinned to 2.8.0 / cu128, whose wheels ship sm_120 kernels.

[Unreleased]: https://github.com/alxb1t/isekai/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/alxb1t/isekai/compare/v0.3...v0.7.0
[0.6.0]: https://github.com/alxb1t/isekai/compare/dffdd63...bbe6924
[0.4.0]: https://github.com/alxb1t/isekai/compare/v0.3...dffdd63
[0.3.0]: https://github.com/alxb1t/isekai/compare/v0.2...v0.3
[0.2.0]: https://github.com/alxb1t/isekai/compare/v0.1...v0.2
[0.1.0]: https://github.com/alxb1t/isekai/releases/tag/v0.1
