# Design — 0001-mf-standard

The *how* for the seven scope items in `proposal.md`. Everything here is decided; nothing is left open.

## 1. The change's own spec delta is **N-A**

This change adds **no behaviour**. It moves a config file, pins a toolchain, adds a `Makefile` target, writes
documentation, and annotates tests. `convert.py` and every module under `isekai/` come out byte-identical except
for import ordering that `ruff --select I` may normalise.

So the absence is **declared** rather than papered over with an invented requirement: the change's tracked
`.openspec.yaml` carries `skip_specs: true`, and `specs/` holds only `.gitkeep`.

**Two mechanical facts about that marker, both learned by running the validator rather than assumed** (phase 13).
`skip_specs` is honoured only when `.openspec.yaml` is *valid change metadata*, which requires a `schema:` key
naming a resolvable schema (`spec-driven`, the packaged default); without it the marker is parsed, rejected, and
the change fails `--strict` exactly as if it were absent. And the marker is **mutually exclusive with any `.md`
under `specs/`** — the validator treats every one as a delta file, so a `specs/README.md` explaining the N-A is
itself the error it explains. This section is therefore the only home for that reasoning, which is why the
paragraph above absorbed it. Precedent for an N-A delta: `0004-planning-skills`.

**The backfill is written directly into `openspec/specs/`, not routed through this change's delta.** That is the
substantive decision, and the reason is mechanical rather than stylistic: a delta is folded into the living spec
at *release*, and `sdd:specs-tree` checks that `openspec/specs/<capability>/spec.md` **exists**. A delta sitting
unfolded in a change directory satisfies nothing, so routing the backfill through it would leave the blocking gap
open until ship — and a "delta" that adds requirements the code has already shipped is a false record besides.
The living spec is where already-shipped behaviour belongs; a delta describes what a change *changes*.

## 2. Capabilities — five, by module cluster

Chosen to mirror the existing module and test-file split as closely as the code allows, so each test file maps to
exactly one capability and the 86 markers are mechanical rather than judgment calls.

| Capability | Source | Test file(s) | Tests |
|---|---|---|---|
| `model-registry` | `isekai/models.py` | `test_model_dispatch.py` | 12 |
| `workflow-injection` | `isekai/workflow.py` | `test_workflow_injection.py` | 15 |
| `workflow-mutation` | `isekai/mutate.py`, `isekai/overrides.py` | `test_mutation.py`, `test_variations.py`, `test_overrides.py` | 30 |
| `comfy-transport` | `isekai/multipart.py`, `isekai/comfy_client.py` | `test_multipart.py`, `test_polling.py` | 5 |
| `cli` | `isekai/cli.py` | `test_cli.py` | 24 |

`isekai/pipeline.py` and `isekai/comfy_types.py` are **orchestration and type declarations** — they carry no
behaviour of their own that a scenario could assert, and no test file targets them directly. They are covered
incidentally through the capabilities above rather than given one of their own.

`workflow-mutation` is the one cluster that merges two modules. `overrides.py` (`apply_overrides`, the CLI dials)
and `mutate.py` (seeded jitter) are two halves of one observable behaviour — *what determines the dial values a
render runs with* — and `--seed`, `--variations`, `--denoise`, `--cfg` and `--ip-weight` are read by a user as one
surface. Splitting them would put the base value and the jitter applied to it in different specs.

## 3. Scenario keys and layers

Keys are `<capability>:<requirement-slug>:<scenario-slug>`, all lower-kebab — e.g.
`model-registry:name-resolution:unknown-model-rejected`. The capability segment matches the directory under
`openspec/specs/`, so a key locates its own spec file.

**Every scenario declares `Layers: unit`, and none declares `e2e`.** The rubric reserves `unit` + `e2e` for
system-boundary behaviour, and this repo's only true system boundary is the ComfyUI transport — which is
**fully mocked** in tests behind the `ComfyTransport` Protocol, by a standing invariant that no test hits a real
GPU or the network. The genuine end-to-end check here is a human judging an image on a live pod, which is not an
assertable layer. Declaring `e2e` would promise a test tier this repo has deliberately chosen not to have.

## 4. Test binding — markers and registration

Both marker names are registered in `[tool.pytest.ini_options] markers` in `pyproject.toml`, which is the
test-runner manifest for this repo (there is no `pytest.ini` or `setup.cfg`). Registration is not optional
bookkeeping: an unregistered marker is silently ignored by pytest and binds nothing, which is the exact failure
`sdd:test-binding` exists to catch.

```toml
[tool.pytest.ini_options]
markers = [
    "spec(key): binds this test to a keyed scenario in openspec/specs/",
    "spec_exempt(reason): declares this test structural — it proves no scenario",
]
```

Applied as `@pytest.mark.spec("<key>")` on behavioural tests. `spec_exempt` is for genuinely structural tests —
fixture-shape assertions, golden-fixture contract locks that assert the JSON's node IDs rather than the
pipeline's behaviour. **The exemption is a declaration, not an escape hatch:** it is used where a test really
proves no scenario, and each one carries a reason a reader can disagree with.

Scenarios and tests are **not** one-to-one. Several tests may share a key where they prove the same behaviour
over different inputs (the four model fixtures, for instance), and that is expected — the key binds a test to the
behaviour it proves, not to a private slot.

## 5. The gate config move

`git mv minions.toml .minions/minions.toml` — **the array is not edited**. It already covers five axes in the
right order (`uv sync --locked` → `ruff format --check` → `ruff check` → `ty check` → `pytest`), which is what
`gate:covers-axes` will assess once it is readable. Moving it is the whole fix.

`.gitignore` gains the pair `.minions/*` then `!.minions/minions.toml`, in that order — run artifacts the
orchestrator writes under `.minions/` stay out of history, the config stays in. Order matters: git cannot
re-include a file whose parent directory is excluded, which is why the pattern is `.minions/*` and not
`.minions/`.

## 6. Toolchain pins

**`.python-version` = `3.12`.** `uv` currently resolves 3.12.11 here and `requires-python` is `>=3.12`. The pin
is the **minor** series rather than the exact patch: it is the floor `requires-python` already declares, it keeps
CI and local machines on one interpreter series, and it does not force a lockfile-irrelevant churn every patch
release. `uv` reads this file directly.

**Ruff `select`.** `pyproject.toml` currently has no `[tool.ruff]` table at all, so ruff has been running its
default rule set — which does include `E` and `F`, but **not `I`**. Making the selection explicit is therefore a
real change and not a formality:

```toml
[tool.ruff.lint]
select = ["E", "F", "I"]
```

**What this actually cost, recorded after the fact.** The predicted risk was import churn from `I`. That is
**not** what happened: `I` flagged nothing — imports were already ordered — and the 7 errors that appeared were
all **`E501` (line too long)**. The cause is that ruff's default selection is `E4`, `E7`, `E9` and `F`, a
*subset* of `E`; selecting `E` whole newly enables the `E5` line-length family. Selecting the narrower subset
would dodge this, but the criterion asks for at least `E`, so the broad selection is the compliant one and the
7 lines are the price.

All 7 were **one-line docstrings and comments** at 89–91 characters, in `comfy_client.py`, `comfy_types.py`,
`overrides.py`, `workflow.py` (×3) and `test_workflow_injection.py`. The formatter never wraps prose, which is
why they had survived at 88-column formatting all along. They were wrapped by hand in the phase-3 commit; **no
statement, signature or logic was touched**, and `ruff format --check` reported no reformatting needed
afterwards, confirming the edits were confined to comment text.

## 7. `CLAUDE.md`, and why it is last

Three (J) clauses have to become true, and each depends on work in an earlier phase:

- **no retired `implementation_plans/` model as source of truth** — the current text (`CLAUDE.md:24-27`, `33-34`)
  makes the highest-numbered `vX.Y_implementation_plan.md` the authority. That becomes `openspec/changes/<id>/`.
- **its account of where progress lives matches the repo** — currently the vault's `overview.md` `current_phase`,
  the plan's Progress ledger and `log.md` (`CLAUDE.md:28-31`, `99-101`). That becomes the `## Progress` checklist
  in `tasks.md`.
- **its gate account matches what the array actually runs** — flags included, because a literal command quoted in
  prose is a literal command and the human types the one the doc shows.

None of the three can be written truthfully until the config has moved, the ruff table exists and the spec tree
is populated. Writing it earlier would mean writing it twice, and the intermediate version would be false.

**What survives the rewrite:** the vault is not being retired. `VAULT_PROJECT_DIR`, `.env` hygiene, the
research/findings files, `log.md` and the metered-GPU protocol all stay, and the guardrails section is accurate
as it stands. The edit is narrow — it re-points *"where does the contract live"* in-tree and corrects the gate
account. It does not rewrite the repo's description of itself.

## 8. Ruff `D` + `ANN` — the two scoping decisions, and why they are not waivers

Widening `select` to `["E", "F", "I", "D", "ANN"]` raised **289 errors: 36 in `isekai/`, 253 in `tests/`.** The
runtime 36 are all fixed outright — module docstrings on all ten modules, docstrings on `Model`, `Overrides`,
`ComfyTransport`'s four methods and `get_model`, return annotations on `main` and `_bounded_float`, and D205/D209
style repairs. No exclusion applies to `isekai/`.

The 253 in `tests/` needed two decisions. The guardrail is that a loosened config is a *plan* problem, so each is
recorded here with its reasoning rather than left as a bare line in `pyproject.toml`.

**8.1 `ignore = ["D203", "D213"]` — forced, not chosen freely.** `D203`/`D211` and `D212`/`D213` are mutually
exclusive **by construction**: selecting `D` whole enables both halves of each pair, and ruff resolves them itself
while printing a warning on every single run. One of each pair must go. Choosing explicitly silences the warning
and makes the choice reviewable, and both picks match what the code already does — `D211` (no blank line before a
class docstring) and `D212` (multi-line summary starts on the first line). Zero code changed as a result. This is
the only blanket `ignore` in the file.

**8.2 `per-file-ignores = {"tests/*" = ["D1"]}` — the one real scoping call.** 132 of the 253 were "missing
docstring" on test functions. This repo's stated convention, in `CLAUDE.md` and in the standard, is that **tests
are named as behavioural sentences and double as documentation**. A docstring on
`test_unknown_model_exits_with_a_legible_message` restates the name, adds nothing, and rots independently of it.
So `D1xx` is waived, in `tests/` only.

**What is deliberately *not* waived there, because the waiver would then be a real weakening:** the `D2xx`/`D4xx`
style rules stay on, so any docstring that *is* written must still be well-formed — and two were repaired under
that rule (`D401`, imperative mood). All of `ANN` stays on: a wrong fixture annotation is a genuine defect, and
`-> None` on a test costs nothing.

**The annotation work itself surfaced one method note.** The first attempt annotated fixture parameters by regex
on the parameter name, which matched **call sites inside test bodies** as well as signatures and produced 100+
syntax errors. It was reverted wholesale and redone with an `ast` walk that edits only `arg` nodes of a
`FunctionDef`. Machine-editing Python by regex on an identifier is not safe; the parser already knows which
occurrence is a parameter.

`ANN401` then rejected `*args: Any` on the two `run` doubles in `test_cli.py`. The fix is `object`, not an
exclusion: those doubles only *record* their arguments, so `object` is both accepted and strictly more precise
than `Any`.

**Verified after the change:** gate green on all five axes · 114 tests still passing · **117 spec markers before
and 117 after, with zero unmarked test functions** — the annotation pass moved no binding · and every line
removed from `isekai/` by the diff is docstring prose, so no runtime behaviour changed.
