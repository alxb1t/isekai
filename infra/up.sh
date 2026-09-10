#!/usr/bin/env bash
# Bring up a RunPod GPU pod from our GHCR image with the models attached,
# then print the SSH + tunnel commands. Config comes from .env.

set -euo pipefail

cd "$(dirname "$0")/.."          # run from repo root no matter where invoked
set -a; source ./.env; set +a    # load RUNPOD_* config

PUBKEY="$(cat ~/.ssh/id_ed25519_runpod.pub)"

# `:latest` is the released image and the default. A metered phase that has to
# boot a branch's image before the branch is merged sets RUNPOD_IMAGE in .env
# instead — untracked, so the tag a pod runs is never a commit away from the tag
# a release means.
RUNPOD_IMAGE="${RUNPOD_IMAGE:-ghcr.io/alxb1t/isekai:latest}"

# The client half of the volume guard, and the half that is certain. The pod-side
# check cannot see whether a network volume was ever requested: RunPod defaults
# `volumeInGb` to 20 and mounts the pod's OWN volume disk at volumeMountPath when
# none is attached, so the mount point exists either way (design.md D5). Here the
# question is answerable and tripping it costs nothing, because no pod exists yet.
if [ -z "${RUNPOD_VOLUME_ID:-}" ]; then
  echo "ERROR: RUNPOD_VOLUME_ID is empty in .env — refusing to create a pod." >&2
  echo "Without the network volume, provisioning downloads 16.5 GiB onto storage" >&2
  echo "that dies at teardown: it renders correctly, bills fully, and is noticed" >&2
  echo "only on the next metered session." >&2
  exit 1
fi

echo "Creating pod in $RUNPOD_DATACENTER, first available of: $RUNPOD_GPU_TYPE"
echo "  image: $RUNPOD_IMAGE"
# RUNPOD_GPU_TYPE may be a comma-separated preference list. RunPod takes a list
# of acceptable types and places on whichever it can, so a single hardcoded GPU
# is a single point of failure -- which is exactly how it failed on 2026-09-08,
# when the volume moved to a datacenter the pinned Blackwell card is not in.
#
# **Every entry must work with the image's cu128 PyTorch.** cu128 covers sm_80
# through sm_120, so Ada and Ampere cards are fine; the constraint recorded in
# CLAUDE.md is that cu124 does NOT work on Blackwell, not that the image is
# Blackwell-only.
# Two ports, for two ways in.
#
#   22/tcp    the SSH tunnel this pipeline was built on.
#   8188/http the fallback RunPod support pointed at on 2026-09-09: an
#             HTTP-proxied port needs NO public IP and is reachable at
#             https://<pod id>-8188.proxy.runpod.net -- exactly the resource the
#             failing allocations never receive.
#
# The proxy is a PUBLIC endpoint. RunPod's own docs: "your service becomes
# publicly accessible", and "the Pod ID provides only obscurity, not security".
# ComfyUI has no auth, so for the pod's lifetime anyone holding the id can drive
# it. Acceptable only because sessions here are minutes long and torn down
# immediately; it is not a posture to leave running.
gpus=$(printf '%s' "$RUNPOD_GPU_TYPE" | jq -R 'split(",") | map(gsub("^\\s+|\\s+$";""))')

body=$(jq -n \
  --arg image  "$RUNPOD_IMAGE" \
  --argjson gpus "$gpus" \
  --arg vol    "$RUNPOD_VOLUME_ID" \
  --arg dc     "$RUNPOD_DATACENTER" \
  --arg pubkey "$PUBKEY" \
  '{ name: "isekai",
     imageName: $image,
     gpuTypeIds: $gpus,
     gpuCount: 1,
     networkVolumeId: $vol,
     volumeMountPath: "/runpod-volume",
     ports: ["22/tcp", "8188/http"],
     containerDiskInGb: 30,
     dataCenterIds: [$dc],
     cloudType: "SECURE",
     env: { PUBLIC_KEY: $pubkey,
            RUNPOD_VOLUME_ID: $vol } }')

resp=$(curl -s -X POST https://rest.runpod.io/v1/pods \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$body")

pod_id=$(echo "$resp" | jq -r '(if type=="array" then .[0] else . end).id // empty')

if [ -z "$pod_id" ]; then
  echo "Pod creation failed:"; echo "$resp" | jq . 2>/dev/null || echo "$resp"; exit 1
fi
echo "$pod_id" > .runpod_pod_id
echo "Pod $pod_id created. Waiting for direct SSH or the HTTP proxy ..."
proxy="https://${pod_id}-8188.proxy.runpod.net"

# Poll until the pod has a public IP and a mapped :22 -- and give up if it never
# arrives. Some SECURE-cloud machines come up `RUNNING` with `runtime: null` and
# only RunPod's SSH proxy, which is a restricted shell and will not carry the
# port forward this pipeline needs. The pod is then useless and bills anyway.
#
# This poll was originally unbounded, which made it the one thing in this
# repository that could bill indefinitely while looking like it was working. It
# cost two sessions on 2026-09-08 before it was noticed. On timeout the pod is
# **torn down here**, because a bounded wait that leaves the meter running has
# not solved the problem it was added for.
# 420s, not 180s. The IP check answers in seconds, but the proxy path cannot
# answer until the image has pulled AND ComfyUI has started -- observed at 2-4
# minutes together. A 180s deadline was right when we only waited for an IP and
# would now tear down healthy pods mid-boot. The cost of the longer wait is ~$0.05
# on a pod that never comes up; the cost of the shorter one is killing good pods.
deadline=$((SECONDS + 420))
while true; do
  pod=$(curl -s "https://rest.runpod.io/v1/pods?id=$pod_id" \
        -H "Authorization: Bearer $RUNPOD_API_KEY")
  ip=$(echo   "$pod" | jq -r '(if type=="array" then .[0] else . end).publicIp // empty')
  port=$(echo "$pod" | jq -r '(if type=="array" then .[0] else . end).portMappings."22" // empty')
  [ -n "$ip" ] && [ -n "$port" ] && break
  # The HTTP proxy needs no public IP, so it can come up when direct SSH never
  # will. Probed every cycle, and taken the moment it answers.
  # `--fail` matters: without it curl exits 0 on the proxy's own 502/503 while
  # ComfyUI is still starting, and the script would announce a pod that cannot
  # yet serve a render.
  if curl -sf -m 5 -o /dev/null "$proxy/system_stats"; then
    echo; echo "Pod is up -- via the HTTP proxy (no public IP was issued)."
    echo "  ComfyUI: $proxy"
    echo "  NOTE: that URL is PUBLIC and ComfyUI has no auth. Tear down promptly."
    exit 0
  fi
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo >&2
    echo "ERROR: pod $pod_id got neither a public IP nor a working HTTP proxy" >&2
    echo "within 180s. Tearing it down rather than billing for a pod we cannot" >&2
    echo "use. Re-run infra/up.sh -- allocation is per-host, so each attempt is" >&2
    echo "a fresh draw." >&2
    bash "$(dirname "$0")/down.sh" >&2
    exit 1
  fi
  sleep 5
done

echo
echo "Pod is up."
echo "  SSH:    ssh -i ~/.ssh/id_ed25519_runpod root@$ip -p $port"
echo "  Tunnel: ssh -i ~/.ssh/id_ed25519_runpod -N -L 8188:localhost:8188 root@$ip -p $port"
echo "  Proxy:  $proxy   (works without the tunnel; public, no auth)"
