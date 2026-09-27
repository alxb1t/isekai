---
name: run-flows
description: Run a directory of photographs through both flows — tag, caption, sheet, review in the browser, render on a rented GPU — and hand the operator a comparison page. Use when the operator asks to run the flows, make a dataset, or render a batch in .data/<batch>/photos.
---

# run-flows — a batch of photographs to a comparison page

Runs `summon-anime-wai` and `conjure-anime-wai` over `.data/<batch>/photos/` and ends with
`.data/<batch>/compare.html`. The commands are exact: run them as written, with `<batch>` replaced. Why each step
is shaped this way: [0035 design D1](../../../openspec/changes/0035-the-flow-skills/design.md#d1).

```
.data/<batch>/
  photos/        the operator's photographs, JPEG or PNG
  runs/          every verb's --runs
  log.txt        every command's output, appended
  compare.html   written by step 5
```

## Never

- **Never read** a photograph, anything under `runs/`, `compare.html`, or `log.txt` beyond the lines the steps
  below grep. Your context is for counts and statuses.
- **Never start step 4 without the operator's go** in this session. It rents a GPU.

## 0 — Check

The shell forgets variables between commands, so every block sets `BATCH` itself.

```bash
BATCH=.data/<batch>
ls "$BATCH"/photos | wc -l
curl -sf --max-time 3 -o /dev/null http://127.0.0.1:11434/api/tags && echo "ollama up"
```

No photographs, or no `ollama up`: stop and tell the operator which.

## 1 — Tag, caption, sheet

Run each block, in order. After each, report its exit status and the refusal count, which is cumulative.

```bash
BATCH=.data/<batch>
uv run python -m isekai tag --flow summon-anime-wai --flow conjure-anime-wai --runs "$BATCH/runs" "$BATCH"/photos/* >> "$BATCH/log.txt" 2>&1; echo "exit $?"
echo "refusals: $(grep -c '^refused' "$BATCH/log.txt")"
```

```bash
BATCH=.data/<batch>
uv run python -m isekai caption --flow summon-anime-wai --flow conjure-anime-wai --runs "$BATCH/runs" "$BATCH"/photos/* >> "$BATCH/log.txt" 2>&1; echo "exit $?"
echo "refusals: $(grep -c '^refused' "$BATCH/log.txt")"
```

```bash
BATCH=.data/<batch>
uv run python -m isekai sheet --flow summon-anime-wai --flow conjure-anime-wai --runs "$BATCH/runs" "$BATCH"/photos/* >> "$BATCH/log.txt" 2>&1; echo "exit $?"
echo "refusals: $(grep -c '^refused' "$BATCH/log.txt")"
```

When the count rose, read only the refusals — `grep '^refused' .data/<batch>/log.txt` — and show them to the operator.
A refusal names its own fix; do not work around one.

## 2 — Review: stop for "approved"

Start one review surface per flow, in the background:

```bash
BATCH=.data/<batch>
PYTHONUNBUFFERED=1 nohup uv run python -m isekai ui --flow summon-anime-wai --port 8517 --runs "$BATCH/runs" $(ls "$BATCH/runs") >> "$BATCH/log.txt" 2>&1 &
PYTHONUNBUFFERED=1 nohup uv run python -m isekai ui --flow conjure-anime-wai --port 8518 --runs "$BATCH/runs" $(ls "$BATCH/runs") >> "$BATCH/log.txt" 2>&1 &
```

Wait until both answer, up to a minute:

```bash
for port in 8517 8518; do
  for i in $(seq 30); do curl -sf --max-time 2 -o /dev/null "http://127.0.0.1:$port/api/batch" && break; sleep 2; done
  curl -sf --max-time 2 -o /dev/null "http://127.0.0.1:$port/api/batch" && echo "$port up" || echo "$port DOWN"
done
```

A port `DOWN`: read `grep '^refused' .data/<batch>/log.txt`, stop both servers (step 3's last block), and report.

Both up: give the operator the two addresses and **stop until the operator says "approved"**:

- `summon-anime-wai` — http://127.0.0.1:8517
- `conjure-anime-wai` — http://127.0.0.1:8518

## 3 — Count the approvals

```bash
BATCH=.data/<batch>
ls "$BATCH/runs" | wc -l
for flow in summon-anime-wai conjure-anime-wai; do
  echo "$flow: $(find "$BATCH/runs" -path "*/$flow/review/*.approved.json" | wc -l) approvals"
done
```

Report the run count and each flow's approvals. Then stop both servers:

```bash
pkill -f -- '-m isekai ui --flow .* --port 851[78]'; echo "exit $?"
```

A run a flow has no approval for refuses at step 4, before anything is rented. When a count is short, tell the
operator which flow and ask whether to go back to step 2.

## 4 — Render: stop for the go

**Stop and ask for the go.** Quote the ceiling: *one pod session, at most 45 minutes and about $0.30*. Only the
operator's explicit go in this session authorises the spend.

On the go:

```bash
BATCH=.data/<batch>
bash infra/render.sh "$BATCH/runs" summon-anime-wai=1 conjure-anime-wai=1 > /dev/null 2>&1; echo "exit $?"
echo "renders: $(grep -c ': rendered ' "$BATCH/log.txt")"
echo "refusals: $(grep -c '^refused' "$BATCH/log.txt")"
```

`render.sh` tears the pod down on every exit. Confirm it is gone yourself: the RunPod MCP's `list-pods` shows no
pod named `isekai`. Report what it returned.

- **Exit 0**: report the render count.
- **Non-zero**: read `grep '^refused' .data/<batch>/log.txt` and `tail -15 .data/<batch>/log.txt`, and report
  them.
- **`down.sh` could not confirm** (its message names the RunPod MCP): once `list-pods` shows the pod gone, run
  `rm .runpod_pod_id .runpod_pod_image`. A pod still listed: tell the operator at once — it is billing.

## 5 — The comparison page

Step 5 is the whole of the `compare-renders` skill:

```bash
uv run python -m isekai compare .data/<batch>
```

Hand the operator the path it prints. Do not open the page.
