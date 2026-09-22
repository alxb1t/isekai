# Design — 0023 backlog paydown

**Verdict: `feasible`.** Every decision below was settled against a body read at `main` `bb01f79`, after
`v0.22.0` was tagged and `0022-one-arm` archived. Two grillings preceded this change: one decided *which*
rows to pay, one decided *how*. **Three premises the second grilling opened with were overturned by
evidence**, and each overturn is recorded at the decision it replaces.

## Context

The backlog held ~95 rows exported from ten converge passes, v0.13 through v0.22. Every row was
re-resolved against the working tree before this change was cut; eighty-two were verified line by line.
**Thirty were already dead.** What is left is eighteen entries carrying twenty ids.

The selection rule is *blast radius* — a row is in scope if it can lose work, spend money, or make the
record lie. Documentation is out **entirely**, including the ten false self-claims the repository makes
about itself, because `v0.22.2` is scheduled for the openspec prose and the living `docs/` and a docs pass
rewrites most of those files anyway.

---

## D1 — Phases decompose by defect group, not by file

Six phases, each *one thing*, which is this repository's own phase rule. By-file decomposition was
considered and refused: it splits `v0.16 review/R4` and `R5` — one edit to one refusal vocabulary — across
two phases, while `pipeline/generate.py` alone carries three unrelated defects that would land in one.

**Line numbers throughout were resolved against `bb01f79`.** Phase 1 moves some of them; re-resolve by
symbol name rather than trusting a number from an earlier phase.

## D2 — No spec delta, and the marker cost is stated here rather than discovered

**This change adds no scenario and no requirement.** `v0.22.2` owns the openspec prose, so behaviour and
the scenario describing it land together there rather than half here.

`CLAUDE.md:115-119` requires every test to carry `@pytest.mark.spec("<key>")` or
`@pytest.mark.spec_exempt("<reason>")`. Against the living specs:

| | count | |
|---|---|---|
| **bind to an existing scenario whose `THEN` is false today** | 4 | real coverage — the fix makes an already-written assertion true |
| **need no test** | 3 | two dead-code deletions and one test-only fix that keeps its marker |
| **carry `spec_exempt` naming `v0.22.2`** | 11 | behaviour with no scenario to bind to |

> ⚠️ **The eleven borrow `spec_exempt` past its documented meaning.** That marker means *genuinely
> structural*, and most of these are behaviour. It is borrowed deliberately, for one version, because the
> alternative options are worse: an unmarked test hides the debt behind a gap the repository already knows
> about (`CLAUDE.md:176-179` — there is no binding checker), and a third marker is new tooling in a patch
> release. **The reason string must name `0024` so the debt is greppable**: `grep spec_exempt tests/ | grep
> 0024` is the worklist `v0.22.2` opens with.

The four real bindings:

| entry | scenario | why it is false today |
|---|---|---|
| `v0.18 review/R7` | `ui:startup:refusals-are-reported-together` | with two unreadable photographs, **neither** is named — `sys.exit` escapes `across` |
| `v0.16 review/R5` | `image-generation:inputs:unapproved-flow-is-refused` | *"the message names the commands that would produce one"* — both printed commands are refused by the parser |
| `v0.16 review/R8` *(dials half)* | `image-generation:manifest:invalid-manifest-names-the-field` | a manifest with an empty `dials` block loads clean |
| `v0.18 review/R6` | `ui:approval:approved-input-refuses-a-draft-update` | the `PUT` succeeds in the re-opened state — see D5 |

## D3 — The middleware goes first

`v0.18 security/S1` is the only entry that changes the request path for **all seven routes**, and
`v0.18 review/R6`, `R10` and `R11` are all tested through those routes. Landing it first means no UI test
ever runs against a request path that differs from what ships.

The counter-argument — that a cross-cutting change landing first can mask or mimic the failures the other
fixes are meant to show — was weighed and rejected: that is the risk of a *wrong* middleware, which the
phase's own gate catches immediately.

**Splitting it into a change of its own was refused.** v0.22's security station recommended exactly that
in writing, and splitting it out is how it stayed unfixed across four versions while four independent
stations re-raised it.

> The surface also grew without anyone noticing: it is **seven** routes, not the six the module docstring
> claims at `app.py:1` and `:25`. `GET /api/fields` arrived at v0.21. **The docstring's numeral is prose
> and is not corrected here** — it belongs to `v0.22.2`'s sweep.

## D4 — Dial validation is role-conditional, and a flat check would reject a tracked flow

> **Overturned premise ①.** The cut-grilling opened on the worry that validating dials and node ids would
> make a tracked flow fail its own new check — and a flow file cannot be edited, because
> `manifest_digest` covers every byte in the directory and `tests/test_flow.py`'s `PINNED` fails the gate
> naming the flow. **Checked literally, neither flow fails either check in either direction:**
>
> ```
> summon-anime-wai    nodes 11/11 resolve in graph.json    dials 12/12 consumed
> conjure-anime-wai   nodes  7/7  resolve in graph.json    dials  9/9  consumed
> ```
>
> The digest hazard does not fire, and the change touches `foundation/flow.py` only — outside every flow
> directory.

**What survives the overturn is a constraint on the implementation's shape.** A flat *"every dial in a
fixed list is present"* check **rejects `conjure-anime-wai`**, which legitimately declares no `ip_weight`,
no `identity_cn_strength`, no `openpose_strength` and no `identity` or `openpose` role. The validation
must be **role-conditional**, mirroring `patch()`'s own guards at `generate.py:315-346` — and
`_hires_target` reads `hires_scale` unconditionally whenever `hires_resize` is declared, so the role→dial
mapping has to be encoded rather than inferred.

## D5 — `ui` and `review` contradict each other, and the `ui` side is already false

> **Overturned premise ②, and it reversed the recommendation this change was nearly cut with.**

The grilling opened proposing a new **re-opened** rail status, on the reading that the rail
(`approved_path is not None`) and the form (`draft is None`) each held one of two true facts and the
disagreement was a missing third state. The living specs say otherwise:

```
ui/spec.md      "SHALL ... refuse a draft update against [an approved] input"
review/spec.md  "reviewing again appends a new numbered draft from the approved one"
                 └── both live, and they cannot both hold
```

`ui:approval:approved-input-refuses-a-draft-update`'s `WHEN` carries **no `and no draft` guard** — its
sibling scenario does. So it matches the state `review --flow F --new-version` produces. And in code,
`save_draft` refuses on *no draft* and never on *approved*, while `put_draft` has **no approval gate at
all**. **The `PUT` already succeeds in that state today; the scenario is already false.**

**Decision: `approved_path` becomes authoritative and `put_draft` gains an approval gate.** That makes an
already-false scenario true, which is a bug fix rather than new behaviour — and is therefore the only
version of this fix that can ship under D2.

**The re-opened state goes to `v0.22.2`**, where it can carry the requirement-prose edit and the `WHEN`
guard it needs. **Which capability is right — `ui` or `review` — is a design question, not a defect**, and
it is that version's to answer.

> ⚠️ **A hazard to record for whoever answers it.** Adding a third rail status splits
> `/api/batch["approved"]`, which `read_batch` derives from the status *string*, from
> `Batch.approved_count`, which reads the directory. `ui:batch:approved-count-comes-from-disk` is the
> scenario that would catch the divergence.

## D6 — The draft precondition is mtime, because nothing else exists on disk

`v0.18 review/R10`'s fix needs something to compare against. There is nothing: the draft carries no
timestamp, no revision counter and no digest. `schema.version` is the constant `1` — an artifact *format*
version — and `save_draft` never advances the filename's `NNN`, by design ("the version and the sheet the
draft records are its identity").

**The only monotonic fact is `st_mtime`, and it is already on the wire** as the payload's `saved` field.
So the client echoes the `saved` it last received, the server compares, and a mismatch answers `409`.

Rejected: a `revision` int in the draft body is the correct answer and changes the artifact shape, which
`read_artifact` refuses for any unknown schema — it touches every reader in the package, which is not a
patch. A lock around `save_draft` does not fix it: out-of-order *sends* still commit out of order.

**Client-side, a generation counter drops a stale response**, and the pattern already exists in this
codebase at `ui/src/composables/useVocabulary.ts:32-57`.

## D7 — Dedup the hosted tag list only

`v0.20 review/R5`'s backlog entry warned that deduplicating in `_tags()` is *"a narrowing decision and must
not be taken silently."* Checked against the spec: `tagging:output:the-list-is-stored-unnarrowed`'s
`SHALL NOT`s are **canonicalising, filtering against a vocabulary, and re-ordering**. Deduplication is
named in two docstrings and in no scenario, and the artifact on disk — which is what the requirement
protects — is untouched either way. `OfferedTag` is `{tag, posts}` where `posts` is a pure function of
`tag`, so **a duplicate is a byte-identical object carrying no information.**

> ⚠️ **`_wd14` must not be deduped.** `ScoredTag` is `{tag, confidence}`, where two rows could legitimately
> differ, the local list is unfiltered by design, and deduping it would falsify
> `ui:source:both-tag-lists-are-shown-raw-and-read-only`'s first `THEN` — *"every tag the local tagger
> scored is present in the response."*

## D8 — `num_ctx` is measured before it is pinned, and phase 6 halts if the caption moves

> **Overturned premise ③.** `v0.19 review/R4` was written against `SORTER_OPTIONS` at `sheet.py:153`,
> citing *"a 7,440-byte briefing."* That constant was deleted with the sorter and `sheet.py` has no
> transport at all. Measured at `bb01f79`:
>
> | | bytes | ≈ tokens |
> |---|---|---|
> | reader briefing — both flows, byte-identical | 2,185 | ~546 |
> | tagger prompt | 48 | ~12 |
> | `num_predict`, drawn from the same window | — | 1024 |
> | **the photograph, base64, in the same request body** | median 1.5 MB, max 21 MB | **unknown** |
>
> **The text is negligible and the finding's own number was wrong by 3.4×.** The whole question is whether
> image tokens consume `num_ctx`, and the repository records nothing — `num_ctx`, `OLLAMA_CONTEXT_LENGTH`
> and *context window* return zero hits across source, tests, specs, the archive and `CHANGELOG`. The
> Modelfile sets no `PARAMETER` at all.

**This is the one entry that can change what the models produce**, and therefore the one thing in this
change that could move a render. `num_ctx` is unset, so the effective window is whatever Ollama resolves;
pinning it changes output unless the pinned value equals the current effective one, and if the window is
currently smaller than the prompt then captions are being truncated now and pinning higher changes them
for the better. Either direction is a change, and captions feed sheets which feed renders.

**So the phase measures first.** Read `prompt_eval_count` off a real local call, pin at or above the
measured effective window, then **re-caption an existing input and byte-compare the artifact.** *If the
caption moves, the pin is wrong and the phase halts* — it does not get argued away in a commit message.

## D9 — `v0.19 security/S1` is closed as a decision, not carried as a fix

The boundary speaks exactly one path, `POST /api/generate`. There is no `GET` anywhere and no liveness
probe, so "check the listener is Ollama" means adding an endpoint the code has never called.

**Refused.** S1's own threat model states the attacker is *already running as the operator* — at which
point they can answer `/api/version` as easily as `/api/generate`. A probe therefore detects an
**accident**, not an attack; and an accident already surfaces within one call, as either the *nothing is
listening* refusal or the `404` that proves the listener knows about models.

The row moves to the operator's backlog as trigger-gated. **The `CLAUDE.md` sentence recording this
posture is prose and travels with `v0.22.2`** — without it, a fifth security station will raise this for a
fifth time.

## D10 — `v0.16 review/R5` is systemic, and the backlog row understates it

The row names `generate.py:213-214`. But `refusal_for` at `run.py:569-590` emits
`` "run `python -m isekai {verb}` again" `` for **every caption and tagging budget refusal** as well.

**Fixing only the two `generate.py` sites leaves `image-generation:inputs:unapproved-flow-is-refused`
still false**, and leaves `cli:refusals:refusal-names-the-remedy` — *"that action is available in this
build"* — false too. The existing test passes only because `tests/test_resume.py:340-360` lists the bare
command strings without the flag, so the scenario text is stronger than the test bound to it.

**Phase 3 threads the flow through `refusal_for` as its own argument** rather than patching call sites,
and updates that fixture.

## D11 — `transient` classifies the failure; rendering's budget stays one

> **Settled at converge, not at the cut.** Round 1's review (`R1`) found that nothing covered the budget
> arithmetic behind `v0.13 review/R7`, and it was right: no decision here reached it.

`render()` now records `"transient"` for an `Unreachable`, which lifts `check_budget`'s permanent
short-circuit. **It does not let the next pass through**, because that function refuses on either of two
conditions and the second does not read `kind`: `BUDGETS["render"]` is `1`, so one record of any kind is
already at budget. The operator's remedy after a closed tunnel is still deleting the record by hand.

**That is kept, and the two ways out of it were both refused.**

- *Count only non-`transient` records against the budget.* The living spec says the opposite in the
  requirement itself — `run-directory`'s *"SHALL refuse a stage whose **transient** attempts have reached
  its budget"* — so an unbounded transient retry is not a reading of it.
- *Give `render` a budget above one.* That falsifies the same requirement's stated reason — *"A render
  that has failed once should cost a person's attention rather than another attempt, which is why that
  stage's budget is one"* — and `tests/test_run_directory.py`'s `test_the_rendering_stages_budget_is_one`
  pins the number against that scenario. **It is also a spending decision**: rendering is the one stage
  that costs money on every pass, and doubling what a resume may spend without a person is not a patch
  release's call, let alone a fix station's. It needs a spec delta, which D2 says this change does not
  have.

**What the reclassification does buy** is the kind in the filename — `run-directory:failure:kind-and-
attempt-are-in-the-filename` exists so the operator can read *why* from a directory listing — the refusal
sentence that matches what happened, and a classification that is correct for every stage whose budget is
not one. That is the *record lying*, the third clause of this change's selection rule, and it is the
clause the row is in scope under.

> ⚠️ **`proposal.md`'s Why overstates this row.** *"`check_budget` then refuses that stage forever"* was
> never true — deleting the record clears the permanent short-circuit exactly as it clears the count — and
> *"the operator's fix is deleting an error record by hand"* is the remedy **after** this change as well
> as before it. The `CHANGELOG` entry is rewritten to say so; the proposal is left as the statement of why
> the change was cut, and this is where the correction is recorded.

`tests/test_generate.py::test_a_transient_render_record_still_refuses_the_next_attempt_on_the_count` makes
the arithmetic visible to the suite, which is what let R1 be found by reading rather than by an operator
losing a pod session to it.

---

## Open questions

**None blocking.** Two are recorded for `v0.22.2` rather than answered here:

1. **Which capability is right, `ui` or `review`?** D5 closes the contradiction in `ui`'s favour because
   that is the fix that needs no spec delta. Whether an approved input *should* be re-openable is a design
   question.
2. **`openspec/specs/ui/spec.md` has no `Source:` and no `Tests:` line** — the only one of twelve without
   them. Nine of this change's eighteen entries live in modules it would name. It belongs in that version's
   sweep.
