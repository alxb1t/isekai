# Design — 0040 the pod image

How the image stops shipping host keys, how `start.sh` keeps ComfyUI's writing in memory, and how one rebuild and
one session prove it. **Verdict: feasible** — the image and the start script change, each held by a text test, and the pod proves
them.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`6a93516`):

- **`Dockerfile:8-11`** installs `openssh-server` in one `RUN`, which leaves `/etc/ssh/ssh_host_*` in that layer.
  `uv sync` (`:49`) runs after the node clones (`:22-37`).
- **`start.sh:17-20`**: `echo … step: sshd`, `mkdir -p /run/sshd`, `ssh-keygen -A` — which only makes missing keys —
  and `/usr/sbin/sshd`, with no `sshd_config` edit. ComfyUI starts at `:152` with `--listen 0.0.0.0 --port 8188`
  alone, after `echo … step: ComfyUI` at `:151`. The volume-floor comment at `:50-52` says the volume is 80 GB.
- **ComfyUI at the pin** takes `--input-directory`, `--output-directory`, `--temp-directory` (meaning `X/temp`),
  `--user-directory` (which must exist) and `--disable-metadata`. `LoadImage` lists its input directory, so it must
  exist before a prompt. ComfyUI logs "Setting input/output/temp directory to …" on stderr.
- **`tests/test_infra.py`** binds these files by text: the line before `mkdir -p /run/sshd` and before
  `exec python main.py` must hold `date -u` (`:680`); no `rm ` near the provisioning hold and the serve line (`:210`); no `\s-r\s` in the `Dockerfile` (`:638`); the pinned clones (`:389`); the
  timestamped-steps check (`:680`) names each step's first command.
- **The pin:** `config/image.json` holds `v0.24-rc1`; `build-image.yml` is dispatch-only and prints the digest in its
  summary.

## Goals / Non-Goals

**Goals:** no host key in the image; one per pod, printed; nothing ComfyUI writes on disk; no metadata in renders;
a proved new digest.

**Non-Goals:** the client's fingerprint check; `up.sh` and `render.sh`; the base image; hashed build tools.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | delete the keys in the install `RUN`; make an Ed25519 key at boot; `sshd` uses it alone; print the fingerprint line | a later layer would only hide the baked keys; one key type, one line to read | `ssh-keygen -A` — it makes every type |
| [D2](#d2) | input, output, temp and user under `/dev/shm/comfyui`; hold below 1 GB free | nothing ComfyUI writes reaches the disk; a clear hold beats a failed first save | a loader node and a websocket — settled against |
| [D3](#d3) | `--disable-metadata` | no saved image carries the prompt | stripping renders on the Mac |
| [D4](#d4) | `uv sync` after ComfyUI's clone, before the node clones | a node bump stops rebuilding torch; free on this rebuild | a separate rebuild later |
| [D5](#d5) | the operator builds `v0.28-rc1` on request | it publishes a public image | the agent dispatching it |
| [D6](#d6) | one metered `render.sh` session, the evidence from the pod's log and the renders | one boot proves the image, the directories, the metadata and the stripped upload | several sessions |

### D1

**The key is the pod's own.** In `Dockerfile:8-11`'s `RUN`, before the apt lists are removed:
`&& rm -f /etc/ssh/ssh_host_*`. In `start.sh`'s sshd step, after `mkdir -p /run/sshd`:

```
key=/etc/ssh/ssh_host_ed25519_key
[ -f "$key" ] || ssh-keygen -q -t ed25519 -N '' -f "$key"
/usr/sbin/sshd -o HostKey="$key"
echo "isekai host key: $(ssh-keygen -lf "$key.pub" | awk '{print $2}')"
```

The printed line's shape — `isekai host key: SHA256:<fingerprint>` — is the contract the client's check reads.

### D2

**ComfyUI writes to memory.** A new step before `echo … step: ComfyUI`, itself timestamped:

- **The directories:** `/dev/shm/comfyui/input`, `output`, `temp` and `user`, made with `mkdir -p`.
- **The size:** it prints `/dev/shm`'s size and free space. Under 1 GB free it prints why and holds with
  `exec sleep "$HOLD_SECONDS"`, as a failed provision does, and ComfyUI never starts.
- **The start line:** `--input-directory /dev/shm/comfyui/input --output-directory /dev/shm/comfyui/output
  --temp-directory /dev/shm/comfyui --user-directory /dev/shm/comfyui/user`, with `echo … step: ComfyUI` still the
  line before it.

`tests/test_infra.py`'s timestamped-steps check gains the new step's first command.

### D3

**No metadata.** The start line adds `--disable-metadata`.

### D4

**`uv sync` moves up.** The `COPY image/…`, the `ENV` lines and `RUN uv sync --locked` (`Dockerfile:39-49`) move to
after `WORKDIR /opt/ComfyUI` (`:25`), before the InstantID clone. The clones keep their order, so
`tools/derive_image_project.py` pairs them as before. The false 80 GB comment (`start.sh:50-52`) says what D27 says:
the volume is 20 GB and reports its cluster's capacity.

### D5

**The rc build is the operator's.** Push `v0.28_the_pod_image`, then
`gh workflow run build-image.yml --ref v0.28_the_pod_image -f tag=v0.28-rc1`; the job summary's digest goes into
`config/image.json` with the tag `v0.28-rc1`.

### D6

**One session proves it.**

- **The run:** `render.sh` over a synthetic portrait and a copy turned 90° and tagged orientation 6 — made once with
  Pillow — through both flows.
- **The pod's log**, read with the RunPod MCP's `stream-pod-logs` during the session: the new host key generated, the
  fingerprint line, `/dev/shm`'s size, and ComfyUI's directory lines naming `/dev/shm/comfyui`.
- **The renders:** the rotated copy renders upright, and no render carries a PNG text chunk.
- **The record:** `acceptance.md`, one line per piece of evidence, with no pod id, address or fingerprint value.
  Ceiling 45 minutes and ~$0.30; planned at ~$0.10.

## Dependencies

None.

## Risks / Trade-offs

- **`/dev/shm` is small on the pod** → the pod holds and says why; the session reports the real size.
- **`sshd` refuses `-o HostKey` with the stock config** → the session fails before any render; `bash -n` and the
  pod's log show it.
- **The rebuild pulls newer apt packages** → the session's render is the check, as for every rebuild.

## Verdict

**feasible** — text-tested edits to the image and the start script, proved on one pod.
