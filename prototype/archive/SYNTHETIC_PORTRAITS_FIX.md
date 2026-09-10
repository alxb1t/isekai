# What needs fixing in `synthetic_portraits`

> **CLOSED 2026-09-10.** The image was rebuilt, the portraits generated, and they are now round 3's
> held-out set at `prototype/inputs/synthetic/`. Archived as the record of what was wrong and how it was
> found; nothing here is outstanding.

**Written 2026-09-09 from isekai's `v0.13_prototype` branch**, after an attempt to generate the twenty
portfolio portraits failed. Nothing here is an isekai problem; this note exists to be carried over to the
`synthetic_portraits` repository and acted on there.

**Context.** The goal was 40 renders (20 prompts × 2 seeds, per
`notes/portfolio/synthetic_prompts.md` §4) into `isekai/inputs/portfolio_preparation/`. **Zero were
produced.** One pod session, ~$0.20, torn down and confirmed empty.

---

## 1 · BLOCKING — the published image has no custom nodes

**The pod ran `ghcr.io/alxb1t/synthetic_portraits:latest` and its `custom_nodes/` is empty**, containing
only ComfyUI's own two stock files:

```
$ ls /opt/ComfyUI/custom_nodes/
__pycache__   example_node.py.example   websocket_image_save.py
```

So the render fails at submit:

```
ComfyExecutionError: {'type': 'invalid_prompt',
 'message': 'Cannot execute because node UltralyticsDetectorProvider does not exist.',
 'details': "Node ID '#12'"}
```

**The repository's own `Dockerfile` does install them** — lines 51–60 clone ComfyUI-Impact-Pack at
`429d0159ad429e64d2b3916e6e7be9c22d025c3c` and Impact-Subpack at
`50c7b71a6a224734cc9b21963c6d1926816a97f1`, which is where `UltralyticsDetectorProvider`, `FaceDetailer`
and `SAMLoader` come from.

**So the published `:latest` tag is stale relative to the Dockerfile.** The README says the hi-res pass
and FaceDetailer arrived in v0.2; the image on GHCR predates that, or a build published without them.

### The fix

Rebuild and push `ghcr.io/alxb1t/synthetic_portraits:latest` from the current `Dockerfile`. If the repo
has a GitHub Actions release workflow, re-running it is likely sufficient. **Verify the result before
booting a pod for real work** — see §3.

### Do not work around it by editing the graph

Both shipped graphs (`workflows/realvis-txt2img.json` and `realvis-txt2img-identity.json`) use the
FaceDetailer path, and `README.md` is explicit that it is what keeps a face antelopev2-detectable at full
height. **Slot 6 of the portfolio set is full-height by design** and is the case that needs it most.
Stripping FaceDetailer to make the graph run would silently break the one thing the downstream consumer
requires.

---

## 2 · NON-BLOCKING — `infra/up.sh` leaves an unusable pod billing

On 2026-09-08 and 09 RunPod repeatedly returned pods that reach `status: RUNNING` with **`runtime: null`,
`ssh.direct: null`, no `publicIp` and no `portMappings`** — only their SSH proxy, which is a restricted
shell that cannot carry a port forward. isekai lost roughly $0.26 to this before it was understood; the
full account is in isekai's `prototype/notes/FINDINGS.md` F31.

`synthetic_portraits/infra/up.sh` polls 60 × 5 s for a public IP and then **prints a warning and exits,
leaving the pod running and billing.** That is how a `synthetic-portraits` pod was found still billing on
2026-09-09 with no way in.

### Already applied on this machine, unreviewed

Two edits were made to `infra/up.sh` on `main` while attempting the run. **They are uncommitted and have
had no test beyond `bash -n`** — review them rather than trusting them:

1. **`"ports": ["22/tcp"]` → `["22/tcp", "8188/http"]`.** An HTTP-exposed port is served by RunPod's proxy
   at `https://<pod id>-8188.proxy.runpod.net` and needs **no public IP**, so it is reachable exactly when
   the tunnel is not.
2. **The no-IP branch now prints the proxy URL** and probes it, instead of only warning.

### But the proxy does not actually work for this client — see §4

### Worth adding, not done

A **bounded readiness deadline that tears the pod down itself** on timeout. isekai's `infra/up.sh` now
does this (180 s for the IP path, 420 s when waiting on the proxy, then `down.sh`), and it converted four
silent billing failures into three-minute ones. A bounded wait that leaves the meter running has not
solved the problem it was added for.

---

## 3 · A verification habit worth adopting — the node check that isn't one

**`GET /object_info/<NodeName>` returns HTTP 200 for nodes that do not exist.** Before the failed run,
`UltralyticsDetectorProvider`, `FaceDetailer` and `SAMLoader` were each probed that way and each returned
200 — on a pod where none of them existed. The probe proves nothing.

The real check fetches the **full** `/object_info` and looks for the key:

```bash
curl -s http://127.0.0.1:8188/object_info \
  | python3 -c 'import json,sys; d=json.load(sys.stdin);
    need=["UltralyticsDetectorProvider","FaceDetailer","SAMLoader"];
    missing=[n for n in need if n not in d];
    print("MISSING:", missing) if missing else print("all present of", len(d), "node types")'
```

Worth running as the first thing after ComfyUI answers, before any render is queued. It would have caught
this in five seconds instead of after a pod boot, a dependency install and two failed submissions.

---

## 4 · The RunPod HTTP proxy is blocked for stdlib clients

The proxy fallback in §2 **answers `curl` and rejects the Python client**:

```
curl  https://<pod>-8188.proxy.runpod.net/system_stats   →  HTTP 200
generate.py --server https://<pod>-8188...               →  ComfyExecutionError: error code: 1010
```

Cloudflare **1010** is a user-agent block. `synthetic_portraits`'s transport is stdlib `urllib`, which
sends `Python-urllib/3.x`, and Cloudflare refuses it. `curl` passes.

**This applies to isekai too** — its `ComfyTransport` is also stdlib `urllib` by design, and isekai's own
finding F33 claimed the proxy workaround "works" on the strength of a `curl` probe alone. **It was never
render-tested.** F33 is being amended.

**If the proxy is to be a real fallback, the transport must send a browser-like `User-Agent` header.**
That is one line in `urllib.request.Request(...)`, it does not add a dependency, and it should be
verified by an actual render rather than by a status probe. Until then, treat the proxy as a diagnostic
channel only and **rely on the SSH tunnel**.

---

## 5 · Minor — the portfolio run needs the `faces` group

`generate.py` constructs `default_face_detector()` unconditionally, so a run without the optional group
dies on `ModuleNotFoundError: No module named 'cv2'` **after** the pod is already up and billing. The
note in the vault mentions `uv sync --group faces` only for `scripts/check_face.py`.

Either document that the CLI needs it too, or fail early with a clear message before the pod is created.
`uv run --group faces python generate.py ...` is the working invocation.

---

## What to do, in order

1. **Rebuild and push the image.** §1. Nothing else can proceed.
2. **Verify with the full `/object_info` check.** §3. Five seconds, on the next pod, before rendering.
3. **Review the two uncommitted `up.sh` edits**, and consider adding the self-teardown deadline. §2.
4. **Decide on the `User-Agent` header** if the proxy is wanted as a real fallback. §4.
5. **Document the `faces` group** for the CLI, or fail early. §5.

Then the portfolio run is one short session:

```bash
uv run --group faces python generate.py \
  --prompts portfolio_prompts.txt --seed 42 -n 2 \
  --out <path to isekai>/prototype/inputs/synthetic \
  --server http://127.0.0.1:8188
```

`portfolio_prompts.txt` is already present in the repo with the twenty lines, untracked.
