#!/usr/bin/env bash
# Bring up a RunPod GPU pod from the image config/image.json pins, with the models
# attached, then print the SSH + tunnel commands. Config comes from .env.

set -euo pipefail

cd "$(dirname "$0")/.."          # run from repo root no matter where invoked
set -a; source ./.env; set +a    # load RUNPOD_* config

PUBKEY="$(cat ~/.ssh/id_ed25519_runpod.pub)"

# The pod boots the digest config/image.json pins, never a tag, and nothing in the
# environment overrides it: moving the pin is a commit (0033 design D3).
image_ref="$(jq -r '"\(.image)@\(.digest)"' config/image.json)"
if ! [[ "$image_ref" =~ @sha256:[0-9a-f]{64}$ ]]; then
  echo "ERROR: config/image.json names no sha256 digest ($image_ref)." >&2
  echo "Refusing to create a pod from an image that is not pinned." >&2
  exit 1
fi

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

echo "Creating pod in $RUNPOD_DATACENTER on '$RUNPOD_GPU_TYPE' ..."
echo "  image: $image_ref"
# `RUNPOD_GPU_TYPE` is a comma-separated preference order, not one name: the API
# takes a list and picks the first with capacity, which is what stops a session
# dying at creation because one model is sold out in one datacenter. It is split
# here rather than in `.env` because the API wants an array of exact enum values,
# and a single string carrying a comma is not one of them -- it is rejected at
# creation with the whole enum echoed back, which is how this was found.
body=$(jq -n \
  --arg image  "$image_ref" \
  --arg gpu    "$RUNPOD_GPU_TYPE" \
  --arg vol    "$RUNPOD_VOLUME_ID" \
  --arg dc     "$RUNPOD_DATACENTER" \
  --arg pubkey "$PUBKEY" \
  '{ name: "isekai",
     imageName: $image,
     gpuTypeIds: ($gpu | split(",") | map(gsub("^\\s+|\\s+$"; "")) | map(select(length > 0))),
     gpuCount: 1,
     networkVolumeId: $vol,
     volumeMountPath: "/runpod-volume",
     ports: ["22/tcp"],
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
# What `generate` records as the image a render ran on; down.sh removes it.
echo "$image_ref" > .runpod_pod_image
echo "Pod $pod_id created at $(date -u +%FT%TZ). Waiting for SSH ..."

# Poll until the pod has a public IP and a mapped :22 -- and give up if one never
# arrives. Some SECURE-cloud machines come up `RUNNING` with `runtime: null` and
# only RunPod's own SSH proxy, which is a restricted shell and will not carry the
# port forward this pipeline needs. The pod is then useless and bills anyway.
#
# This poll was unbounded, which made it the one thing in this repository that
# could bill indefinitely while looking like it was working. It cost two sessions
# on 2026-09-08. On timeout the pod is **torn down here**: a bounded wait that
# leaves the meter running has not solved the problem it was added for, and
# teardown is the act that stops the billing.
#
# 420s, not 180s. The IP check itself answers in seconds, but the pod is not
# usable until the image has pulled and ComfyUI has started -- observed at 2-4
# minutes together. The cost of the longer wait is a few cents on a pod that
# never comes up; the cost of a shorter one is tearing down healthy pods
# mid-boot.
#
# The prototype's companion change -- exposing ComfyUI's port through RunPod's
# HTTP proxy, and probing it as a fallback -- is deliberately NOT taken. That
# proxy is a public, unauthenticated endpoint and ComfyUI has no auth, so a
# version adopting it must put authentication in front of ComfyUI first
# (design.md D10). The bounded wait adds no exposure; it only removes one, and
# that asymmetry is why one half crosses and the other does not. The grep this
# phase is verified by is literal, so the two names stay out of this file
# entirely -- including out of the comment that says why.
deadline=$((SECONDS + 420))
while true; do
  pod=$(curl -s "https://rest.runpod.io/v1/pods?id=$pod_id" \
        -H "Authorization: Bearer $RUNPOD_API_KEY")
  ip=$(echo   "$pod" | jq -r '(if type=="array" then .[0] else . end).publicIp // empty')
  port=$(echo "$pod" | jq -r '(if type=="array" then .[0] else . end).portMappings."22" // empty')
  [ -n "$ip" ] && [ -n "$port" ] && break
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo >&2
    echo "ERROR: pod $pod_id got no public IP and no mapped :22 within 420s." >&2
    echo "Tearing it down rather than billing for a pod we cannot use. Re-run" >&2
    echo "infra/up.sh -- allocation is per-host, so each attempt is a fresh draw." >&2
    # Spelled from the repository root, which line 7 already moved to. Re-deriving
    # `dirname "$0"` here would read a path relative to the *original* working
    # directory against the new one -- `bash isekai/infra/up.sh` from the parent
    # would look for `<parent>/isekai/isekai/infra/down.sh` and find nothing, and
    # a teardown that cannot resolve leaves the pod billing.
    bash ./infra/down.sh >&2
    exit 1
  fi
  sleep 5
done
# The API's mapping of :22 is the event timed: nothing here contacts SSH itself.
echo "Port 22 mapped at $(date -u +%FT%TZ)."

echo
echo "Pod is up."
echo "  SSH:    ssh -i ~/.ssh/id_ed25519_runpod root@$ip -p $port"
echo "  Tunnel: ssh -i ~/.ssh/id_ed25519_runpod -N -L 8188:localhost:8188 root@$ip -p $port"
