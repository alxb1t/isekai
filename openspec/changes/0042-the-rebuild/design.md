# Design — 0042 the rebuild

How one rebuild moves the image to a plain base, keeps the upload in memory, carries the telemetry switches, swaps
onnxruntime for the CPU package and checks the build tools by hash, and how one session proves it. **Verdict:
feasible** — text- and stub-tested edits to the image files, proved on one pod.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`ad27f67`):

- **`Dockerfile:3`** is `nvidia/cuda:12.4.1-devel-ubuntu22.04@sha256:da67…`; line 1's comment says "CUDA runtime".
  `:9-13` installs `git python3 python3-pip curl wget openssh-server libgl1 libglib2.0-0` with
  `--no-install-recommends`, and deletes the host keys in the same `RUN`. The only `ENV`s are `:5`, `:38-40` and `:73`.
- **The pinned image** is 9.06 GiB: the base's layers 3.83 GiB, of which the devel toolkit is 2.46 GiB; the
  `uv sync` layer 4.93 GiB — read from `v0.28-rc1`'s manifest on GHCR, the bases' sizes from Docker Hub's tag
  pages. torch 2.8.0+cu128's `nvidia-*` wheels bring every CUDA library torch loads. The old base set
  `NVIDIA_VISIBLE_DEVICES=all` and `NVIDIA_DRIVER_CAPABILITIES=compute,utility`, and installed `ca-certificates`.
- **Python on the pod** is uv's managed CPython 3.12.14 in `/opt/ComfyUI/.venv`, first on `PATH` (`:38-40`); the
  `python3` that `tools/download_models.sh:38` and `:70` call resolves there. apt's `python3` is unused.
- **insightface 0.7.3** is an sdist that compiles a C++ extension, so the build needs `g++`. Nothing compiles at
  runtime.
- **`image/pyproject.toml` is derived** by `tools/derive_image_project.py`: `PINS` (`:35-40`) win over upstream
  entries, `DROPPED = ("onnxruntime",)` (`:46`), and `BUILD_CONSTRAINTS` (`:49`) are rendered as plain strings
  (`:125`). comfyui_controlnet_aux's requirements name `onnxruntime-gpu`; no upstream names `onnxruntime`.
- **`onnxruntime-gpu` 1.30.0** (`image/uv.lock:1195`) is built for CUDA 13, which nothing in the image supplies, so
  it runs on the CPU after a warning. InstantID's face analysis asks for the CPU anyway. DWPose, in
  `summon-anime-wai` only, runs its box detector through it.
- **`start.sh`'s memory step** is `:158-173`: `mkdir -p` of the input, output, temp and user directories
  (`:161`), the `df` read (`:162`), an unreadable figure set to `free_kib=0` (`:165-167`), the floor's hold
  (`:168-173`). ComfyUI starts at `:178-184`. No `TMPDIR` is set.
- **`infra/up.sh:158-163`** sends the telemetry switches in the create's `env`, under the comment at `:143`.
- **`tests/test_infra.py`** binds these by text:
  - `baked_host_key_faults` (`:726-748`) finds the install layer as the `RUN` naming `openssh-server`, and faults any
    other line naming `openssh`, `ssh_host_` or `ssh-keygen`.
  - `boot_step` (`:780-785`) ends a step at its first blank line.
  - `memory_hold_faults` (`:874-894`) requires the `if [ "$free_kib" -lt "$SHM_FREE_FLOOR_KIB" ]; then` line and a
    `>&2` line before `exec sleep "$HOLD_SECONDS"`.
  - `:223` forbids `rm ` in `lines[hold - 6 : serve]`, from before the first hold to the serve line.
  - `BOOT_STEPS` (`:676-683`) and `unmade_directories` (`:843-852`) read the `mkdir -p` line.
  - `telemetry_left_on` (`:1591-1595`) parses `up.sh`'s `env:` block.
- **`docs/pins.md:42`** says "the sdist builds' tools by version"; *Not pinned* carries their row (`:92`).
  **`docs/principles.md:280-289`** lists the privacy principle's tests.
- **`CHANGELOG.md:56-57`**, 0.26.1's first bullet, omits the append-only exception `0038` D6 records.

## Goals / Non-Goals

**Goals:** a smaller pull; nothing of the photograph's on the container disk; `/dev/shm` proved memory; the
switches in the image; an honest onnxruntime; hashed build tools; a proved new digest.

**Non-Goals:** the pod's lifecycle; a builder stage; onnxruntime on the GPU; the rehash; the uv cache.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `ubuntu:22.04` by digest, one stage; `build-essential` and `ca-certificates` in place of apt's Python; the `NVIDIA_*` `ENV`s | ~3.6 GiB off the pull; torch brings its CUDA | the CUDA runtime base, ~1.2 GiB bigger; a builder stage, which copies uv's Python and the venv across for ~200 MB |
| [D2](#d2) | the memory step makes a `tmp` directory and exports `TMPDIR` to it; it holds on a `/dev/shm` that is not a tmpfs, and on an unreadable figure, naming each | the upload spools to `TMPDIR`; a guess is not a reading | setting `TMPDIR` in the `Dockerfile`, which would move every build step's temp files too |
| [D3](#d3) | the telemetry switches as `ENV` in the `Dockerfile`; `up.sh`'s `env` loses them | *declared once*; the image holds for every pod | a copy in each |
| [D4](#d4) | `onnxruntime==1.30.0` pinned in the deriver, `onnxruntime-gpu` dropped; DWPose's box detector moves to OpenCV, and the operator ruled the release a patch | the CPU is what runs; the package says so and is smaller | a CUDA 12 build of `onnxruntime-gpu` tied to torch's CUDA; restoring `onnxruntime-gpu` for DWPose; releasing as a minor |
| [D5](#d5) | the deriver renders each build constraint as a `{ requirement, hashes }` table | uv checks them under `uv sync --locked` | a hashed constraints file, which `uv sync` does not read |
| [D6](#d6) | 0.26.1's first bullet names the append-only exception and cites `0038` D6 | the open thread from `0038` | a new bullet |
| [D7](#d7) | the operator builds `v0.29.1-rc1` on request | it publishes a public image | the agent dispatching it |
| [D8](#d8) | one metered `render.sh` session; the evidence from the pod's own environment and log | one boot proves the image | a session for each piece of evidence |

### D1

**The base is plain Ubuntu.** `FROM ubuntu:22.04@sha256:<digest>`, the digest resolved with
`docker buildx imagetools inspect ubuntu:22.04` as `docs/pins.md` says. Line 1's comment says what the base is and why
it carries no CUDA. The install `RUN` stays the one line naming `openssh-server`:

```
git curl wget ca-certificates openssh-server build-essential libgl1 libglib2.0-0
```

`python3` and `python3-pip` go. A new `ENV NVIDIA_VISIBLE_DEVICES=all NVIDIA_DRIVER_CAPABILITIES=compute,utility`
follows `:5`, so the container runtime mounts the driver.

### D2

**The memory step also covers the temporary files, and holds on what it cannot trust.** In `start.sh`'s step, with no
blank line inside it and no word ending in `rm` before a space:

- **The directory:** the `mkdir -p` line gains `/dev/shm/comfyui/tmp`, and `export TMPDIR=/dev/shm/comfyui/tmp`
  follows it. `exec python main.py` inherits it; its line stays as it is.
- **The type:** `shm_type="$(stat -f -c %T /dev/shm)" || shm_type=''`, printed beside the size. Anything but `tmpfs`
  prints what it is to `>&2` and holds with `exec sleep "$HOLD_SECONDS"`.
- **The figure:** an empty or non-numeric `free_kib` prints "could not read /dev/shm's free space" to `>&2` and holds
  the same way, before the floor's `if`. `free_kib=0` goes.

### D3

**The switches are the image's.** After `D1`'s `ENV`:

```
ENV ORT_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_TELEMETRY=1 DO_NOT_TRACK=1 NO_ALBUMENTATIONS_UPDATE=1
```

`infra/up.sh`'s `env` keeps `PUBLIC_KEY` and `RUNPOD_VOLUME_ID`, and the comment at `:143` goes with the switches.
`telemetry_left_on` reads the `Dockerfile`'s `ENV` lines and `up.sh`, keeping its test's name, which
`docs/principles.md` cites.

### D4

**onnxruntime is the CPU package.** In `tools/derive_image_project.py`: `PINS` gains `onnxruntime==1.30.0`,
`DROPPED` becomes `("onnxruntime-gpu",)`, and the comment says why. `uv run python -m tools.derive_image_project`
rewrites `image/pyproject.toml` and `image/uv.lock`.

**What it moves.** The session showed that DWPose, finding no GPU provider, runs its box detector through OpenCV on
the CPU, where `onnxruntime-gpu` had run it through onnxruntime ([acceptance](acceptance.md)). DWPose is in
`summon-anime-wai` only, and its keypoints condition the pose, so this changes code that shapes that flow's render:
the same inputs may give a different image. `conjure-anime-wai` has no DWPose. The operator accepted OpenCV pending an
evaluation on more photographs.

**The operator's ruling, 2026-09-29: the release stays a patch, `v0.29.1`.** `CLAUDE.md`'s patch rule says nothing
changes the image for the same inputs; this move can, and the operator ruled it a patch all the same, choosing to
record the ruling here over releasing as a minor or restoring `onnxruntime-gpu` for DWPose. The operator gave no
further reason, and this design records none.

### D5

**The build tools are checked by hash.** `BUILD_CONSTRAINTS` becomes the requirements with their wheel hashes, which
`image/uv.lock` already holds:

| requirement | hash |
|---|---|
| `setuptools==84.0.0` | `sha256:51a52592b3b99e102b609654876bd65f19f999935166d1352678931132b0c670` |
| `numpy==2.5.3` | `sha256:b7e18c623bb5c95acb3b3328861272816ba199fb531921c5d6d0b675f1fde9e3` |
| `cython==3.3.0` | `sha256:428fafed98ea26927000a287b4dfc9ef07339f56656a5329a34eaa593f79a4f8`, `sha256:9b24b5c8cd536946b62086fcafee6d5509d3f549f72d553d2336af87ffbe0da1` |

`render` writes each as `{ requirement = "…", hashes = ["sha256:…"] }`. uv 0.12.16 and later records the hashes in
`uv.lock`'s `[manifest]` and fails a build tool that does not match. `docs/pins.md`'s row says "by hash", and its
*Not pinned* row goes.

### D6

**The open thread.** `CHANGELOG.md:56`: `- Every version rewritten terse: Keep a Changelog sections only, …` → `- Every
version rewritten terse, the one stated exception to append-only: Keep a Changelog sections only, …`, and its ids
gain `D6`. The bullet stays under `tests/test_changelog.py`'s 300 characters.

### D7

**The rc build is the operator's.** Push `v0.29.1_the_rebuild`, then
`gh workflow run build-image.yml --ref v0.29.1_the_rebuild -f tag=v0.29.1-rc1`; the job summary's digest goes into
`config/image.json` with the tag `v0.29.1-rc1`.

### D8

**One session proves it.**

- **The run:** `render.sh` over a synthetic portrait, through `summon-anime-wai` and `conjure-anime-wai`.
- **The pod's environment**, read over the `SSH:` line `up.sh` prints while the session runs:
  `tr '\0' '\n' < /proc/1/environ` holds `TMPDIR=/dev/shm/comfyui/tmp` and the telemetry switches.
- **The pod's log**, through the RunPod MCP's `stream-pod-logs`: `/dev/shm is tmpfs`, and the boot's timestamps,
  created → port 22, set beside 0033's 4 m 33 s.
- **The renders** arrive, and the MCP shows `pods: []` after.
- **The record:** `acceptance.md`, one line per piece of evidence, no pod id, address or fingerprint.
- **If the base fails** — torch finds no GPU, or a node cannot load — the old base returns in a follow-up commit, the
  operator builds `v0.29.1-rc2`, and a second session proves it.

Ceiling 45 minutes and ~$0.30 a session; planned at ~$0.10.

## Dependencies

- `onnxruntime` replaces `onnxruntime-gpu` in the image project, per [D4](#d4) — approved at the grilling.

## Risks / Trade-offs

- **torch cannot see the GPU on a plain base** → the metered session shows it before any render; D8's fallback.
- **An apt package the NVIDIA base brought is missing** → the build or the first boot fails loudly; the session is
  the check, as for every rebuild.
- **`stat -f` on `/dev/shm` prints another name for a tmpfs** → the pod holds and prints the name; the session shows
  it.
- **DWPose's box detector on OpenCV finds a different box than onnxruntime did** → `summon-anime-wai`'s pose, and so
  its image, can differ from `v0.28-rc1`'s for the same inputs; accepted pending an evaluation on more photographs,
  and ruled a patch by the operator ([D4](#d4)).
- **The re-derive moves other packages** — upstream is read at the pinned commits, so only onnxruntime's entries
  should move → `git diff --stat -- image/` is read at the task.

## Verdict

**feasible** — edits to the image files and the deriver, each held by a test, proved on one pod.

DWPose's move to OpenCV, found in the session, breaks the patch rule's same-image clause for `summon-anime-wai`; the
operator ruled on 2026-09-29 that the release stays a patch ([D4](#d4)).
