# Tasks — 0024 the documents

## Progress

- [x] 1 — The sweep: what this repository says about itself
- [x] 2 — `docs/arc/`: the module graph and the data flow
- [x] 3 — `CLAUDE.md`: cut to agent operating instructions
- [x] 4 — The spec catches up with the code, and the one code change
- [x] 5 — Seventeen scenarios
- [x] 6 — Rebind the seventeen tests
- [ ] 7 — The acceptance

## The per-phase ritual

1. **Run each sub-task's stated verification — run it, never summarize it. Paste real output.**
2. **Gate green before the commit** — `make gate`, the commands in `.minions/minions.toml`'s `gate` array,
   in order. **Never weaken the gate to pass**; halt and say so.
3. A `CHANGELOG.md` entry under `## [Unreleased]`, appended in that phase's own commit.
4. The phase's box ticked in `## Progress` above, in that phase's own commit.
5. **One commit per phase**, staged **by name**, carrying `Change: 0024-the-documents` contiguous with the
   `Co-Authored-By:` line.
6. **Every new test carries a binding** — `@pytest.mark.spec("<key>")` naming the scenario it proves.
   ⛔ **No test in this change may carry `spec_exempt` naming `0024`.** That marker is what this change
   exists to repay; adding one would be the debt refinancing itself.

**`design.md` is authoritative.** Where the tree disagrees with a decision it settled, that is a halt and
a finding, never a quiet divergence.

**Line numbers below were resolved against `main` `b4abe12`, after `v0.22.1` merged.** Phase 1 moves many
of them; re-resolve by symbol or by quoted text rather than trusting a number from an earlier phase.

**⛔ Metered cost is ZERO in every phase.** No pod, no `generate`, no `infra/up.sh`. A pod in any of them
is a halt. No flow file is edited in any phase — `manifest_digest` must not move.

> ⚠️ **HAND THIS TO `mf-release` BEFORE IT FOLDS.** This change carries **nineteen new scenarios and one
> MODIFIED requirement** across four capabilities — seventeen in `ADDED` blocks, two more inside the
> `MODIFIED` one. `openspec archive` cannot run end-to-end on this
> repository, so the fold is done by hand. The `MODIFIED` block in `specs/ui/spec.md` **renames its
> requirement heading** — *"An approved input is read-only on the surface"* becomes *"…until it is
> re-opened"* — so a title-matching fold finds nothing and appends, which is exactly the failure
> `v0.14 review/R11` recorded. **Match on the old title; replace, do not append.**

---

## 1 — The sweep: what this repository says about itself

**Every fix in this phase changes a claim, never code** (`design.md` D6). If a claim would be truer with a
code change, that is a backlog row, not a task here.

- [x] 1.1 **The ten false self-claims.** Each verified false at `b4abe12`:

  | at | says | truth |
  |---|---|---|
  | `README.md:78` | a flow is *"two tracked files"* | **four** — `git ls-files flows/summon-anime-wai` |
  | `isekai/README.md:46-48` | *"five files … with a falsification twin each"* | **six constants across four files**, and **one** falsification test. `tests/test_package_paths.py:3` and `:95` already say so |
  | `isekai/README.md:27-29`, `:37` | the `provision` edge is eager | **both** imports are function-local in `load()` — `shared/vocabulary.py:126`, `:127` |
  | `isekai/boundary/README.md:3-4` | nothing outside opens a socket or spawns a binary | **three** — `labels.py:107` `git`, `bundle.py:131` `npm`, `app.py:463` binds a port |
  | `isekai/pipeline/sheet.py:23`, `:30` | *"the sixteen fields"*, *"six of the sixteen"* | true of `summon-anime-wai`; `conjure-anime-wai` declares **21**. *"which seven are scored"* is right for both |
  | `isekai/evaluation/evaluate.py:19-21` | *"the one-path rule"* | `CLAUDE.md:18-25` records that rule as **replaced** |
  | `scripts/manifest.py:29-31` | *"`convert.py`'s import graph"* | no `convert.py` exists |
  | `scripts/derive_manifest.py:257-258` | *"the SHA-256 **and byte count**"* | signature is `-> str`; `:280` returns the digest alone |
  | `tests/test_flow.py:469`, `:376` | *"the tracked flow"* singular | two tracked flows; the fixture is parametrized. `:683` is already plural |
  | `CHANGELOG.md:1968`, `:1976`, `:1983` | — | 153 / 136 / 138 chars against a ~100 wrap. **Byte-unchanged since v0.15; they only moved** |

  ⛔ **Do not touch `isekai/boundary/multipart.py:8`.** Its hardcoded boundary still names the module
  v0.14 deleted, and the backlog row on it triggers on *the next edit to that file* — touching it owes
  `secrets.token_hex(16)`, a collision rescan and RFC 6266 escaping.

  ✅ `isekai/evaluation/labels.py`'s `load_records` is **already gone** — deleted by `v0.22.1`. Verified:
  `grep -rn load_records` returns no code hit.

- [x] 1.2 **The six stale `CLAUDE.md` numerals**, plus two more the audit found:

  | at | says | truth |
  |---|---|---|
  | `:46-47` | *"Change one, change all four"* | **three** copies. `ci.yml:41-44` says CI *"invokes that mirror rather than keeping a third copy"* |
  | `:101-103` | `{captions,sheets,review,prompts,outputs}` | **seven** — `run.py:113-120` adds `wd14` and `tags` |
  | `:110-113` | `Cmd+Z` *"still matches `event.key.toLowerCase()`"* at `:243`, *"a known live violation"* | **false on three counts.** `ReviewApp.vue:315` now matches `event.key.toLowerCase() === 'z' \|\| event.code === 'KeyZ'` — Cyrillic **and** Dvorak. Not a violation, not in the backlog, and the line number is wrong |
  | `:128` | a change is *"four artifacts, always all four"* | `0023` shipped **five** plus `.openspec.yaml` |
  | `:136-138` | id is `(major × 100) + minor` | **no patch case.** `v0.22.1` shipped as `0023`, which the formula cannot produce |
  | `:142-144` | `skip_specs: true` *"plus `specs/.gitkeep`. The two are mutually exclusive."* | **the `plus` is right** — `0023` carries both. **The next sentence contradicts it.** Fix the sentence, keep the pairing |
  | `:187-190` | every `__init__.py` holds *"no code"* | `interface/ui/__init__.py` is **53 lines** with `serve()` and `HOST` |
  | `:226-229` | *"the catalogue holds twelve candidate checkpoints"* | **no catalogue exists in this repository.** Delete the reference or restate it without the artifact |

  Also: the *"four ignored roots"* table at `:263-272` omits **`.inputs/`** — `.gitignore:27-32` calls its
  line load-bearing because it holds a person's likeness. And `:166-168` says the changelog heading is
  `## [X.Y.0]`; `CHANGELOG.md:28` is `## [0.22.1]`.

- [x] 1.3 **Strip every quantity from the group READMEs** (`design.md` D2), replacing each with the names
  it counted. **Eight are wrong at HEAD**: `foundation/README.md:18` *"fifteen"* (16) ·
  `pipeline/README.md:31` *"nine"* (11) and `:34` *"five"* (7) · `boundary/README.md:21` *"five"* (6) and
  `:25` *"ten"* (9) · `interface/README.md:28` and `:29` *"four"* (5 and 7) ·
  `evaluation/README.md:25` *"three"* (2). Also: `isekai/README.md:11` `shared/` 4 → **5**, `:12`
  `boundary/` 7 → **6**, and the self-aware paragraph at `:16-19` goes with them.

- [x] 1.4 **Three claims that are wrong for a reason other than a count:**
  `isekai/shared/README.md:3-4` says these modules read *"no run, no flow"* — `field_map.py` imports
  both (`:39`, `:48`) and `fields.py` imports `flow` (`:17`). `isekai/interface/README.md:22` says
  *"the six endpoints"* — there are **seven**, and `app.py:1` and `:25` say six too.
  `isekai/evaluation/README.md:28-30` says *"v0.19 owes either coverage or a narrower override"* — the
  debt is real and the version is three releases stale.

- [x] 1.5 **`v0.20 review/R2`** — `ci.yml:22` calls `typecheck_ui.sh` the gate's *"sixth command"*; it is
  the **fifth of six**. ⛔ `CHANGELOG.md:30`'s *"gains a sixth command"* is correct — do not touch it.

- [x] 1.6 **`0008 S1b`** — add *pod id* to `CLAUDE.md`'s guardrail bullet at `:390-394`. ⛔ **The three
  `CHANGELOG.md` pod ids stay.** That file is append-only history; the guardrail is what stops a fourth
  being added.

- [x] 1.7 **Verify nothing in this phase touched code.** `git diff --stat` shows no `.py`, `.vue` or
  `.ts` change except docstrings and comments. **Gate green. CHANGELOG. Tick 1. Commit.**

---

## 2 — `docs/arc/`: the module graph and the data flow

**Two files. Prose, short sentences, ASCII where it helps, and no quantities** (`design.md` D2).

- [x] 2.1 **`docs/arc/modules.md`.** Measured at HEAD and unchanged since `bb01f79`:

  ```
  Module-level, cross-group:
    interface   ──▶ boundary · foundation · pipeline · shared
    pipeline    ──▶ boundary · foundation · shared
    evaluation  ──▶ boundary · foundation · shared
    foundation  ──▶ boundary · shared
    boundary    ──▶ foundation · shared
    shared      ──▶ foundation

  Lazy, broken at import time:
    shared    ──▶ boundary      vocabulary.py:126, inside load()
    shared    ──▶ evaluation    vocabulary.py:127, inside load()
    boundary  ──▶ evaluation    wd14.py:233

  No module cycles.  Two subpackage cycles, both module-level:
    foundation ⇄ shared         run → atomic_write ;  fields → flow
    foundation ⇄ boundary       flow → comfy_types ;  comfy_types → refusal
  ```

  Carry `isekai/README.md`'s structural sentence forward — *"The module graph has no cycles and never
  has; the group graph does, and drawing it as a stack would be a lie"* — and say **why** each cycle
  exists: `refusal` is what everything raises, and `atomic_write` is a primitive `run` writes through.

- [x] 2.2 **`docs/arc/data-flow.md`.** The seven verbs from `interface/cli.py:70-78`, what each stage
  reads and writes, and the run layout `runs/<input-id>/<flow-id>/<stage>/` with **all seven** stage
  directories. Name the two facts a reader most needs: **`caption` writes three artifacts in one
  invocation** and the ordering is failure isolation; and **the WD14 list, not the prose, is what the
  sheet is built from.**

- [x] 2.3 **Delete `isekai/README.md`'s edge table** (`:33-38`) and replace it with a pointer to
  `docs/arc/modules.md` (`design.md` D4). The group READMEs keep their file tables.

- [x] 2.4 **Verify no quantity survives in either file** — read both back and check every sentence.
  **Gate green. CHANGELOG. Tick 2. Commit.**

---

## 3 — `CLAUDE.md`: cut to agent operating instructions

- [x] 3.1 **`## The path` (`:281-386`) leaves.** Its content is `docs/arc/data-flow.md`'s. Anything in it
  that is a *rule* rather than a description stays, relocated to the section that owns the rule.

- [x] 3.2 **`## Layout`'s per-group inventory (`:191-249`) is deleted, not moved** — the six group
  READMEs already hold it, and moving it would create a seventh copy (`design.md` D3). What stays from
  that section: the flow-directory rules, the ignored-roots table (with `.inputs/`), and the precedence
  statements.

- [x] 3.3 **Add a one-paragraph system summary with a stated ceiling in the file itself.** The ceiling is
  the point: that paragraph is how `## The path` grew the first time.

- [x] 3.4 **Verify the result is instructions.** Read every remaining paragraph and ask *does this tell an
  agent what to do?* **Target ~200 lines from 420** — a target, not a gate. **Gate green. CHANGELOG.
  Tick 3. Commit.**

---

## 4 — The spec catches up with the code, and the one code change

- [x] 4.1 **The one code change** (`design.md` D5). `isekai/interface/ui/app.py:288`'s gate is
  `if batch.approved_path(held) is not None`. It becomes *approved **and no draft numbered above the
  approved artifact's `approved_from`***. The refusal's forward reference to *"the re-opened state is
  v0.22.2's"* is removed, because this is v0.22.2.

- [x] 4.2 **The rail reports `re-opened`** as a third status, and the form is editable in that state.

- [x] 4.3 ⛔ **HALT CHECK — the two approved counts must still agree.**
  `/api/batch["approved"]` derives from the status string; `Batch.approved_count` reads the directory.
  A third status splits them. `ui:batch:approved-count-comes-from-disk` must stay green, and the new
  `ui:approval:a-re-opened-input-is-not-counted-approved` pins it from the other side. **If they diverge,
  stop** — do not adjust the test to match.

- [x] 4.4 **Audit `image-generation`, `ui`, `review` and `cli` against the code** — the four capabilities
  `v0.22.1` touched. For each scenario: is its `THEN` true at HEAD, and can its `WHEN` occur? **Report
  every finding; fix only prose.** A scenario that is false because the *code* is wrong is a backlog row.

- [x] 4.5 **Gate green. CHANGELOG. Tick 4. Commit.**

---

## 5 — Seventeen scenarios

**They are already written, in this change's `specs/`.** This phase makes them true and bound.

```
ui                 10    Host/Origin (4) · draft precondition (2) · bundle (3) · dedup (1)
cli                 3    flow-manifest validation at load
image-generation    2    transient transport · per-flow assembly
run-directory       2    show's injected flows root · the mid-stream refusal
```

- [x] 5.1 **Read `specs/` and confirm each scenario describes behaviour that exists at HEAD.** These
  describe what `v0.22.1` already built, so a scenario that does not match is a **defect in the
  scenario** — fix it here rather than changing code to suit it. The exception is the four
  `ui:approval:*`, which describe phase 4's work.

- [x] 5.2 **Verify no key collides** with an existing one. The naive check prints two false positives —
  `ui:approval:approved-input-opens-read-only` and `ui:approval:approved-input-refuses-a-draft-update`
  are **restated on purpose**, because a `MODIFIED` requirement carries all of its scenarios. So:
  ```
  grep -rho '^- \*\*Key:\*\* .*' openspec/specs/*/spec.md \
    openspec/changes/0024-the-documents/specs/*/spec.md | sort | uniq -d
  ```
  must print **those two and nothing else**.

- [x] 5.3 **`openspec validate 0024-the-documents --strict`.** **Gate green. CHANGELOG. Tick 5. Commit.**

---

## 6 — Rebind the seventeen tests

- [x] 6.1 **Replace each `spec_exempt("behaviour; the scenario lands in 0024")` with `spec("<key>")`:**

  | file:line | test | key |
  |---|---|---|
  | `test_ui_api.py:133` | `…bound_address_is_answered` | `ui:address:a-request-to-the-bound-address-is-answered` |
  | `test_ui_api.py:143` | `…someone_elses_host_is_refused` | `ui:address:another-host-is-refused` |
  | `test_ui_api.py:155` | `…another_pages_origin_is_refused` | `ui:address:another-origin-is-refused` |
  | `test_ui_api.py:172` | `…every_loopback_alias…` | `ui:address:every-loopback-spelling-is-answered` |
  | `test_ui_api.py:343` | `…against_a_stale_draft_is_refused` | `ui:draft-update:a-stale-precondition-is-refused` |
  | `test_ui_api.py:381` | `…no_precondition_is_still_accepted` | `ui:draft-update:no-precondition-is-accepted` |
  | `test_ui_api.py:457` | `…hosted_panel_shows_each_tag_once…` | `ui:source:each-hosted-tag-is-offered-once` |
  | `test_ui.py:439` | `…build_config_edited_after_the_build…` | `ui:bundle:a-changed-build-input-makes-the-bundle-stale` |
  | `test_ui.py:463` | `…fetched_dependency_tree_is_not_source` | `ui:bundle:a-fetched-tree-is-not-an-input` |
  | `test_ui.py:475` | `…build_that_does_not_finish…` | `ui:bundle:an-unfinished-build-is-stopped-and-named` |
  | `test_flow.py:393` | `…node_the_graph_does_not_carry…` | `cli:manifest:a-dangling-node-id-is-refused-at-load` |
  | `test_flow.py:414` | `…every_role…resolves_in_its_own_graph` | `cli:manifest:every-tracked-role-resolves` |
  | `test_flow.py:426` | `…every_dial…is_one_of_its_roles_reads` | `cli:manifest:every-tracked-dial-is-read` |
  | `test_run_view.py:206` | `test_show_reads_the_flows_root_it_is_given` | `run-directory:inspection:the-injected-flows-root-is-used` |
  | `test_run_view.py:230` | `…no_flow_answers_for_refuses…` | `run-directory:inspection:an-unanswerable-directory-refuses-first` |
  | `test_generate.py:651` | `…malformed_sheet_does_not_cost_its_siblings…` | `image-generation:assembly:a-bad-sheet-is-per-flow` |
  | `test_generate.py:715` | `…recorded_transient_not_permanent` | `image-generation:failure:an-unreachable-endpoint-is-transient` |

- [x] 6.2 **Add tests for the two *new* `ui:approval:*` scenarios** phase 4 built —
  `a-re-opened-input-is-editable` and `a-re-opened-input-is-not-counted-approved`. The other two keys in
  that requirement already exist and are already bound; **re-run their tests** against the narrowed gate,
  because `approved-input-refuses-a-draft-update`'s `WHEN` gained an *and no later draft* clause.

- [x] 6.3 ✅ **Done when `grep spec_exempt tests/ | grep 0024` returns nothing.** Paste the empty output.
  **Gate green. CHANGELOG. Tick 6. Commit.**

---

## 7 — The acceptance

- [ ] 7.1 **`make gate` — all six commands, output pasted.**

- [ ] 7.2 **`grep spec_exempt tests/ | grep 0024` returns nothing.**

- [ ] 7.3 **Every numeral this change touched was re-derived from the tree**, not from the sentence it
  replaced. For each: the command that produced it, and its output.

- [ ] 7.4 **Walk the re-opened path by hand.** Approve an input · try to edit it, and confirm the refusal
  · run `review --flow F --new-version` · reload the surface · confirm the input is **editable** and the
  rail says **re-opened** · save an edit · confirm the batch's approved count still matches the
  directories.

- [ ] 7.5 **Confirm no flow moved** — `uv run pytest -k test_every_tracked_flow_matches`.

- [ ] 7.6 **Record what was not verified.** No pod, no render, and **the other 244 scenarios were not
  audited** — only the four capabilities `v0.22.1` touched. That is the design; the full pass is a
  backlog row.

- [ ] 7.7 **`/simplify` over this change's own diff.** **Gate green. CHANGELOG. Tick 7. Commit.**
