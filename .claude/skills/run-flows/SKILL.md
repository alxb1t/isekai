---
name: run-flows
description: Run a directory of photographs through both flows — tag, caption, sheet, review in the browser, render on a rented GPU — and hand the operator a comparison page. Use when the operator asks to run the flows, make a dataset, or render a batch in .data/<batch>/photos.
---

# run-flows — a batch of photographs to a comparison page

Runs `summon-anime-wai` and `conjure-anime-wai` over `.data/<batch>/photos/` and ends with
`.data/<batch>/compare.html`. The commands are exact: run them as written, with `<batch>` replaced. Why each step
is shaped this way: [0035 design D1](../../../openspec/changes/archive/0035-the-flow-skills/design.md#d1).

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
- **Never report or write down** a pod id, a volume id or a pod's host and port — `log.txt` holds them, and
  step 4's filter drops them.
- **Never run `gpunit volume down` on your own.** Step 5 asks first. The ceiling is not a teardown: past it, a
  window nobody closes bills until `volume down` deletes its volume.

## 0 — Check

The shell forgets variables between commands, so every block sets `BATCH` itself.

```bash
BATCH=.data/<batch>
ls "$BATCH"/photos | wc -l
curl -sf --max-time 3 -o /dev/null http://127.0.0.1:11434/api/tags && echo "ollama up"
```

No photographs, or no `ollama up`: stop and tell the operator which.

## 1 — Tag, caption, sheet

Run each block, in order. After each, report its exit status and the refusal count, which is cumulative. On more
than a few photographs a block outlasts a foreground command: run it in your shell tool's background mode and wait
for its exit.

```bash
BATCH=.data/<batch>
uv run python -m isekai tag --flow summon-anime-wai --flow conjure-anime-wai --runs "$BATCH/runs" "$BATCH"/photos/* >> "$BATCH/log.txt" 2>&1; echo "exit $?"
echo "refusals: $(grep -c 'refused:' "$BATCH/log.txt")"
```

```bash
BATCH=.data/<batch>
uv run python -m isekai caption --flow summon-anime-wai --flow conjure-anime-wai --runs "$BATCH/runs" "$BATCH"/photos/* >> "$BATCH/log.txt" 2>&1; echo "exit $?"
echo "refusals: $(grep -c 'refused:' "$BATCH/log.txt")"
```

```bash
BATCH=.data/<batch>
uv run python -m isekai sheet --flow summon-anime-wai --flow conjure-anime-wai --runs "$BATCH/runs" "$BATCH"/photos/* >> "$BATCH/log.txt" 2>&1; echo "exit $?"
echo "refusals: $(grep -c 'refused:' "$BATCH/log.txt")"
```

When the count rose, read only the refusals — `grep 'refused:' .data/<batch>/log.txt` — and show them to the operator.
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
  state=DOWN
  for i in $(seq 30); do
    curl -sf --max-time 2 -o /dev/null "http://127.0.0.1:$port/api/batch" && { state=up; break; }
    sleep 2
  done
  echo "$port $state"
done
```

A port `DOWN`: read `grep 'refused:' .data/<batch>/log.txt`, stop both servers (step 3's last block), and report.

Both up: give the operator the two addresses and **stop until the operator says "approved"**:

- `summon-anime-wai` — http://127.0.0.1:8517
- `conjure-anime-wai` — http://127.0.0.1:8518

## 3 — Count the approvals

```bash
BATCH=.data/<batch>
ls "$BATCH/runs" | wc -l
for flow in summon-anime-wai conjure-anime-wai; do
  approved=$(find "$BATCH/runs" -path "*/$flow/review/*.approved.json" | sed "s#/$flow/review/.*##" | sort -u | wc -l)
  echo "$flow: $((approved)) runs approved"
done
```

Report the run count and each flow's approved runs — a run approved twice counts once. Then stop both servers:

```bash
pkill -f -- '-m isekai ui --flow .* --port 851[78]'; echo "exit $?"
```

A run a flow has no approval for refuses at step 4, before anything is rented. When a count is short, tell the
operator which flow and ask whether to go back to step 2.

## 4 — Render: stop for the go

**Stop and ask for the go.** Quote both prices: *one pod session, at most 45 minutes and about $0.30; the models
volume, 50 GB for up to 4 hours, about $0.02*. Only the operator's explicit go in this session authorises the
spend.

On the go, open the window first. `volume up` creates the models volume, or extends a live one to 4 hours from now:

```bash
BATCH=.data/<batch>
uv run --env-file .env gpunit volume up --yes >> "$BATCH/log.txt" 2>&1; echo "exit $?"
grep -o 'until [0-9TZ:-]*' "$BATCH/log.txt" | tail -1
```

- **Exit 0**: go on to the render block.
- **Exit 3**: the create's answer was lost, and a volume may bill. Render nothing, and tell the operator at once.
  No window is recorded, so `volume down` asks y/N on its input about each `gpunit-isekai` volume and, with no
  answer, keeps it: do not run it yourself. Ask the operator to run `uv run --env-file .env gpunit volume down`
  in an interactive terminal and answer its prompt. Then confirm it yourself: the RunPod MCP's
  `list-network-volumes` shows no volume named `gpunit-isekai`. Report what it returned. A volume still listed:
  tell the operator at once — it is billing.
- **Any other non-zero**: report `grep 'refused:' .data/<batch>/log.txt`, and render nothing.

Then run this block **in your shell tool's background mode**, not in the foreground, and wait for it to
exit — do not poll the log. The session outlasts a foreground command, about 13 minutes for five photographs, and a
command killed mid-render can cut the teardown short. `render` halts itself at the ceiling.

```bash
BATCH=.data/<batch>
uv run python -m isekai render "$BATCH/runs" summon-anime-wai=1 conjure-anime-wai=1 > /dev/null 2>&1; echo "exit $?"
echo "renders: $(grep -c ': rendered ' "$BATCH/log.txt")"
echo "refusals: $(grep -c 'refused:' "$BATCH/log.txt")"
```

`render` tears down its own pod on every exit. A refusal naming a recorded or listed pod leaves that pod: tell the
operator at once, and run `uv run --env-file .env gpunit down` only on their word — gpunit reads no `.env`. Confirm
it is gone yourself: the RunPod MCP's `list-pods` shows no pod named `gpunit-isekai`. Report what it returned. A
`refused:` line may follow a time, so the counts match it anywhere on a line.

- **Exit 0**: report the render count.
- **Non-zero**: read `grep 'refused:' .data/<batch>/log.txt` and
  `tail -15 .data/<batch>/log.txt | grep -v -e 'root@' -e '[Pp]od [a-z0-9]\{12,\}' -e '[Vv]olume [a-z0-9]\{8,\}'`,
  and report them. A
  `ceiling` refusal keeps the renders so far; step 4 again renders only the rest, and needs a new go.
- **The teardown failed** (its refusal names `uv run --env-file .env gpunit down`): tell the operator at once, and
  run it only on their word. Once `list-pods` shows the pod gone and `gpunit down` still refuses, run
  `rm -f .gpunit/pod .gpunit/pending`. A pod still listed: tell the operator at once — it is billing.

## 5 — The comparison page, then the window

Step 5 opens with the whole of the `compare-renders` skill:

```bash
uv run python -m isekai compare .data/<batch>
```

Hand the operator the path it prints. Do not open the page.

Then name the window's end — the last `until` line step 4 printed — and ask: *another batch?* Tell the operator
the end is not a teardown: past it, the volume bills until `volume down` deletes it. On
yes, skip the close: the next step 4 extends the window. On no, close it:

```bash
BATCH=.data/<batch>
uv run --env-file .env gpunit volume down >> "$BATCH/log.txt" 2>&1; echo "exit $?"
```

Whichever the answer, confirm it yourself through the RunPod MCP's `list-network-volumes`, and report what it
returned. After a no it shows no volume named `gpunit-isekai`; one still listed: tell the operator at once — it
is billing. After a yes it shows the window's one volume, open until the operator closes it.
