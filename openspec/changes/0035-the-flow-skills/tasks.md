# Tasks — 0035 the flow skills

The verb and the script first, then the abort, then the skills that name them; the operator's own run of
`run-flows` last ([D7](design.md#d7)).

## Progress

- [x] 1 — `compare`: the comparison page
- [x] 2 — `infra/render.sh`: a render session that always tears down
- [ ] 3 — the tagger's native abort
- [ ] 4 — the skills, their check, the pod rule and the docs
- [ ] 5 — 🛑 **HUMAN · METERED · HALT** — the operator runs `run-flows` end to end

Line numbers are `866c346`'s; find each site by the text it names.

## 1 — `compare`: the comparison page

- [x] 1.1 **HALT CHECK** — there is no `compare` verb.
  Verify: `grep -c '("compare", ' isekai/interface/cli.py` prints `0`.
- [x] 1.2 Add `compare` to `VERBS` in `isekai/interface/cli.py`, with a positional batch directory and without the photographs, `--runs` and `--flow` arguments; build the page in a new `isekai/interface/compare_view.py`, per [D2](design.md#d2).
  Verify: `grep -c '("compare", ' isekai/interface/cli.py` prints `1`, and `test -f isekai/interface/compare_view.py; echo $?` prints `0`.
- [x] 1.3 In a new `tests/test_compare.py`, test `the-page-links-photographs-to-renders`, `a-run-without-a-render-is-marked`, `only-the-path-is-printed` and `a-batch-without-runs-is-refused` under `cli:compare:`; add `compare` to `tests/test_pipeline_cli.py`'s `EXPECTED_VERBS` and give it a batch argument in `test_each_verb_is_reachable_as_a_subcommand` (`:173-179`).
  Verify: `grep -c 'cli:compare:' tests/test_compare.py` prints `4`, and `grep -c '"compare"' tests/test_pipeline_cli.py` prints a number above `0`.

## 2 — `infra/render.sh`: a render session that always tears down

- [x] 2.1 **HALT CHECK** — no script joins `up.sh` and `down.sh`.
  Verify: `test -f infra/render.sh; echo $?` prints `1`.
- [x] 2.2 Write `infra/render.sh` per [D3](design.md#d3): the trap on `EXIT`, `INT` and `TERM` before `up.sh`, the tunnel from `up.sh`'s "Tunnel:" line, the bounded wait for `/system_stats`, and `generate` per flow; `bash -n infra/render.sh` passes.
  Verify: `grep -c '^trap ' infra/render.sh` prints `1`, and `bash -n infra/render.sh; echo $?` prints `0`.
- [x] 2.3 In `tests/test_infra.py`, test `pod-image:session:every-exit-tears-down` and `pod-image:session:the-endpoint-is-awaited` against the script's text.
  Verify: `grep -c 'pod-image:session:' tests/test_infra.py` prints `2`.

## 3 — the tagger's native abort

- [ ] 3.1 Run `python -m isekai tag --new-version --flow summon-anime-wai --runs <root> <run>` on a synthetic portrait until it exits 134, up to twenty times, and record the runs and exits as the line `Before: <runs> runs, <n> exited 134` in `openspec/changes/0035-the-flow-skills/native-abort.md`.
  Verify: `grep -c '^Before: ' openspec/changes/0035-the-flow-skills/native-abort.md` prints `1`.
- [ ] 3.2 **HALT CHECK** — the abort reproduced.
  Verify: `grep -c '^Before: .*, [1-9][0-9]* exited 134' openspec/changes/0035-the-flow-skills/native-abort.md` prints `1`.
- [ ] 3.3 Release the WD14 session when the verb's work is done, per [D5](design.md#d5); re-run the same loop and record `After: <runs> runs, 0 exited 134`.
  Verify: `grep -c '^After: .*, 0 exited 134' openspec/changes/0035-the-flow-skills/native-abort.md` prints `1`.

## 4 — the skills, their check, the pod rule and the docs

- [ ] 4.1 Write `.claude/skills/run-flows/SKILL.md` and `.claude/skills/compare-renders/SKILL.md` per [D1](design.md#d1): exact commands, the stops for "approved" and for the go, and what never to read.
  Verify: `ls .claude/skills/run-flows/SKILL.md .claude/skills/compare-renders/SKILL.md | wc -l` prints `2`.
- [ ] 4.2 In a new `tests/test_agent_skills.py`, test `agent-skills:commands:every-command-parses` and `agent-skills:commands:a-stale-command-fails`, per [D6](design.md#d6).
  Verify: `grep -c 'agent-skills:commands:' tests/test_agent_skills.py` prints `2`.
- [ ] 4.3 Amend `CLAUDE.md`'s pod rule (`:229-232`) and add the record files' removal under *Who confirms*, per [D4](design.md#d4).
  Verify: `grep -c 'explicit go in the session' CLAUDE.md` prints `1`, and `grep -c 'marks metered\.\*\*' CLAUDE.md` prints `0`.
- [ ] 4.4 Name `compare` in the `cli` spec's preamble (`openspec/specs/cli/spec.md:5-7`), in `README.md`'s verb list (`:8`) and in `docs/data-flow.md` beside `show`; add a `README.md` section naming both skills and `infra/render.sh`.
  Verify: `grep -c 'compare' openspec/specs/cli/spec.md` prints a number above `0`, and `grep -c 'run-flows' README.md` prints a number above `0`.

## 5 — 🛑 **HUMAN · METERED · HALT** — the operator runs `run-flows` end to end

**Ceiling: 45 minutes and ~$0.30.** The operator's go authorises the spend ([D4](design.md#d4)); `render.sh` tears
down, and the RunPod MCP confirms. Synthetic portraits only.

- [ ] 5.1 ⛔ **HALT.** The operator puts synthetic portraits in `.data/<batch>/photos/` and runs `run-flows` on it; record the go as the first line of `openspec/changes/0035-the-flow-skills/acceptance.md`, `Go: <date>`.
  Verify: `grep -c '^Go: ' openspec/changes/0035-the-flow-skills/acceptance.md` prints `1`.
- [ ] 5.2 Record each command `run-flows` ran and its one-line result, the MCP's confirmation that the pod is gone, and the path `compare` printed, in `acceptance.md`, with no absolute path.
  Verify: `grep -c -e 'compare.html' -e 'pod gone' openspec/changes/0035-the-flow-skills/acceptance.md` prints a number above `1`.
