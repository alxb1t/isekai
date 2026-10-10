# Design — 0059 the pod in Python

How the last bash becomes tested Python without moving the pod's privacy: the start module, `fetch`, the memory
step, the browser check, the parity table, and the proof on a pod. **Verdict: feasible** — every step already has a
spec and a test; the work runs each step instead of reading it.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `4a53e8b` (`v0.35.0`):

- **`start.sh`** (185 lines): `MODELS_NAMESPACE="${GPUNIT_VOLUME_PATH:-}/isekai"` (`:16`); `hold()` sleeps 900 s
  then `exit 1` (`:26-31`); `FAILURE_MARKER` (`:36`); the 40 GiB `VOLUME_SIZE_FLOOR_KIB` (`:61`) and 1 GiB
  `SHM_FREE_FLOOR_KIB` (`:65`); `provision()` — the `GPUNIT_VOLUME_*` check, the capacity floor, the guarded swap
  of `/opt/ComfyUI/models` for a symlink, `download_models.sh` (`:76-130`); the guarded call and its hold
  (`:141-150`); the `/dev/shm` directories, `TMPDIR`, `stat -f`, `df` and their holds (`:153-175`); `exec python
  main.py` with the `/dev/shm` directories and `--disable-metadata` (`:179-185`).
- **`tools/download_models.sh`** (90 lines): `plan`, then `wget` per source into `.partial`, then `land`, the next
  source on a failure (`:39-88`); `MODELS_DIR` defaults to `./models` (`:34`).
- **`provision.py`:** `decide`, `land`, `plan` (`:349`, `:405`, `:425`); `main` matches `plan` and `land`
  (`:494-517`); the `Fetcher` seam does HEADs (`:150`); `VOLUME_MOUNT` and `MODELS_NAMESPACE` (`:627-628`),
  imported by `tests/test_infra.py:21-23`.
- **The remedies:** `isekai/shared/vocabulary.py:40`, `isekai/boundary/ollama.py:103`, the docstring at
  `provision.py:488`; asserted by `tests/test_caption.py:567`, `tests/test_vocabulary_manifest.py:254`, and
  `DRIVER_PATH` at `tests/test_vocabulary_manifest.py:55`; named at `tests/test_resume.py:395`.
- **`tools/typecheck_ui.sh`**, run by `Makefile:17`.
- **The `Dockerfile`:** `wget` among the apt packages (`:17`); copies `start.sh`, `tools/download_models.sh`,
  `config/models.json`, `isekai/boundary/provision.py` (`:81-84`); `ENTRYPOINT` gpunit's boot script (`:95`),
  `CMD ["/start.sh"]` (`:96`).
- **`tools/image_record.py`:** `COPY` matches one source and one destination, skipping any other form (`:22`).
- **The privacy tests** in `tests/test_infra.py`: `test_comfyui_writes_to_memory` (`:1099`),
  `test_too_little_memory_holds_the_pod` (`:1141`), `test_comfyui_spools_uploads_to_memory` (`:1195`),
  `test_a_shm_that_is_not_memory_holds_the_pod` (`:1248`), `test_an_unread_figure_holds_the_pod` (`:1270`),
  `test_comfyui_writes_no_metadata` (`:1292`); named by `docs/principles.md:286-290`.
- **After phase 5:** `HuggingFaceFetcher.get` makes one `urlopen` with a 60 s timeout, and `_transfer` moves to the
  next source on any `OSError` (`provision.py:226`, `:478`). `wget` retried a broken transfer. Three entries of
  1 GB or more in `config/models.json` have one source.

## Goals / Non-Goals

**Goals:** no tracked `.sh` file; every pod step run under test; the privacy keys held unchanged; one metered proof
that reads the pod.

**Non-Goals:** a change to gpunit, a flow, a render, the review or the UI; a new requirement.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `pod_start.py`, stdlib only, beside `provision.py`; `CMD ["python", "/opt/isekai/isekai/boundary/pod_start.py"]` | one module per step, each run in a test | a bash wrapper |
| [D2](#d2) | `pod_start` provisions by `subprocess.run([sys.executable, <provision.py>, "fetch", "--models-dir", …])` | one CLI on the laptop and the pod | importing `provision` |
| [D3](#d3) | `provision.py fetch [--models-dir DIR] [manifest]`: plan, `urllib` transfer, land, next source; `plan` and `land` verbs gone | the transfer was all the bash did | keeping `wget` |
| [D4](#d4) | the type from `/proc/mounts`; free from `os.statvfs`; swap from `/proc/swaps` and `memory.swap.max`, printed only | the stdlib reads no filesystem type | holding for swap |
| [D5](#d5) | `tools/typecheck_ui.py`, its refusals word for word | the gate's last bash | — |
| [D6](#d6) | each privacy key held by a test of `pod_start`; the parity table below | the same guarantees, proven by behaviour | dropping a key |
| [D7](#d7) | the riding cards, each in the phase that opens its file | their triggers fire here | a separate patch |
| [D8](#d8) | a metered phase builds, re-pins, reads the pod over `gpunit ssh`, renders once | only the pod shows what it gets | trusting the tests alone |
| [D9](#d9) | `fetch` tries a broken transfer again from the same source, three attempts, 10 s then 30 s apart; phase 7 rebuilds as `v0.35.1-rc3` | `wget` retried, and an entry with one source has nowhere to fall | resuming with `Range`; a cold-volume proof |

### D1

```
main() ─▶ step "the volume"       GPUNIT_VOLUME_ID, GPUNIT_VOLUME_PATH set; statvfs total ≥ 40 GiB
       ─▶ step "the namespace"    mkdir <path>/isekai; a non-empty mounted models tree refuses; else symlink
       ─▶ step "provisioning"     fetch (D2)
       ─▶ step "the memory"       /dev/shm dirs, TMPDIR, type, free ≥ 1 GiB, swap reported (D4)
       ─▶ step "ComfyUI"          os.execvpe("python", [main.py, … /dev/shm dirs …, --disable-metadata], env)
any step's failure ─▶ marker (provisioning only) ─▶ hold: print why, sleep 900 s, exit 1
```

Each step prints `<UTC> step: <name>`. The paths, floors and the exec are module constants or parameters, so a test
points them at a temporary tree and replaces `os.execvpe`, `time.sleep`, `os.statvfs` and `subprocess.run`. The
marker stays `/opt/isekai/provisioning-failed`, off the volume.

### D2

`pod_start` runs `<its own directory>/provision.py fetch --models-dir /opt/ComfyUI/models`, every path absolute. A
non-zero exit is a provisioning failure.

### D3

`fetch` reuses `decide` and `land`. For a `FETCH` it opens each source with `urllib`, through the `Fetcher` seam
widened by `get(url, into)`, streams to `<target>.partial`, and lands it; a transfer that fails or bytes that do not
verify move to the next source; every source exhausted exits `1`. `--models-dir` defaults to the repository's
`models/`. `main` is argparse with `fetch` alone. The remedies become `uv run python -m isekai.boundary.provision
fetch config/vocabulary.json` and `… fetch config/reader.json`. `wget` leaves the `Dockerfile`'s apt line.

### D4

`/dev/shm`'s type is the third field of its `/proc/mounts` line; no line, or an unreadable file, holds with "could
not read /dev/shm's filesystem type" (`0042·R5`). Free space is `f_bavail * f_frsize`. Swap is "the container can
swap" when `/proc/swaps` lists a device and the cgroup's `memory.swap.max` is not `0`, else "cannot"; it never holds.
D35 gains a sentence: the host's swap is part of the operator's boundary (`0042·S3`).

### D5

`tools/typecheck_ui.py` checks `shutil.which("npm")`, then `ui/node_modules/`, printing today's refusals, then runs
`npm run typecheck` in `ui/` and exits with its code. `Makefile:17` runs `uv run python -m tools.typecheck_ui`.

### D6

| today's test (`tests/test_infra.py`) | key | its successor (`tests/test_pod_start.py`) |
|---|---|---|
| `test_comfyui_writes_to_memory` | `pod-image:memory:comfyui-writes-to-memory` | the exec'd argv names the `/dev/shm` directories, made before it |
| `test_too_little_memory_holds_the_pod` | `pod-image:memory:too-little-memory-holds` | a `statvfs` under 1 GiB holds; no exec |
| `test_comfyui_spools_uploads_to_memory` | `pod-image:memory:uploads-spool-to-memory` | the exec'd env holds `TMPDIR=/dev/shm/comfyui/tmp`, made before it |
| `test_a_shm_that_is_not_memory_holds_the_pod` | `pod-image:memory:a-disk-backed-shm-holds` | a `/proc/mounts` naming `ext4` holds; no exec |
| `test_an_unread_figure_holds_the_pod` | `pod-image:memory:an-unread-figure-holds` | a failing `statvfs` holds; no exec |
| — | `pod-image:memory:an-unread-type-holds` | no `/dev/shm` line holds; no exec |
| — | `pod-image:memory:swap-is-reported` | both readings printed; exec either way |
| `test_comfyui_writes_no_metadata` | `pod-image:render-metadata:none-is-written` | the exec'd argv holds `--disable-metadata` |
| `test_each_boot_step_prints_a_utc_time_before_it_begins` | `pod-image:boot:each-step-is-timestamped` | every step prints a UTC line before it acts |
| the provisioning tests | `model-provisioning:reachability:*` | a failing `fetch`, namespace or volume holds, marks, exits `1`; nothing removed |
| `test_every_hold_ends_in_the_stop`, `test_a_boot_that_ends_stops_the_pod` | `pod-image:stop:*` | a hold exits `1` after its sleep; a clean run ends in the exec |

`docs/principles.md`'s *Held by* names the successors. The image tests of the `Dockerfile` — no baked host key,
telemetry, the boot script — stay.

### D7

- `0058·R9`: `pod_start` reads `GPUNIT_VOLUME_PATH` alone; `provision.py`'s `VOLUME_MOUNT` and `MODELS_NAMESPACE`
  go, with their imports in `tests/test_infra.py`.
- `0058·R4`: `tools/image_record.py` refuses a `COPY` line it cannot read — a flag, or more than one source —
  naming it.
- `0058·R3`: `docs/pins.md`'s pod image recipe says an edit to a copied file needs a rebuild, then a re-record.
- `0058·R2`: the seeds-from diagram (the delta) and `tests/test_docs.py:50`'s docstring name `isekai render`.
- `0058·R8`: `.github/workflows/build-image.yml:5`'s comment cites no change.

### D8

A **HUMAN · METERED** phase. Push the branch; dispatch `build-image.yml` with tag `v0.35.1-rc2`; check the
summary's files equal `config/image.json`'s; re-pin `config/image.json` and `gpunit.toml`. Run `isekai render` on a
small batch, and while the session is open, from a second terminal, `uv run gpunit ssh` to read: ComfyUI's command
line, `/dev/shm`'s type, `TMPDIR` in ComfyUI's environment, and after the render `/opt/ComfyUI/output` empty. On the
laptop, read the saved PNG's chunks: no `tEXt`, `iTXt` or `zTXt`. Write the readings to
`.minions/0059_pod_proof.txt`. Confirm through the RunPod MCP that no `gpunit-isekai` pod is left. Phase 7
repeats it on `v0.35.1-rc3` ([D9](#d9)).

### D9

`_transfer` tries each source up to `ATTEMPTS = 3` times. An `OSError` from `get` is a broken transfer: the partial
is removed, `fetch` waits — 10 s, then 30 s — and transfers from the same source again. A `DigestMismatch` is
permanent and moves to the next source at once. The wait is a parameter of `fetch`, defaulting to `time.sleep`, so a
test passes one that records instead of sleeping.

A retry starts from zero rather than resuming with a `Range` request: `land` verifies the whole file either way, and
a resume is a second path through the real `get` that only a live server tests. The most a source adds is two waits
and two 60 s stalls, under four minutes, inside the 45-minute ceiling.

`provision.py` is a file the image copies, so the fix needs a new image. Phase 7 builds `v0.35.1-rc3`, re-pins it,
and renders once on it, reading the pod as [D8](#d8) lists. That pod's volume is warm, so it runs no transfer; the
real `get` runs once on the laptop instead, landing `config/vocabulary.json` into an empty directory. The retry
itself is held offline, where a transfer can be broken on purpose.

## Dependencies

None.

## Risks / Trade-offs

- **`urllib` instead of `wget`** → no progress bar; `fetch` prints each file's start and end. No resume: a broken
  transfer starts again from zero ([D9](#d9)).
- **A retry on a pod is never seen live** → held by a test with a transfer that breaks; the laptop runs the real
  transfer once ([D9](#d9)).
- **The image's Python is 3.12; the laptop's is the project's** → `pod_start` and `provision` are stdlib only and
  pass the gate's `ty` and tests on the laptop's.
- **A copied file changes, so the record changes** → re-recorded in its phase; the human phase checks the build
  printed the same.

## Verdict

Feasible: each step is a function with a test, the transfer a seam, and the pod read once in the metered phase.
