# Design — 0037 the boundaries

How each boundary refuses what it cannot trust, and how the tests follow. **Verdict: feasible** — each fix is local
to one boundary, reuses a refusal path that exists, and adds no dependency.

## Context

See [proposal](proposal.md) — *Why*. The boundaries, and where each fix sits:

```
  photograph ──▶ run frame ──▶ review surface ──▶ ComfyUI transport ──▶ pod
                 D7            D6                 D1 D2 D3 D4 D5        render session D8 D9 D11
```

What holds at the cut (`fcb5e3b`):

- **`ComfyClient`** (`isekai/boundary/comfy/client.py`) calls `request.urlopen` at `:48`, `:61`, `:67`, `:80` and
  `:86`, with no `timeout=`. `_reported` (`:95-136`) turns every failure into a `TransportFailure`: an HTTP status
  below 500 is permanent; a 5xx, a cut answer, a `URLError` or an `OSError` is transient; a `ValueError`, `KeyError`
  or `TypeError` is permanent.
- **The reader's precedent:** `isekai/boundary/ollama.py:80` builds `OPENER` with `ProxyHandler({})`, and
  `tests/test_ollama.py`'s `test_no_proxy_in_the_environment_can_capture_the_photograph` holds it by patching
  `http.client.HTTPConnection`.
- **Tests stub `urllib.request.urlopen`:** `tests/test_generate.py:815`, `:841`, `:903`, `:977`, `:1310`;
  `tests/test_resume.py:609`; and the guards `tests/test_sheet_stage.py:85-89` and `tests/test_pipeline_cli.py:442-446`.
  A client with its own opener bypasses every one of them.
- **`render`** (`isekai/pipeline/generate.py:418-512`) catches `Refusal` only; `_recorded` (`:515-538`) records a
  `TransportFailure` by its kind and anything else as permanent. The render's budget is one attempt (`BUDGETS`), so
  either kind refuses the next render until its record is deleted (D21).
- **`_submit`** (`:541-560`) polls with no deadline; a `prompt_id` that is not a string never matches the history's
  keys.
- **The review surface** answers a `Refusal` with 409 and `{"refusal": …}` (`isekai/interface/ui/app.py:152-155`);
  anything else is a 500. `read_input` (`:260`, `:262`, `:270`), `_wd14` (`:400-403`) and `_tags` (`:435`, `:453`)
  index unchecked; `put_draft` converts its body at `:326-329`, before the lock.
- **`Run.photo`** (`isekai/foundation/run.py:245-248`) joins the frame's name unchecked; `_run_for` (`:290`) reads
  `sha256` unchecked. `open_run` writes the name as `photo.png` or `photo.jpg` (`:324`).
- **`infra/render.sh`**: the watchdog sleeps `$CEILING` once (`:79-87`); `open_tunnel` (`:97-102`) accepts new keys
  into `~/.ssh/known_hosts`. `tests/test_infra.py`'s `unbounded_session` (`:1016-1040`) requires the literal
  `sleep "$CEILING"`.
- **curl follows an exported `http_proxy` to loopback.** curl 8.6 on this machine sends `http://127.0.0.1:8188`
  to the proxy, so `render.sh`'s port check (`:45`) and wait loop (`:108`) never reach the tunnel with a proxy
  exported.

## Goals / Non-Goals

**Goals:** no photograph through a proxy; no unbounded wait on the metered path; an upload no part can re-shape; no
control character from an endpoint in a refusal; no 500 from a damaged file or body; no run pointing outside itself;
no watchdog outliving its session; no host key outliving its session.

**Non-Goals:** the pod's real host-key check; EXIF; the flows, the prompt or the image; a new dependency.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the client's own `OPENER` with `ProxyHandler({})`; tests stub it | the reader's rule, one mechanism | `no_proxy` for loopback — depends on the environment |
| [D2](#d2) | every request times out at 60 s, refused transient with its own message | a stopped pod must not hold a request open | the "could not be reached" message — it sends the operator to bring a pod up |
| [D3](#d3) | the poll gives up at 600 s, transient; a prompt id must be a non-empty string | an unattended session must end; a wrong id must not poll for ever | leaving `0013·R10` settled — its premise failed |
| [D4](#d4) | a random boundary, redrawn while any part holds it; names percent-encoded | a body no part can end early | a fixed boundary with a scan that refuses |
| [D5](#d5) | printable characters only, before truncating | a terminal and an agent read the refusal | `repr` — it quotes the body in Python's syntax |
| [D6](#d6) | the surface checks each read and the draft body, and refuses by name | the stages already do | a generic 500 handler — it would name nothing |
| [D7](#d7) | a frame's photograph name is one plain filename; its keys are checked | the name is a file's word, not a path | resolving and checking containment — a plain name is simpler and stricter |
| [D8](#d8) | the watchdog polls `kill -0 $$` every 5 s | it ends within seconds of its session | a parent-PID check at the ceiling only |
| [D9](#d9) | a per-session known-hosts file, removed by the trap | a reused address must not cost a session | `StrictHostKeyChecking=no` — it drops even the session's own check |
| [D10](#d10) | one metered session with a dead `http_proxy` exported | renders arriving prove the transport end to end | a unit test alone — it proves no real upload |
| [D11](#d11) | `render.sh`'s requests to `$SERVER` pass `--noproxy '*'` | the session's own checks must not follow a proxy either | exporting `no_proxy` for the session — it would let the old client pass too |

### D1

**The client's own opener.** `isekai/boundary/comfy/client.py` declares
`OPENER = request.build_opener(request.ProxyHandler({}))` and every call goes through `OPENER.open(req,
timeout=TIMEOUT)`. `docs/decisions.md`'s D6 gains one sentence — "The ComfyUI transport ignores the environment's
proxy the same way." — and `0037` joins its *Made by*.

- **The test:** `test_no_proxy_in_the_environment_reaches_the_rendering_endpoint` in `tests/test_generate.py`,
  bound to `comfy-transport:proxy:an-exported-proxy-is-ignored`. It exports `http_proxy`, patches
  `http.client.HTTPConnection` as `tests/test_ollama.py` does, and asserts the refusal names `127.0.0.1:8188`; its
  twin shows a default opener reaching the proxy.
- **The stubs move:** every `urllib.request.urlopen` stub the *Context* lists patches `client.OPENER`'s `open`
  instead, through one helper in `tests/fakes.py` that accepts `timeout`. The guards in `tests/test_sheet_stage.py`
  and `tests/test_pipeline_cli.py` stub it too, so they still prove nothing is reached.

### D2

**Every request times out at 60 s.** `TIMEOUT = 60` in `client.py`. A `TimeoutError`, or a `URLError` whose reason
is one, is caught before the generic `OSError` branch and refused transient:
`the endpoint did not answer within 60 s; check the pod's ComfyUI log`. Bound to
`comfy-transport:timeout:an-unanswered-request-is-transient`.

### D3

**The poll gives up at 600 s.**

- **The deadline:** `RENDER_DEADLINE = 600` in `generate.py`; `render` takes `deadline: float = RENDER_DEADLINE`
  beside `poll`, and `_submit` measures it with `time.monotonic()`.
- **At the deadline** it raises `TransportFailure("transient", "prompt <id> did not finish within 600 s; check the
  pod's ComfyUI log")`, which `_recorded` records. Tests pass `deadline=0` with a `FakeComfyClient` whose history
  never completes.

- **The prompt id:** `submit` raises `ValueError` when `prompt_id` is not a non-empty string, which `_reported` turns
  into its permanent "shape this build does not read" refusal; `history` quotes the id into its URL with
  `parse.quote(prompt_id, safe="")`.
- **Keys:** `comfy-transport:polling:an-unfinished-prompt-is-refused-at-the-deadline` and
  `comfy-transport:polling:a-prompt-id-that-is-not-a-string-is-refused`.

### D4

**A boundary no part holds.** `build_multipart` takes `draw: Callable[[], str]`, defaulting to
`"isekai-" + secrets.token_hex(16)`, and draws again while any field value or file's bytes contain the boundary.
Every name, field name and filename has `"` → `%22`, CR → `%0D`, LF → `%0A` (RFC 7578 §4.2). Before → after, in
shape:

```
before:  Content-Disposition: form-data; name="image"; filename="a"b.png"
after:   Content-Disposition: form-data; name="image"; filename="a%22b.png"
```

`tests/test_multipart.py` keeps its existing tests, which read the boundary from the content type, and gains
`comfy-transport:multipart:the-boundary-appears-in-no-part` (a `draw` whose first value is inside the file's bytes)
and `comfy-transport:multipart:names-are-escaped`.

### D5

**Printable only.** `_error_body` keeps `"".join(c for c in text if c.isprintable())` before truncating to
`ERROR_BODY_CHARS`. Bound to `comfy-transport:error-text:control-characters-are-dropped`: a 400 whose body holds
`\x1b[31m` and `\x07` yields a refusal and a record without them.

### D6

**The surface refuses damage by name.** Each read in `app.py` checks its keys with `artifacts.require` and each
entry's shape, and refuses naming the file and its fix — the command that rewrites it, or for an approved sheet,
which no command rewrites, the file to restore:

| file | read in | remedy it names |
|---|---|---|
| draft | `read_input` | `python -m isekai review --flow <flow> --new-version <id>` |
| approved sheet | `read_input` | `restore it in <approved path> by hand, then reload the page` |
| caption | `read_input` | `python -m isekai caption --flow <flow> --new-version <id>` |
| WD14 list, hosted tag list | `_wd14`, `_tags` | `python -m isekai tag --flow <flow> --new-version <id>` |

Each command names `--runs <root>`, shell-quoted, whenever the run's root is not the default `.data/runs`, so the
pasted fix reaches the run the surface serves.

`put_draft` checks its body before the lock: `fields` is an object, each value a list, each tag a string; otherwise
it refuses with `the update's <field> is not a list of tags`, and nothing is written. Keys:
`ui:damage:a-damaged-file-is-refused-by-name` and `ui:damage:a-malformed-update-is-refused-naming-the-field`.

### D7

**A plain photograph name.**

- **`Run.photo`** checks the frame with `require` — `photo` an object, `name` a string — and refuses a name that is
  empty, `.`, `..`, or holds `/` or `\`. The refusal names `run.json` and its existing remedy: `delete <frame>, then
  offer the photograph again by its path`.
- **`_run_for`** checks `photo` and `sha256` the same way.
- **Every caller** already lets a `Refusal` reach `across`, so one run is refused and the batch goes on.
- **Keys:** `run-directory:frame:a-name-that-leaves-the-run-is-refused` and
  `run-directory:frame:a-frame-without-its-photograph-is-refused`.

### D8

**The watchdog polls.** In `infra/render.sh`, before → after:

```
before:  sleep "$CEILING" </dev/null >/dev/null 2>&1
after:   end=$((SECONDS + CEILING))
         while [ "$SECONDS" -lt "$end" ]; do
           kill -0 $$ 2>/dev/null || exit 0
           sleep 5 </dev/null >/dev/null 2>&1
         done
         kill -0 $$ 2>/dev/null || exit 0
```

The refusal line, `kill -TERM $$`, `pkill -TERM -P $$` and `kill "$watchdog"` stay as they are.
`tests/test_infra.py`'s `unbounded_session` checks for `end=$((SECONDS + CEILING))` in place of `sleep "$CEILING"`,
with the same order: after the trap, before the pod. A new test, bound to
`pod-image:session:the-watchdog-ends-with-its-session`, checks that `kill -0 $$ 2>/dev/null || exit 0` comes before
`kill -TERM $$` inside the watchdog, with a twin.

### D9

**A per-session known-hosts file.** `known_hosts=$(mktemp)` beside `up_out`; `open_tunnel` adds
`-o UserKnownHostsFile="$known_hosts"` and keeps `StrictHostKeyChecking=accept-new`; `teardown` removes it with
`up_out`. The comment says the key is trusted for this session alone. A new test, bound to
`pod-image:session:host-keys-are-the-sessions-own`, checks the ssh line and the teardown's `rm`, with a twin.

### D10

**One metered session proves it.**

- **The run:** on a synthetic portrait in `.data/v0.26/photos/`, with `http_proxy=http://127.0.0.1:9` exported and
  `https_proxy` unset, the operator runs the `run-flows` skill over both flows. RunPod's API is HTTPS, so it is
  untouched; the script's own checks ignore the proxy per [D11](#d11).
- **What it proves:** renders arriving prove the proxy ignored, the new multipart body accepted and the tunnel
  opened through the session's own known hosts.
- **The record:** `acceptance.md` holds the renders, the log's refusals, and the RunPod MCP confirming no pod.
- **The spend:** ceiling 45 minutes and ~$0.30; planned at ~$0.10.

### D11

**The script's checks ignore a proxy.** Every `curl` in `infra/render.sh` that names `$SERVER` — the port check
(`:45`) and the wait loop (`:108`) — gains `--noproxy '*'`, keeping its `--max-time`. A new test, bound to
`pod-image:session:the-tunnel-is-reached-directly`, checks that every such line carries it, with a twin.

## Dependencies

None.

## Risks / Trade-offs

- **A slow first render trips the 600 s deadline** → the first render pays the model load, about a minute; 600 s is
  ten times that.
- **A slow upload trips the 60 s timeout** → the timeout is per socket operation, not per request, and a photograph
  moves in seconds through the tunnel.
- **Moving the stubs weakens a test** → each moved stub keeps its assertion; the guards stub the opener as well as
  `urlopen`.
- **The watchdog's 5 s poll leaves a PID-reuse window** → 5 s against 44 minutes today.

## Verdict

**feasible** — local fixes at each boundary, each with a scenario and a test that fails before the build.
