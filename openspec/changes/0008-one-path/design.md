# Design — 0008-one-path

**Verdict: `feasible-with-caveats`.** The subtraction itself is mechanical and local. The caveats are
three: one unverified tooling behaviour (`openspec` **archiving** a capability reduced to zero — the
delta itself validates), one
unverifiable-without-a-GPU render change (the prompt edit), and one guardrail that ships before its
first real use (the spend rule). Each is named below with the phase that resolves it.

## Context

See `proposal.md — Why` for motivation. The design-relevant state of the repo at v0.7.0:

- Four paths resolve through a name→`Model` registry in `isekai/models.py`. Three are dead; the
  fourth, `animagine-i2i-cn`, is the product.
- `pipeline.run` takes `inject` and `mutate` as parameters. The registry fills them in. Nothing else
  ever has — `tests/test_variations.py` passes the real functions, and `tests/test_cli.py` fakes
  `run` itself rather than substituting through those seams.
- `tests/fixtures/*.json` are **byte-identical copies** of `workflows/*.json`, with no check that
  they stay so.
- Several defensive branches exist solely for deleted graphs: `overrides.py` no-ops `ip_weight` when
  no `ApplyInstantIDAdvanced` exists (qwen), `mutate._base` refuses a dial wired to another node
  (qwen's `cfg`), `mutate._node_order` parses `"102:14"` subgraph ids (no surviving graph has one),
  and `find_node` takes a `title` argument no caller passes.
- The gate is green: `uv sync --locked`, `ruff format --check`, `ruff check`, `ty check`, `pytest`
  (114 tests). It runs offline and deterministically, which is a constraint on everything below.

## Goals / Non-Goals

**Goals:**

- One path, reachable one way, with nothing about it typed at the command line.
- Every abstraction that survives has more than one thing passing through it.
- The living spec describes the product, not its history — no orphaned scenario, no capability
  describing a choice that no longer exists.
- The change is buildable and verifiable locally; exactly one phase spends money, and it spends it
  last.

**Non-Goals:**

- **No base change.** The checkpoint, the ControlNet stack, the InstantID weights and the network
  volume are untouched. That is v0.9's work and everything uncertain about it belongs there.
- **No quality claim.** This change may assert that the path *runs*. It may not assert that it
  renders better, or that identity is better preserved. There is no evaluator yet; that is two
  versions out.
- **No new register.** The positive prompt's register tags are checkpoint-family specific. v0.8
  removes one pose tag and decides nothing else about the string.
- **No tagger seam.** A future WD14 tagger needs a purpose-built entry point, designed against the
  base it will run on.

## Decisions

### D1 — The survivor is renamed to nothing

`workflows/pipeline.json`, `workflows/pipeline_ui.json`, `inject()`, and spec keys with no model
segment.

*Why:* the name lands in the JSON filename, the UI export, the injector and ~30 spec keys, so
renaming is expensive and worth doing once. Every **descriptive** name available today describes the
base (`animagine`), the technique (`instantid`, `i2i`, `cn`), or both — and v0.9 replaces the base.
If the new base is not SDXL, InstantID goes with it. A name that describes what is being replaced is
a name that gets renamed twice.

*Alternatives:* keep `animagine-i2i-cn` (accepts the second rename); pick a new descriptive name
(same problem, one version later). Rejected — the only name v0.9 cannot invalidate is no name.

### D2 — The registry is deleted, not reduced to one entry

`isekai/models.py`, `Model`, `get_model` and the `model-registry` capability all go.

*Why:* a one-entry `dict` with an unreachable "unknown name" branch is a dispatch mechanism with
nothing to dispatch. `CLAUDE.md` currently calls the registry a load-bearing seam on the grounds that
"adding a model is a registry entry, not a branch" — but the additive-models invariant is itself
being retired, so the justification goes with it. Keeping the registry would be a bet on v0.9's shape
that has not been made: whether the new checkpoint is a registry entry or a replaced constant is
undecided.

*Alternative:* keep it as a one-entry map "because v0.9 will need it". Rejected as speculative
generality — the exact thing this change exists to remove.

### D3 — A parameter is a seam only if something else is actually passed through it

`pipeline.run` loses `inject`, `prompt` and `mutate`; it imports `inject` and `mutate` directly.
`Injector` and `Mutator` disappear from `isekai/comfy_types.py`. `client` **stays** a parameter, and
`workflow` **stays** a parameter.

*Why:* `ComfyTransport` earns its parameter — `FakeComfyClient` is what makes the whole suite
offline. `inject` and `mutate` never had a second implementation and never had a test double; they
were parameters because the registry filled them in, and the registry is gone. `workflow` stays so
`run` does no file I/O and the CLI keeps ownership of path resolution.

This rule is written into `CLAUDE.md` in the docs phase, because it is the general form of what this
change learned.

### D4 — The output is a timestamped directory, resolved by the CLI

`-o` names a **directory** (default `./outputs`). The CLI resolves `<dir>/<UTC instant>/` and hands
the resolved path to `run`, which writes `0.png` … `4.png` and `run.json` into it.

*Why the CLI resolves it:* a `datetime.now()` inside `run` makes the output path unassertable, and
this suite's entire discipline is injected nondeterminism — `random.Random(seed)` is passed in, never
drawn inside. Resolving in `main()` keeps `run` a pure function of its arguments and adds no clock
seam for a single caller.

*Format:* compact basic ISO, `20260904T141530Z`. Colons are legal on APFS but Finder renders them as
`/` and they are illegal on Windows checkouts.

*The extension guard:* `-o out.png` was valid in v0.7 and would now silently create a *directory*
named `out.png`. Parse-time rejection with a message naming the change is three lines and is the only
thing standing between an upgrading caller and a very confusing folder.

*`run.json`:* with five derived seeds printed to stdout, reproducing render 3 next week otherwise
requires still having the terminal. The manifest moves reproducibility from a property of the
operator's scrollback to a property of the artifact.

*Alternatives:* inject a clock into `run` (a seam for one caller); keep `-o` as a file and default
`--variations` to 1 (preserves a filename at the cost of the product).

### D5 — Every variation's seed is derived; variation 0 loses its exemption

*Why:* the exemption's stated reason in `pipeline.py` is "what earlier releases rendered from" —
those releases ran paths this change deletes. What remains is a flag with two meanings: a stream
seed for variations 1–N and a literal sampler seed for variation 0. One meaning is cheaper to
document and to reason about, and the printed per-variation seed plus `run.json` preserve every
reproducibility property the exemption provided.

*Trade-off:* `--seed 42` no longer produces the same render 0 as v0.7. Nothing else in this change
preserves v0.7 render output either — see R2.

### D6 — Only the pose tag leaves the prompt

The committed positive loses `arms crossed` and keeps the rest, including `1girl, solo`.

*Why:* `arms crossed` is removable on a purely **architectural** argument that needs no render to
justify — pose is the OpenPose ControlNet's axis, and a pose tag in the prompt competes with the
mechanism that owns it. `1girl, solo` is not subject text in the Danbooru sense; it is the mode
selector for the base, and an empty or subject-less positive is **not** neutral on a Danbooru-trained
checkpoint. Removing it would be a register decision, and v0.8 changes no base and therefore decides
no register.

*Known defect, stated rather than smoothed over:* `1girl` fixes the gender of every input photo, in a
product whose input is "a photo of a person". This is a real correctness problem, it is recorded in
`CHANGELOG.md`, and it is owned by the version that changes the base — because that is the version
that can probe a replacement against real renders.

*Alternatives:* empty positive (a register decision this version may not make); drop
`1girl, solo, arms crossed` wholesale (same, plus a larger unverified render change).

### D7 — The prompt is pinned by a literal, not by a blacklist

The suite asserts the graph's positive string **equals** a literal it holds.

*Why:* "the committed string holds no subject text" has no mechanical form — a test asserting
`"arms crossed" not in text` is a blacklist any rewrite defeats silently. Equality makes every future
prompt edit a deliberate test edit, which is exactly the property "not typeable" is trying to name.

### D8 — The conditioning trace is deleted, and its insight is written down

With no prompt to place, `inject` wires the photo and nothing else; the walk from `KSampler.positive`
to the first `CLIPTextEncode` has no caller and goes.

*Why not keep it as an unused helper:* dead code with no caller is what this change is removing.

*What is preserved, and where:* the non-obvious fact — that `KSampler.positive` may point at
`ApplyInstantIDAdvanced` directly **or** through a stack of `ControlNetApplyAdvanced` nodes, so the
encoder must be found by following the link rather than by class lookup — is recorded here and in the
`workflow-injection` capability header. A future tagger rebuilds the trace deliberately, as a
purpose-built entry point, rather than inheriting one shaped by a deleted flag.

### D9 — Fixtures are deleted; the suite reads the shipped graph

`tests/fixtures/` goes; `conftest.load_fixture` reads `workflows/`.

*Why:* the fixtures are byte-identical copies with no drift check, so they are a second thing to
rename and a silent divergence waiting to happen.

*Trade-off, stated:* a fixture that **is** the shipped graph can never catch an unintended edit to
that graph. Nothing catches that today either — and D7 now pins the one field that matters most.

### D10 — The spend rule ships in its own phase, last but one

`CLAUDE.md`'s metered bullet is rewritten: teardown confirmed through the RunPod MCP replaces the
explicit human "go". The rewrite must state three things the original protocol got for free from the
human: **who creates** (`infra/up.sh`), **who confirms** (`down.sh` performs teardown; the MCP
*confirms* the pod is gone — confirmation is not the act), and **what happens when the MCP is
unreachable** (the human gate is back). It carries a ceiling: 45 minutes, ~$0.30.

*Why its own phase, and why late:* it is an authority **expansion** in an otherwise subtractive
change. Burying it mid-stream is how it escapes review. Phase 8 is its first exercise, with the
operator present.

### D11 — Phase 8 is a blocking, metered, hand-off phase

The build **halts**. The agent brings the pod up and tears it down (exercising D10); the operator
supplies a photo, runs `convert.py`, and judges. Pass criterion is a checklist written **before** the
run, not "are we okay". Nothing from the run is tracked — not the photo, not the renders.

*Why blocking:* a smoke test that cannot fail tests nothing, and "the path runs" is the only claim
this version is permitted to make, so it is the one worth blocking on. A failure adds phases to
`0008-one-path`; it does not become `0009`.

*Why nothing is tracked:* the input would be the repo's first tracked binary, and committing five
renders of a specific tuning in a repo whose next version changes the base means stale images that
edge toward the quality claim this change forbids.

*Why this is not an empty phase:* the paid run is the act; the commit is its record — a ticked box, a
`tasks.md` result and one `CHANGELOG.md` line. Say so explicitly, because Phase 0 of the original
plan was cut for being a phase with no act, and this one must not read the same way.

### D13 — A narrowed requirement is expressed as REMOVED + ADDED, not MODIFIED

`openspec` 1.11 has **no scenario-level removal**: a `## MODIFIED Requirements` block must repeat
every scenario the current spec still has, and validation rejects one that omits any
(`findMissingCurrentScenarios`). Renaming does not escape the check either — the validator walks the
rename chain back to the original block.

So a requirement whose scenario set *narrows* is declared **REMOVED** with a Reason and Migration,
and re-**ADDED** under a new name carrying only the surviving scenarios. Seven requirements are
handled this way across `cli`, `workflow-injection` and `workflow-mutation`; each new name is a
plain restatement (`Photo wiring` → `Photo wiring into the one graph`) and each REMOVED block says
which scenarios went and why.

*Consequence for the build:* requirement **names** change in the living spec even where behaviour
does not. Scenario **keys** are the stable identifier and are unchanged except for the two renamed in
phase 2, so `@pytest.mark.spec` bindings are unaffected by this decision.

*Requirements genuinely unchanged are simply absent from the delta* — `workflow-mutation`'s "Jitter is
relative to the current base", `workflow-injection`'s "img2img latent initialisation", and the whole
of `comfy-transport`.

### D12 — This is not a pure refactor, and the record says so

Timestamped run directories and `run.json` are **additions**. `CHANGELOG.md` gets a non-empty
`### Added`, and `### Changed` carries **BREAKING** on both the `-o` semantics and the `--variations`
default. At 0.x SemVer permits this in a minor bump; the record has to be loud about it anyway,
because `--prompt` was *required* and every existing invocation breaks.

## Risks / Trade-offs

**R1 — retiring a whole capability is untested in this repo.** The living spec goes from five
capabilities to four, and nothing here has removed one before. → **Partly answered at cut time:**
`openspec validate 0008-one-path --strict` is green with `model-registry`'s three requirements all
declared REMOVED, so the *delta* is well-formed. What is still unproven is **archive** time, when
`mf-release` folds the delta and the capability's `spec.md` is left with no requirements. Phase 1
re-runs validate after the directory is actually deleted; if archive later rejects a zeroed
capability, the fallback stands — absorb the one surviving fact into `cli` and keep `model-registry`
as a stub.

**R2 — the prompt edit changes render output, with no GPU in the build to check it.** Removing
`arms crossed` alters what the graph produces. → Phase 8 confirms the path *runs*. No phase confirms
it renders well, and no artifact of this change may claim it does.

**R3 — the spend rule guards real money before it has ever run.** Phase 7 writes it; phase 8 is its
first exercise. → The operator is at the console for phase 8 by design, so the first exercise is
supervised. The phase records what the MCP teardown confirmation actually returned — the only
evidence phase 7 will have before it starts guarding unattended runs. The MCP must be **authorized
from an interactive session before phase 8 begins**; it cannot be authorized non-interactively.

**R4 — phase 8 can fail late.** The change is blocking on a live pod at its final phase: the pod may
not boot, the volume may have been reprovisioned, ComfyUI may OOM across five sequential renders. →
Accepted deliberately, as the price of the version's one claim. `scripts/download_models.sh` is
pruned but not destructive, so a reprovisioned volume is recoverable by running it.

**R5 — deleting the fixtures removes the only copy that could disagree with the shipped graph.** →
See D9. Mitigated in the one place it matters by D7's pinned prompt literal.

**R6 — spec↔test bindings are maintained by hand.** `CLAUDE.md` states there is no binding checker in
this repo. This change removes ~31 scenarios and renames two keys, which is the largest binding churn
so far. → The "every test carries a live `spec()` marker" acceptance row is a **hand review**, and is
recorded as such rather than as a gate that does not exist.

## Migration Plan

There is no deployment; the deliverable is the repository. For a caller upgrading from v0.7.0:

| v0.7 | v0.8 |
|---|---|
| `--prompt "..."` (required) | removed — the prompt is committed to the graph |
| `--model animagine-i2i-cn` | removed — it is the only path |
| `--model qwen` / `animagine` / `animagine-i2i` | no equivalent; the paths are deleted |
| `--workflow other.json` | no equivalent; edit `workflows/pipeline.json` |
| `-o out.png` | **rejected at parse time**; `-o ./outputs` names a directory |
| `--variations` defaults to 1 | defaults to 5, capped at 25 |
| `--seed 42` reproduces render 0 verbatim | every variation's seed is derived; see `run.json` |

`--seed`, `--server`, `--denoise`, `--cfg` and `--ip-weight` are unchanged. Rollback is `git switch
main`; nothing outside the repository is modified except the pod created and destroyed in phase 8.

## Open Questions

None that can be deferred. R1 is a tooling unknown with a decided fallback, not an open question, and
phase 1 answers it.
