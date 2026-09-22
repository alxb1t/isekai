# Tasks — 0023 backlog paydown

## Progress

- [x] 1 — The middleware: `Host`/`Origin` on all seven routes
- [x] 2 — Failure records: a transport failure is transient, a bad sheet spares its siblings
- [x] 3 — Refusal strings: the path order, and the flag the remedy omits
- [ ] 4 — Load-time validation: the dials and the node ids
- [ ] 5 — The UI server: nine entries
- [ ] 6 — The local arm: measure, then pin
- [ ] 7 — The acceptance: gate green and one local pass, no pod

## The per-phase ritual

1. **Run each sub-task's stated verification — run it, never summarize it. Paste real output.**
2. **Gate green before the commit** — `make gate`, the commands in `.minions/minions.toml`'s `gate` array,
   in order. **Never weaken the gate to pass**; halt and say so.
3. A `CHANGELOG.md` entry under `## [Unreleased]`, appended in that phase's own commit.
4. The phase's box ticked in `## Progress` above, in that phase's own commit.
5. **One commit per phase**, staged **by name**, carrying `Change: 0023-backlog-paydown` contiguous with
   the `Co-Authored-By:` line.
6. **Every new test carries a binding** — see the table below. **This change adds no scenario**, so a test
   either binds to a scenario named there or carries
   `@pytest.mark.spec_exempt("behaviour; the scenario lands in 0024")`. **The `0024` is load-bearing**:
   `grep spec_exempt tests/ | grep 0024` is the worklist the next version opens with (`design.md` D2).

**`design.md` is authoritative.** Where the tree disagrees with a decision it settled, that is a halt and
a finding, never a quiet divergence.

**Line numbers below were resolved against `main` `bb01f79`.** Phase 1 moves some of them; re-resolve by
symbol name rather than trusting a number from an earlier phase.

**⛔ Metered cost is ZERO in every phase.** No pod, no `generate`, no `infra/up.sh`. A pod in any of them
is a halt.

### The bindings, once, for the whole change

| entry | marker |
|---|---|
| `v0.18 review/R7` | `spec("ui:startup:refusals-are-reported-together")` |
| `v0.16 review/R5` | `spec("image-generation:inputs:unapproved-flow-is-refused")` |
| `v0.16 review/R8` *(dials half)* | `spec("image-generation:manifest:invalid-manifest-names-the-field")` |
| `v0.18 review/R6` | `spec("ui:approval:approved-input-refuses-a-draft-update")` |
| `v0.18 review/R11`, `v0.15 review/R7` | no test — dead-code deletion, no behaviour change |
| `v0.19 review/R7` | keeps its existing `spec_exempt` |
| **everything else** | `spec_exempt("behaviour; the scenario lands in 0024")` |

---

## 1 — The middleware: `Host`/`Origin` on all seven routes

**First, so every later UI phase is tested behind the request path that ships** (`design.md` D3).

- [x] 1.1 **Add host validation to `create_app()`** — `isekai/interface/ui/app.py:62`. Today
  `grep -rn "add_middleware\|Origin\|TrustedHost" isekai/` exits 1 with **zero hits**. Reject a request
  whose `Host` is not the loopback address the server bound, and whose `Origin`, when present, does not
  match it. **Verify:** paste that grep before and after.

- [x] 1.2 **A test per direction** — a request with the bound `Host` succeeds; one with an attacker's
  `Host` is refused; one with a mismatched `Origin` is refused. Marker:
  `spec_exempt("behaviour; the scenario lands in 0024")`.

- [x] 1.3 **Verify the count is seven, not six** —
  `grep -c '@app\.\(get\|put\|post\)' isekai/interface/ui/app.py`. ⚠️ **Do not correct the module
  docstring's "six" at `:1` and `:25`.** That is prose and belongs to `v0.22.2`; correcting it here
  widens a patch into the version that was cut to avoid exactly that.

- [x] 1.4 **Gate green. CHANGELOG. Tick 1. Commit.**

---

## 2 — Failure records: a transport failure is transient, a bad sheet spares its siblings

- [x] 2.1 **`v0.13 review/R7` — a closed tunnel stops being `permanent`.** `pipeline/generate.py:418-423`
  calls `record_failure(..., "permanent", ...)` unconditionally, while `_reported()`
  (`interface/cli.py:557-566`) turns `URLError`/`OSError` into that same `Refusal`. `check_budget`
  (`run.py:527`) then short-circuits forever. **Fix:** raise a distinct type from `_reported()` and branch
  on it at the `record_failure` call. **Verify:** a test forcing a `URLError` through the transport and
  asserting the record's kind is `transient`.

- [x] 2.2 **`v0.16 review/R6` — one malformed sheet stops aborting its siblings.**
  `pipeline/generate.py:216-218` assembles in a dict comprehension, and `prompt_artifact`'s failure path
  at `:172-176` has already written a **permanent** record before raising at `:178`. **Fix:** collect
  per-flow refusals the way `across` does per photograph. **Verify:** two flows, one malformed sheet —
  assert the good flow is assembled and that the bad flow's record does not poison a later run.

- [x] 2.3 **Gate green. CHANGELOG. Tick 2. Commit.**

---

## 3 — Refusal strings: the path order, and the flag the remedy omits

> ⚠️ **`R5` is systemic and its backlog row understates it** (`design.md` D10). `refusal_for` at
> `run.py:569-590` emits `` "run `python -m isekai {verb}` again" `` for **every caption and tagging
> budget refusal** too. Fixing only the two `generate.py` sites leaves the bound scenario still false.

- [x] 3.1 **`v0.16 review/R4` — the path order.** `pipeline/generate.py:180` prints
  `{PROMPTS}/{flow.id}/` against a real layout of `{flow.id}/{PROMPTS}/` (`generate.py:158`).
  `review.py:319` already has it right — match it.

- [x] 3.2 **`v0.16 review/R5` — thread the flow into `refusal_for` as its own argument**, rather than
  patching call sites. Covers `generate.py:213-214` **and** every `run.py:569-590` caller. **Verify:**
  extract every `python -m isekai` string the suite produces and assert each carries `--flow`.

- [x] 3.3 **Update `tests/test_resume.py:340-360`'s `AVAILABLE` list.** It currently holds the bare
  command strings without the flag, which is the only reason
  `cli:refusals:refusal-names-the-remedy` passes today.

- [x] 3.4 **Gate green. CHANGELOG. Tick 3. Commit.**

---

## 4 — Load-time validation: the dials and the node ids

**`v0.16 review/R8` + `v0.17 review/R6`.** Today a manifest missing `steps`, or naming a node id absent
from `graph.json`, passes all six gate commands, **rents the pod, uploads the photograph**, then raises a
bare `KeyError` from `patch()` — not a `Refusal`, so `across` does not collect it and no failure record is
written.

> ⚠️ **Role-conditional, never a flat list** (`design.md` D4). A flat *"every dial in a fixed list is
> present"* check **rejects `conjure-anime-wai`**, which legitimately declares no `ip_weight` and no
> `identity` role. Mirror `patch()`'s own guards at `generate.py:315-346`, and note `_hires_target` reads
> `hires_scale` unconditionally whenever `hires_resize` is declared.

- [ ] 4.1 **Validate at load that every node id resolves in the graph** — `foundation/flow.py:385-391`.

- [ ] 4.2 **Validate at load that every dial the declared roles require is present.**

- [ ] 4.3 **One test iterating `tracked_flows()`** asserting every value of `flow.nodes` is a key of
  `flow.graph()`. **Verify first that both tracked flows pass unchanged** — `summon-anime-wai` 11/11 and
  12/12, `conjure-anime-wai` 7/7 and 9/9. **If either fails, halt**: a flow file cannot be edited without
  moving `manifest_digest`, and that is a different change.

- [ ] 4.4 **Confirm `manifest_digest` has not moved** — `uv run pytest -k test_every_tracked_flow_matches`.

- [ ] 4.5 **Gate green. CHANGELOG. Tick 4. Commit.**

---

## 5 — The UI server: nine entries

- [ ] 5.1 **`v0.18 review/R6` — `approved_path` becomes authoritative, and `put_draft` gains an approval
  gate.** `app.py:244` keys the rail on `approved_path`; `:182` keys the form on `draft is None`. **Read
  `design.md` D5 before writing this**: `ui/spec.md` and `review/spec.md` contradict each other and the
  `ui` side is already false in code, because `put_draft` has no approval gate at all. This makes an
  already-false scenario true. Marker:
  `spec("ui:approval:approved-input-refuses-a-draft-update")`. ⛔ **Do not add a third rail status** —
  the re-opened state is `v0.22.2`'s.

- [ ] 5.2 **`v0.18 review/R10` — an mtime precondition and a `409`.** `app.py:198-217` ·
  `review.py:180-204`. The client echoes the `saved` it last received; the server compares to
  `path.stat().st_mtime` and refuses on mismatch (`design.md` D6).

- [ ] 5.3 **A generation counter in `ui/src/composables/useSheet.ts`**, so a stale response is dropped.
  **The pattern already exists** at `useVocabulary.ts:32-57` — copy it rather than inventing one.

- [ ] 5.4 **`v0.18 review/R7` — one unreadable photograph stops killing the batch.** `batch.py:182` calls
  `image_dimensions()` unguarded; it exits via `sys.exit` (`shared/image.py:277,279,285,288`) and `across`
  catches only `Refusal`. **The fix already exists one module away** — `generate.py:240-262` wraps the same
  call in `except SystemExit`. Marker: `spec("ui:startup:refusals-are-reported-together")`; **the test
  needs two unreadable photographs**, since the scenario asserts *every* one is named.

- [ ] 5.5 **`v0.18 review/R11` — delete the dead guard.** `app.py:98`'s
  `if (posts := batch.vocabulary.count(tag)) is not None` never drops a row; `count()` is `-> int`. No
  test — no behaviour change.

- [ ] 5.6 **`v0.18 review/R9`′ — a `timeout=` on the `npm run build` subprocess.** `bundle.py:101-103`.

- [ ] 5.7 **`v0.20 review/R5` — dedupe `_tags()`.** `app.py:265-304`. ⚠️ **Hosted side only**
  (`design.md` D7). Deduping `_wd14` would falsify
  `ui:source:both-tag-lists-are-shown-raw-and-read-only`'s first `THEN`.

- [ ] 5.8 **`v0.20 review/R6` + `security/S2` — `_is_fresh` watches the build config.**
  `bundle.py:66-70` compares only `ui/src/` and `ui/index.html`; add `vite.config.ts`, `package.json` and
  `package-lock.json`. **Verify:** touch `package.json`, start the server, assert a rebuild.

- [ ] 5.9 **`v0.16 review/R2` — `run_view` honours the injected seam.** `run_view.py:136` calls
  `load_flow` with the default `FLOWS_DIR`, ignoring `Wiring.flows_dir` (`wiring.py:86`), over an
  unfiltered `iterdir()`; and `report` is a generator, so the refusal lands after fifteen lines have
  streamed. Fix both halves — the seam **and** the mid-stream refusal.

- [ ] 5.10 **`v0.21 B1` — `Cmd+Z` matches `event.code`.** `ui/src/ReviewApp.vue:301`. **The same handler
  already argues for `event.code` thirteen lines earlier** at `:285-288`; `:291` and `:296` already use
  it. ⛔ **This binding only** — the keyboard re-work is its own version, and `TagInput.vue:59`'s thirteen
  `event.key` branches are not this change's.

- [ ] 5.11 **Gate green. CHANGELOG. Tick 5. Commit.**

---

## 6 — The local arm: measure, then pin

> ⛔ **This phase can change what the models produce, and it is the only one in this change that can.**
> Read `design.md` D8. `v0.19 review/R4`'s own figure — *"a 7,440-byte briefing"* — was measured against a
> constant that no longer exists and is wrong by 3.4×; the real briefing is 2,185 bytes ≈ 546 tokens, and
> the open question is entirely whether the base64 photograph in the same request body consumes `num_ctx`.

- [ ] 6.1 **Measure before pinning.** One local `caption` call on a real photograph; read
  `prompt_eval_count` off the response and record it in the task list. **This is a number nobody in this
  repository has.**

- [ ] 6.2 **Pin `num_ctx` at or above the measured effective window** in `READER_OPTIONS`
  (`caption.py:64-68`) and `TAGGER_OPTIONS` (`tagging.py:87-92`), **with the measurement in the comment** —
  this file's convention is that a pinned value carries the measurement it came from.

- [ ] 6.3 ⛔ **HALT CHECK — re-caption an existing input and byte-compare the artifact.** If the caption
  moved, **the pin is wrong and this phase stops**. Do not argue it away in a commit message; record the
  measurement and hand it back. A moved caption moves the sheet, and the sheet moves the render.

- [ ] 6.4 **`v0.19 review/R7` — clear `no_proxy` in the falsification twin.** `tests/test_ollama.py:82-96`
  sets `http_proxy`/`https_proxy` and never clears `no_proxy`, so the assertion is true only in a clean
  environment. **Keeps its existing `spec_exempt` marker.**

- [ ] 6.5 **`v0.15 review/R7` — delete `load_records`.** `evaluation/labels.py:317-319`; the definition
  line is its only reference repo-wide. **Verify:** `grep -rn "load_records" isekai/ tests/ scripts/`
  returns nothing after.

- [ ] 6.6 **Gate green. CHANGELOG. Tick 6. Commit.**

---

## 7 — The acceptance: gate green and one local pass, no pod

**This version adds no capability and changes no generated image, so *"the gate is green"* is what the
gate says on any day and cannot be the acceptance on its own.**

- [ ] 7.1 **`make gate` — all six commands, output pasted.**

- [ ] 7.2 **One local pass through ①②③ on a fresh photograph, no render.** Ollama and WD14 run on this
  machine; the pod is needed only for ④. Confirm: the caption is written, both tag lists are written, the
  sheet is filled, the review surface serves it, a draft saves and the receipt returns.

- [ ] 7.3 **Confirm the three operator-visible behaviour changes**, each by hand:
  a draft update against an approved input is refused · an overlapping `PUT` answers `409` ·
  the hosted tag panel shows each tag once.

- [ ] 7.4 **Confirm `Cmd+Z` under a Cyrillic layout**, which is the defect's whole subject.

- [ ] 7.5 **`/simplify` over this change's own diff**, as every change in this repository closes.

- [ ] 7.6 **Record what was NOT verified**: stage ④ was not run, so no render was produced and no pod was
  rented. **That is the design, not a gap** — the flow directories are untouched and `manifest_digest`
  did not move.

- [ ] 7.7 **Gate green. CHANGELOG. Tick 7. Commit.**
