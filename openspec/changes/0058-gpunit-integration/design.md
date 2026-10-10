# Design — 0058 gpunit integration

How isekai's render session moves onto gpunit: one verb in Python, one seam to gpunit, a pod that boots gpunit's
script, the specs mapped key by key, and a build record before the one metered proof.
**Verdict: feasible** — gpunit `v0.2.0` already does the lifecycle in-process; isekai keeps what is its own.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `d865baa` (`v0.34.2`); gpunit at `v0.2.0`:

- **The session today:** `infra/render.sh` parses `<runs> <flow>=<count|source>…`, orders a source before its
  dependents (`:31-53`), assembles every prompt with `isekai generate` and checks the sources (`:76-87`), starts a
  2640 s watchdog before `up.sh` (`:117-134`), parses `up.sh`'s `Tunnel:` line, waits 300 s for `/system_stats`
  (`:159-167`), renders each flow with `isekai generate --server` (`:169-176`), and appends everything to
  `<runs>/../log.txt` (`:22-29`).
- **The provenance:** `_generate` reads `booted_image()` (`isekai/interface/cli.py:709`), which reads
  `.runpod_pod_image` (`isekai/interface/wiring.py:44-56`). `Wiring` carries `client`, `rng`, `out`, `err`
  (`:93-109`).
- **The entry point imports no third-party package at module scope** (D20, `tests/test_pipeline_cli.py`'s `-S`
  guard); `RUNTIME_STACK` lists what a run reaches (`tests/test_packaging.py:24-30`).
- **`start.sh`:** steps 1–3 are the stop timer and trap, the authorized key, sshd and `isekai host key:` (`:9-32`);
  `hold()` ends in `exec bash "$STOP_POD"` (`:48-53`); the volume check reads `RUNPOD_VOLUME_ID` (`:100-104`) and
  `/runpod-volume` (`:38`); `export -n RUNPOD_API_KEY` (`:202`); ComfyUI runs as a child (`:209`).
- **The `Dockerfile`:** copies `start.sh`, `tools/download_models.sh`, `tools/stop_pod.sh`, `config/models.json`,
  `isekai/boundary/provision.py` (`:81-86`); `CMD ["/start.sh"]`, no `ENTRYPOINT` (`:90`).
- **`config/image.json`:** `image`, `tag` `v0.30-rc2`, `digest`. `build-image.yml` writes only the digest to its
  summary (`:57-62`).
- **`.env`:** `RUNPOD_API_KEY`, `RUNPOD_VOLUME_ID`, `RUNPOD_GPU_TYPE`, `RUNPOD_DATACENTER`. The cards in use:
  `NVIDIA RTX PRO 4500 Blackwell`, `NVIDIA L4`, `NVIDIA GeForce RTX 4090`, `NVIDIA A40`,
  `NVIDIA RTX PRO 6000 Blackwell Workstation Edition`.
- **The tests that read the scripts** sit in `tests/test_infra.py`, grouped by the files they read; the scripts are
  also named by `tests/test_docs.py` (`ROOTS`), `tests/test_spec_prose.py` (`_COMMENT_TREES`),
  `tests/test_resume.py:621`, `tests/test_generate.py:916`, `:1212`, `:1645-1673`, `:1855`, `:1932`,
  `tests/test_package_paths.py:56`, `tests/conftest.py:55`, `tests/fakes.py:130`, and `docs/principles.md`'s
  *Held by*, which `tests/test_principles.py` checks.
- **gpunit `v0.2.0`:** `gpunit.session(spec, environ=, cwd=, say=)` yields `host`, `port(remote)`, `ssh`, `image`,
  `pod_id`; raises `Refused`, `Lost`, `TeardownFailed`, `Interrupted`; owns the signals while open; the pod is told
  `GPUNIT_VOLUME_ID` and `GPUNIT_VOLUME_PATH`; `boot.sh` runs its command without `RUNPOD_API_KEY`.

## Goals / Non-Goals

**Goals:** the session in tested Python over gpunit; no provider name in isekai's code; the privacy the pod gives
unchanged; one metered proof.

**Non-Goals:** the pod's start in Python; a second provider; any change to a flow, a render, the review or the UI.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `isekai render` in `isekai/interface/render.py`, registered in `cli.py`; the same arguments, ordering, pre-pod pass and log as `render.sh` | the session's logic under unit test | keeping `render.sh` |
| [D2](#d2) | `isekai/boundary/gpu.py`: `read_env(path)`, `open_session(…)`; `gpunit` imported only inside `open_session` | one seam to fake; D20's import guard | `import gpunit` in the CLI |
| [D3](#d3) | the watchdog a `threading.Timer` started before the session opens, `SIGTERM` to this process | it counts from before the pod, as today; gpunit turns the signal into a teardown | a watchdog inside the session |
| [D4](#d4) | the flows run in-process through `dispatch`, with a `Wiring` whose `out` and `err` also append to the batch log | one process; the log as `render.sh` kept it | a subprocess per flow |
| [D5](#d5) | `Wiring.image` set from `s.image`; `_generate` reads it; `booted_image` and `POD_IMAGE` deleted | the session is what booted; gpunit's state file is private | reading `.gpunit/pod` |
| [D6](#d6) | `gpunit.toml` committed; `.env` down to the key; the volume id may be committed | the pin, the cards and the ceiling reviewable | a gitignored spec |
| [D7](#d7) | `boot.sh` the `ENTRYPOINT`; `start.sh` steps 1–3 out, `GPUNIT_VOLUME_*`, `exit 1` after a hold, `exec` ComfyUI | gpunit is the stop, the key and sshd | keeping `start.sh`'s own stop |
| [D8](#d8) | the scripts and their tests deleted once the verb and the pod stand; their keys REMOVED or rebound | the tests read text that no longer exists | keeping dead tests |
| [D9](#d9) | the decisions, principles, pins guide, README, `CLAUDE.md`, run-flows skill and remedies say gpunit | a decision in force is edited where it lives | — |
| [D10](#d10) | `config/image.json` records a SHA-256 per copied file; `tools/image_record.py` prints it for the workflow and the test | the image's drift from the tree becomes a red test (`0033·R6`) | a build commit field |
| [D11](#d11) | the last phase is HUMAN · METERED: build `v0.35-rc1`, check the record, re-pin, one render session | only a pod proves the pod | — |

### D1

`python -m isekai render <runs> <flow>=<count|source> …` keeps `render.sh`'s argument shape, its refusals and their
words, its source-before-dependent order, and its log at `<runs>/../log.txt`.

```
parse ─▶ order ─▶ pre-pod pass (assemble, sources) ─▶ busy port 8188?
   ─▶ watchdog ─▶ with open_session(...) as s:
                     await s.port(8188), 300 s ─▶ each flow: dispatch(generate --server)
   ─▶ cancel watchdog ─▶ exit: 0 · 1 a flow failed or refused · 3 Lost · 128+n Interrupted
```

`TeardownFailed` exits `1` with a refusal naming `uv run --env-file .env gpunit down`, since gpunit's CLI reads
no `.env`. Refusals are `refused: …` lines.

### D2

`gpu.py` holds `read_env(path) -> dict[str, str]` — `KEY=VALUE` lines, quotes stripped, comments and blanks skipped
— and `open_session(cwd, environ, say)`, which imports `gpunit` and returns `gpunit.session(cwd / "gpunit.toml",
environ=environ, cwd=cwd, say=say)`. `render` passes `os.environ | read_env(REPOSITORY / ".env")`, so isekai names
no provider variable. `render` takes `open_session` as a parameter; its tests pass a fake that yields a session with
`port`, `image` and `host`, and raises gpunit's exceptions.

### D3

`threading.Timer(CEILING_S, …)` with `CEILING_S = 2640`, started just before `open_session`. It appends
`refused: the session reached its 2640s ceiling; …` to the log and sends `SIGTERM` to this process. Inside the block
gpunit raises `Interrupted(15)` and tears down. The timer is cancelled in a `finally`.

### D4

For each flow, `render` builds `generate`'s arguments with `build_parser()` — `--flow`, `--count` or
`--seeds-from`, `--server http://127.0.0.1:<s.port(8188)>`, `--runs`, the run ids — and calls `dispatch` with a
`Wiring` from `wiring(args)` whose `out` and `err` write to the terminal and the batch log, and whose `image` is
`s.image`. The endpoint wait polls `read_runtime` through that wiring's client, which ignores proxies.

### D5

`Wiring` gains `image: str | None = None`. `_generate` reads `wired.image`. `booted_image`, `POD_IMAGE`, their
anchor in `tests/test_package_paths.py` and their patch in `tests/conftest.py` go. A `generate --server` outside
`render` records no image and declares itself unpinned.

### D6

```toml
project = "isekai"
image = "ghcr.io/alxb1t/isekai@sha256:<config/image.json's digest>"
gpus = [<the cards in Context, in that order>]
vram_gb = 24
ram_gb = 24
cuda = "12.8"
disk_gb = 30
ports = [8188]
ceiling = "45m"
timeout = 420
volume = "<.env's RUNPOD_VOLUME_ID>"
```

`.env.example` keeps `RUNPOD_API_KEY` alone. `CLAUDE.md`'s *Guardrails* no longer lists the volume id as a secret,
and names `.gpunit/` in place of the `.runpod_*` files. `.gitignore` adds `.gpunit/` and drops `.runpod_*`.
`pyproject.toml` adds `gpunit @ git+https://github.com/alxb1t/gpunit@v0.2.0` to `dependencies`, and
`RUNTIME_STACK` names it.

### D7

`Dockerfile`: `ADD --checksum=sha256:<boot.sh at v0.2.0> https://raw.githubusercontent.com/alxb1t/gpunit/v0.2.0/
boot/boot.sh /opt/gpunit/boot.sh`, `ENTRYPOINT ["/opt/gpunit/boot.sh", "--"]`, `CMD ["/start.sh"]`; the
`stop_pod.sh` copy and `chmod` go. `start.sh`: steps 1–3 and `STOP_POD` go; `MODELS_NAMESPACE` is
`"$GPUNIT_VOLUME_PATH/isekai"`; the volume check reads `GPUNIT_VOLUME_ID`; `hold()` sleeps, then `exit 1`;
`export -n RUNPOD_API_KEY` goes; ComfyUI starts as `exec python main.py …`.

### D8

The tests of `tests/test_infra.py` that read `up.sh`, `down.sh`, `pods.sh`, `render.sh` or `stop_pod.sh` go, with
their twins and helpers. The `start.sh` and `Dockerfile` tests are rewritten for [D7](#d7).

| scenario key | where it is held after this change |
|---|---|
| `pod-image:boot:the-pinned-digest-is-booted` | a test reading `gpunit.toml` and `config/image.json` |
| `pod-image:boot:no-override`, `…:the-booted-image-is-recorded` | `tests/test_render.py` |
| `pod-image:boot:each-step-is-timestamped` | `start.sh`'s steps, `BOOT_STEPS` without steps 1–3 |
| `pod-image:session:*` | `tests/test_render.py` |
| `pod-image:host-key:the-image-carries-none` | unchanged |
| `pod-image:host-key:each-boot-makes-and-prints-one` | the `Dockerfile`'s `ENTRYPOINT` and `ADD`, at `pyproject.toml`'s gpunit tag |
| `pod-image:memory:*`, `…:render-metadata:none-is-written` | unchanged; `serve_command` reads the `exec` line |
| `pod-image:telemetry:the-switches-are-off` | the `Dockerfile`, and `gpunit.toml`'s `[env]` |
| `pod-image:placement:the-create-carries-the-floors` | a test reading `gpunit.toml` |
| `pod-image:placement:{a-card-short…, an-unknown-card…}` | gpunit's `session:place:*` |
| `pod-image:host-key:{a-matching-key…, a-mismatch…, no-fingerprint…, a-scan…}` | gpunit's `session:hostkey:*` |
| `pod-image:volume:*` | gpunit's `session:volume:*`; the pod's floor |
| `pod-image:reconcile:*` | gpunit's `session:one:*`, `session:down:*`, `session:lost:*`, `library:*` |
| `pod-image:stop:armed-at-boot` | `gpunit.toml`'s ceiling and the `ENTRYPOINT` |
| `pod-image:stop:{a-hold-ends…, a-boot-that-ends…}` | `start.sh` run with stubs |
| `pod-image:stop:{a-failed-stop…, comfyui-holds-no-key}` | gpunit's `boot:stop:retries`, `boot:child:no-key` |
| `model-provisioning:reachability:*` | `start.sh` tests, `GPUNIT_VOLUME_*`; `gpunit.toml` names the volume |

### D9

- `docs/decisions.md`: D27 — gpunit pins the data centre, the size check is the pod's floor; D28 — `gpunit.toml`
  pins, a pod is made only by `isekai render` through gpunit; D35 — `boot.sh` holds the stop key, readable from
  its `/proc`; D36 — *A render session is `isekai render`*: the three bounds are the watchdog, the pod's own stop and
  gpunit's listing.
- `docs/principles.md`: *Held by* lists repointed to the tests that now hold them; the host-key bullets cite
  gpunit's `session:hostkey:*`.
- `docs/pins.md`: the pod image row — `gpunit.toml` pins, `config/image.json` records; *Re-pinning* names both.
- `README.md`: the lifecycle, ④–⑦, the layout, the provisioning flow; `isekai render` the one way onto a pod.
- `CLAUDE.md`: the metered protocol — `isekai render` creates through gpunit, the session tears down, the MCP
  confirms no `gpunit-isekai` pod, `uv run --env-file .env gpunit down` and `.gpunit/` replace `down.sh` and
  `.runpod_*`.
- `.claude/skills/run-flows/SKILL.md`: `uv run python -m isekai render`, `refused:` counted anywhere on a line,
  `gpunit-isekai`.
- The remedies: `isekai/boundary/comfy/client.py:145`, `isekai/pipeline/generate.py:330`, `:379`,
  `evaluation/record.py:20`, `evaluation/README.md:36`, `:44` name `isekai render`.

### D10

`tools/image_record.py` reads the `Dockerfile`'s `COPY` sources and prints `{"Dockerfile": sha256, <source>:
sha256, …}`. `config/image.json` gains `"files"` holding that object. `build-image.yml` runs it from its checkout and
writes it to the summary. A test fails when `"files"` differs from what the tool prints on the tree.

### D11

The operator pushes the branch, dispatches `build-image.yml` with tag `v0.35-rc1`, checks the summary's files
equal `config/image.json`'s, writes the tag and digest into `config/image.json` and `gpunit.toml`, renders one flow
on a small batch with `uv run python -m isekai render`, and confirms through the RunPod MCP that no
`gpunit-isekai` pod is left.

## Dependencies

- `gpunit @ git+https://github.com/alxb1t/gpunit@v0.2.0` — runtime: `isekai render`'s GPU session. Stdlib only;
  nothing transitive. Approved in the grilling.

## Risks / Trade-offs

- **A copied file edited after the record** → the record's test goes red; the image must be rebuilt and
  re-recorded. That is the guard's purpose.
- **The scripts deleted before the proof** → git keeps them; the metered phase is the proof, and it is last.
- **The cut's gpunit pin pins an image that cannot boot under gpunit** → nothing renders before the last phase
  re-pins.
- **gpunit's signal handlers replace isekai's during the session** → isekai sets none of its own.

## Verdict

Feasible. The lifecycle is gpunit's; isekai's part is a verb, a seam, a trimmed `start.sh`, and the specs and docs
that name them.
