---
version: v0.22.1
---

## Why

**Ten releases of converge left a backlog nobody trusted.** It held ~95 rows across sixteen sections, and
when every row was re-resolved against `main` at `bb01f79`, **thirty of them were already dead** — six
because v0.22 deleted the file they named, nineteen because the defect had been fixed in a commit and the
row was never deleted, five because they live inside an archived change this repository refuses to edit.
The backlog's own bookkeeping section put the already-fixed count at eight, and two of the entries it
listed as closed are live.

**Eighteen rows are worth paying and they fit one version.** They are not a theme; they are what the
selection rule left standing — *everything that can lose work, spend money, or make the record lie*. Four
of them can do the first two:

- **A closed tunnel is recorded `permanent`**, and `check_budget` then refuses that stage forever. The
  operator's fix is deleting an error record by hand.
- **One malformed sheet aborts every sibling flow** in the invocation, and has already written a permanent
  record poisoning its own flow for every later run.
- **A manifest missing a dial passes all six gate commands, rents the pod, uploads the photograph**, and
  then raises a bare `KeyError` — not a `Refusal`, so no failure record is written and the rest of the
  batch dies with it.
- **One unreadable photograph kills a whole batch**, because `image_dimensions()` exits and `across()`
  catches only `Refusal`. The fix already exists one module away: `generate.py:240-262` wraps the same call
  in `except SystemExit`, with a comment explaining exactly this hazard, while `batch.py:51-54` *documents*
  it instead of closing it.

**This is a patch release: no new capability, no new CLI surface, and no spec delta.** The flow
directories are untouched, so `manifest_digest` does not move and `PINNED` holds. `v0.22.2` is already
scheduled for the openspec prose and the living `docs/`, and every documentation row — the ten false
self-claims, the stale docstrings, the archived-change errata — was deliberately cut out of this version
and left to it, so behaviour and the sentence describing it land together rather than half here.

## What changes

**Eighteen entries, twenty ids, six phases.** The full disposition, with the evidence behind every
deletion and every carry, was produced at two grillings before this change was cut.

1. **The middleware.** No `Host`/`Origin` validation on the unauthenticated loopback API —
   `grep add_middleware\|Origin\|TrustedHost isekai/` returns zero hits. **Raised independently by four
   converge security stations across v0.18, v0.20, v0.21 and v0.22.** It goes first because it changes the
   request path for all seven routes, and four later UI fixes are tested through them.
2. **Failure records.** A transport failure stops being `permanent`; one flow's malformed sheet stops
   aborting its siblings.
3. **Refusal strings.** Two refusals print a pre-v0.16 path order at a directory that does not exist, and
   two name commands without the `--flow` v0.16 made required — so **copy-pasting the remedy a refusal
   states returns an argparse error instead of the fix.**
4. **Load-time validation.** `load_flow` validates the four node roles and validates no dial, and resolves
   no node id against the graph.
5. **The UI server.** Nine entries: the rail and the form disagreeing about approval, overlapping `PUT`s
   committing out of order, a batch killed by one bad JPEG, a stale bundle after a dependency change, a
   dead guard, an unbounded `npm` subprocess, duplicate Vue keys, `show` bypassing its injected seam, and
   `Cmd+Z` dead under a Cyrillic layout.
6. **The local arm.** `num_ctx` unpinned in both option maps, a test that fails on any machine exporting
   `no_proxy`, and a dead public function.

**One row left the version at the cut-grilling and is not here.** `v0.19 security/S1` — photograph bytes
crossing plaintext loopback with no check the listener is Ollama — is closed as a **decision rather than a
fix**: its own threat model says the attacker is already running as the operator, at which point they can
answer a `/api/version` probe too, so the probe detects an accident and not an attack, and an accident
already surfaces as a refusal within one call.

## Impact

**The flow definitions are untouched and stage ④ is unchanged.** No graph, dial, schema or briefing is
edited; `manifest_digest` does not move.

> ⚠️ **One entry can change what the models produce, and it is the reason phase 6 carries a stop.**
> `num_ctx` is unset today, so the effective context window is whatever Ollama resolves from the GGUF and
> the host. **Pinning it changes the reader's and tagger's output unless the pinned value equals the
> current effective one** — and if the window is currently *smaller* than the prompt, captions are being
> truncated right now and pinning higher changes them for the better. Either direction is a change:
> captions feed sheets and sheets feed renders. **Phase 6 measures `prompt_eval_count` first and
> byte-compares a re-captioned artifact before the pin lands. If the caption moves, the pin is wrong and
> the phase halts.**

**Three behaviour changes reach the operator directly.** A draft update against an approved input is
refused where it currently succeeds; an overlapping `PUT` can answer `409` where the client has never seen
one; and the hosted tag panel shows each tag once.

**Metered cost is zero.** No pod, no `generate`, no `infra/up.sh` in any phase. The acceptance is the gate
plus one local pass through stages ①②③ on a fresh photograph — the arm is Ollama and WD14 on the
operator's own machine, and the pod is needed only for ④. The two rows that cannot be reached locally are
failure paths, and their acceptance is a test that forces the failure rather than a metered sitting.

**No spec delta.** Four entries bind to existing scenarios whose `THEN` is false today; three are
dead-code deletions needing no test; the remaining eleven carry `spec_exempt` with a reason naming
`v0.22.2`. **That borrows the marker past its documented meaning for one version** — see `design.md` D2,
where the cost is stated rather than left for a reviewer to find.
