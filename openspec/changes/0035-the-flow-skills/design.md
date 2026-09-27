# Design — 0035 the flow skills

How an agent runs the flows for the operator with little context: skills that chain the existing verbs, a
`compare` verb for the one step that must read runs, and a render session that cannot leave a pod billing.
**Verdict: `feasible`.** Every line below was re-checked at `main` `866c346`.

## Context

- **No verb takes a directory**, and every stage verb takes many photographs, so a shell glob gives a batch. Each
  prints one line per photograph, per flow and per stage (`isekai/interface/cli.py`, `_say`); refusals go to stderr
  as `refused: …`, and the exit status is 1 when any fired.
- **`ui` serves one flow per process** (`cli.py`, `_OneFlow`), blocks, and prints
  `<flow>: N inputs, M approved -- http://127.0.0.1:<port>` once; an approval is a file,
  `<runs>/<id>/<flow>/review/NNN.approved.json`.
- **`infra/up.sh`** prints `  Tunnel: ssh … -N -L 8188:localhost:8188 root@<host> -p <port>` when port 22 is mapped
  (`:169`); **`infra/down.sh`** removes both record files only on a 204 and keeps them on a 404 (`:26-35`). No script
  joins them, and none sets a trap.
- **`CLAUDE.md:217-232`**: a pod goes up only for a phase `tasks.md` marks metered.
- **`tag` sometimes exits 134 after writing everything** — `libc++abi: … recursive_mutex lock failed` at interpreter
  exit. The throwing thread is onnxruntime's telemetry client, not the session: see [D5](#d5).
- **The operator's example page**, `.data/v0.24/compare.html`, sits beside `photos/` and `runs/`, links each image by
  a relative path with `loading=lazy`, and embeds nothing.
- `run_view.rendered` (`isekai/interface/run_view.py:147`) lists each flow's rendered seeds from filenames.

## Goals / Non-Goals

**Goals**

- An agent runs a batch end to end from the skill alone, and reads nothing but short command output.
- A render session always ends with the pod torn down.

**Non-Goals**

- Anything the [proposal](proposal.md#not-in-this-change) sets out.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | skills chain the existing verbs; output to a log; the agent reads statuses and counts | the operator: the skill runs the commands, with little context | new batch and status verbs |
| [D2](#d2) | a `compare` verb writes the page and prints its path | the page cannot be written without reading the runs | a page written by the agent |
| [D3](#d3) | `infra/render.sh`, with a trap on exit | only a trap tears down whichever step fails | teardown as a skill step |
| [D4](#d4) | the pod rule gains the operator's go, and the record files' removal after a confirmed teardown | a skill spends outside any change; `0033 security/S1`'s documentation half | leaving the rule to be broken |
| [D5](#d5) | `ORT_DISABLE_TELEMETRY=1` is set before onnxruntime is imported, on every path that imports it | the abort turns a success into a failed status; loading onnxruntime connects to Microsoft, and no local tool makes an outbound call | releasing the session earlier; `disable_telemetry_events()`; ending the process abruptly |
| [D6](#d6) | a test parses every command a skill names | the skills are only worth their accuracy | review alone |
| [D7](#d7) | the operator runs `run-flows` end to end as the acceptance | the skills are proved by being used | |
| [D8](#d8) | a minor, one feature | a new verb and a new capability | a patch |

### D1

**The skills, and the batch they work on.**

```
.data/<batch>/
  photos/        the operator's photographs
  runs/          --runs for every verb
  log.txt        every command's output, appended
  compare.html   written by `compare`
```

- **`run-flows`**, given `.data/<batch>/photos`:
  1. `tag`, `caption` and `sheet` — each `--flow summon-anime-wai --flow conjure-anime-wai --runs "$BATCH/runs"
     "$BATCH"/photos/*` — output appended to `"$BATCH/log.txt"`; after each, the agent reads the exit status and
     `grep -c '^refused' "$BATCH/log.txt"`, and on a refusal only that line.
  2. `ui` once per flow, in the background, on ports `8517` and `8518`, over the run ids `ls "$BATCH/runs"` names; the
     agent hands the operator both URLs and **stops until the operator says "approved"**.
  3. It counts approvals — `ls "$BATCH"/runs/*/<flow>/review/*.approved.json | wc -l` per flow — reports them, and
     stops both servers.
  4. **It stops for the operator's go**, quoting the ceiling, then runs `bash infra/render.sh "$BATCH/runs"
     summon-anime-wai=1 conjure-anime-wai=1` ([D3](#d3)), and confirms through the RunPod MCP that the pod is gone.
  5. `python -m isekai compare "$BATCH"` ([D2](#d2)), and hands the operator the path it prints.
- **`compare-renders`** is step 5 alone.
- **Both skills forbid** reading a photograph, anything under `runs/`, `log.txt` beyond the counted lines, and the
  page. They say nothing of what the photographs are: that is the operator's to know, and an agent could only
  check it by reading one (amended during the build, on the operator's decision).
- An exit status of 134 with no `refused` line is the tagger's native abort; the agent reports it and goes on
  ([D5](#d5) removes it).

### D2

**`compare`.** `python -m isekai compare <batch>` — a positional batch directory, no `--flow`, no photographs, no
`--runs`: the runs root is `<batch>/runs`. The page's shape is the operator's example: one entry per run, the run's
photograph copy, then each flow's renders under its latest approval, labelled `<flow> · seed <seed>`, each with the
positive prompt it came from beneath it; each flow's latest caption in a full-width row below the images (amended
during the build, on the operator's decision); *no render yet* where a flow has none. Images are linked relative to the page,
with `loading=lazy`, and none is embedded. The page is written to `<batch>/compare.html` through
`foundation/atomic_write.py`, and the verb prints its path alone. A new `isekai/interface/compare_view.py` builds it
with `html.escape` and `pipeline.generate.rendered_seeds` — the rule `generate` itself decides a render by (amended
in the build's simplify pass; it was `run_view.rendered`); the entry point stays stdlib-only. A run directory this
build carries no flow for reads *not a tracked flow* rather than refusing the page (amended in converge).

### D3

**`infra/render.sh <runs> <flow>=<count> …`**, run from the repository root:

```
trap: down.sh (when .runpod_pod_id exists) · kill the tunnel
up.sh ──▶ host, port from its "Tunnel:" line ──▶ ssh -N -L 8188 … &
──▶ wait ≤ 300 s for http://127.0.0.1:8188/system_stats
──▶ generate --flow <flow> --count <count> --server http://127.0.0.1:8188 --runs <runs> <every run id>
──▶ exit ──▶ trap
```

- The trap is set before `up.sh` runs, on `EXIT`, `INT` and `TERM`. `up.sh` is run unchanged, its output appended to
  the batch's log and shown.
- A flow's `generate` failing does not stop the next flow; the script exits 1 when any failed. A wait past 300 s
  exits through the trap.
- *Amended in converge:* the trap is on `HUP` too, and the teardown ignores `INT`, `TERM` and `HUP` rather than
  resetting them, so a second Ctrl-C cannot kill `down.sh` mid-DELETE. A watchdog started after the trap and before
  `up.sh` refuses at 44 minutes — `CLAUDE.md`'s 45-minute ceiling, less one for `down.sh` — stops the command in
  flight and exits through the trap; the renders written are kept, and the same command renders only the rest.

### D4

**`CLAUDE.md`'s pod rule** (`:229-232`):
- before: *"the authority to spend comes from the **phase**, never from the agent: **a pod goes up only for a phase
  `tasks.md` marks metered.**"*
- after: the authority comes from a phase `tasks.md` marks metered, **or from the operator's explicit go in the
  session, which quotes the ceiling** — never from the agent.
- A new line under *Who confirms*: when the MCP confirms a pod gone after a teardown that did not answer 204, delete
  `.runpod_pod_id` and `.runpod_pod_image` — a leftover image record would lend its pin to a later render
  (`0033 security/S1`, its documentation half).

### D5

**The native abort is onnxruntime's telemetry.** Amended during the build, on the operator's decision after a spike.

- **The cause**, from an `lldb` backtrace of an aborted `tag`: at exit, `PosixEnv::~PosixEnv` →
  `PosixTelemetry::Shutdown` tears down the telemetry client (`Microsoft::Applications::Events`) while its worker
  thread handles an upload's HTTP response, and that thread locks a destroyed `recursive_mutex`.
- **The session is not the cause.** No `OnnxSession` or `InferenceSession` is alive when `main` returns, so the
  first reading of this decision — release the session before `dispatch` returns — was already the code's behaviour.
- **It needs the Ollama call.** The upload is in flight at exit only when the process runs long enough; WD14 alone,
  or with a fake hosted tagger, gave no abort in 60 runs each.
- **Loading onnxruntime connects to Microsoft.** `import onnxruntime` alone opened an HTTPS connection to a
  Microsoft Corporation address (whois), sampled with `lsof` on 3 of 3 runs; numpy and Pillow alone opened none.
- **`disable_telemetry_events()` fixes neither.** Called after the import, the connection was already open; with it,
  the real `tag` loop still aborted on 5 of 40 runs.
- **The fix:** `ORT_DISABLE_TELEMETRY=1` in the environment before the import — a switch the binary reads at load.
  With it set, the import opened no connection on 4 of 4 runs. `silence_onnxruntime()` in `boundary/wd14.py` sets
  it, and both `OnnxSession`s call it before `_require("onnxruntime")`: WD14's and `evaluation/eval_backends.py`'s,
  so no local tool makes an outbound call. The repair is proved by the loop that reproduced it, with every run's
  sockets sampled.

### D6

**`tests/test_agent_skills.py`** reads every `python -m isekai` line inside a code block of
`.claude/skills/*/SKILL.md`, splits it with `shlex`, and parses it with `build_parser()`; a line the parser refuses
fails naming the skill and the line. Its twin feeds a skill text with an unknown flag.

### D7

**The acceptance is the operator using `run-flows`** on synthetic portraits in a new `.data/<batch>/`, end to end:
the URLs, "approved", the go, `render.sh`, the MCP's confirmation, `compare.html`. The record keeps each command
and its one-line result. Metered under the standing ceiling.

### D8

**A minor.** A new verb, a new script, a new capability; one feature: the flow skills.

## Dependencies

None.

## Risks / Trade-offs

- [An agent ignores the skill and reads a run] → the skill forbids it by name; nothing enforces it.
- [The "Tunnel:" line's wording moves] → `render.sh` refuses when it cannot find a host and a port, and the trap
  tears the pod down.
- [Two `ui` servers on fixed ports] → a port in use refuses at start, before the operator is handed anything.

## Verdict

`feasible`.
