#!/usr/bin/env bash
# Bring up a RunPod GPU pod from the image config/image.json pins, with the models
# attached, check its host key, then print the SSH + tunnel commands. Config
# comes from .env.

set -euo pipefail

cd "$(dirname "$0")/.."          # run from repo root no matter where invoked
set -a; source ./.env; set +a    # load RUNPOD_* config

PUBKEY="$(cat ~/.ssh/id_ed25519_runpod.pub)"
API="https://api.runpod.io/v2"
# What a host needs to render: torch's cu128 build and the model stack (0043 design D1).
RAM_FLOOR_GB=24
VRAM_FLOOR_GB=24
CUDA_FLOOR="12.8"

# Every call to RunPod: the key reaches curl on a file descriptor, never on its
# argv, where any process listing could read it; and the call is bounded, so a
# stalled read cannot hold the poll past its 420 s teardown (0034 design D2).
api() {
  curl -s --max-time 30 -H @<(printf 'Authorization: Bearer %s\n' "$RUNPOD_API_KEY") "$@"
}
source ./infra/pods.sh

report() {  # report <call> <status> <body>, per 0034 design D4
  echo "$1 returned HTTP $2:" >&2
  echo "$3" \
    | jq -er 'select(type == "object" and has("title")) | "  \(.title): \(.detail)"' \
      >&2 2>/dev/null \
    || echo "  $3" >&2
}

lost() {  # a create whose outcome is unknown may have placed a pod no file records
  echo "The create's outcome is unknown: a pod named 'isekai' may exist and bill." >&2
  echo "Run bash infra/down.sh -- it finds and removes every 'isekai' pod --" >&2
  echo "then re-run bash infra/up.sh." >&2
}

refuse() { echo "refused: $*" >&2; exit 1; }

# A pod outside its volume's data centre boots without its models, and a volume
# smaller than the manifest fails its download after billing starts (0041 design D3).
check_volume() {
  local volume dc size need
  volume=$(api -f "$API/network-volumes/$RUNPOD_VOLUME_ID") \
    || refuse "the models volume RUNPOD_VOLUME_ID names could not be read; check it with the RunPod MCP's get-network-volume"
  read -r dc size < <(echo "$volume" | jq -r '"\(.dataCenter // "") \(.size // "")"' 2>/dev/null) || true
  [ -n "${dc:-}" ] && [[ "${size:-}" =~ ^[0-9]+$ ]] \
    || refuse "the models volume's answer names no data centre and size; check it with the RunPod MCP's get-network-volume"
  [ "$RUNPOD_DATACENTER" = "$dc" ] \
    || refuse "RUNPOD_DATACENTER is $RUNPOD_DATACENTER, but the models volume is in $dc; set RUNPOD_DATACENTER=$dc in .env"
  need=$(jq '[.entries[].bytes] | add' config/models.json)
  [ "$((size * 1000 * 1000 * 1000))" -ge "$need" ] \
    || refuse "the models volume holds $size GB, but config/models.json needs $need bytes; grow it to $(( (need + 999999999) / 1000000000 )) GB with the RunPod MCP's update-network-volume"
}

# refuse_and_tear_down <reason> [<next step>]: the next step is printed only once
# down.sh has stopped the billing; a failed teardown ends on down.sh's own words.
refuse_and_tear_down() {
  echo "refused: $1" >&2
  bash ./infra/down.sh >&2 || exit 1
  [ -z "${2:-}" ] || echo "$2" >&2
  exit 1
}

# A pod beside a recorded or listed one orphans it, billing with nothing watching
# it; down.sh removes them all (0043 design D2).
check_no_pod() {
  local listed
  [ ! -f .runpod_pod_id ] \
    || refuse "a pod is already recorded in .runpod_pod_id; run bash infra/down.sh"
  listed=$(isekai_pods) \
    || refuse "the account's pods could not be listed; check them with the RunPod MCP's list-pods"
  [ -z "$listed" ] \
    || refuse "an 'isekai' pod already exists: $(echo "$listed" | awk '{printf "%s%s (%s)", (NR > 1 ? ", " : ""), $1, $2}'); run bash infra/down.sh"
}

# placeable_gpus <cards>: the cards the catalogue gives VRAM_FLOOR_GB or more, one
# per line. A card RunPod does not know refuses: a typo never lands another card.
placeable_gpus() {
  local gpu out code memory
  while IFS= read -r gpu; do
    out=$(api -S -w '\n%{http_code}' "$API/catalog/gpus/$(jq -rn --arg g "$gpu" '$g|@uri')") || true
    code=${out##*$'\n'}
    case "$code" in
      200) ;;
      404) refuse "RUNPOD_GPU_TYPE names $gpu, which RunPod does not know; fix .env" ;;
      *)
        report "Catalogue read of '$gpu'" "${code:-000}" "${out%$'\n'*}"
        refuse "RunPod's catalogue could not be read for $gpu; check it with the RunPod MCP's get-gpu-type"
        ;;
    esac
    memory=$(echo "${out%$'\n'*}" | jq -r '.memory | numbers' 2>/dev/null) || true
    [ -n "$memory" ] \
      || refuse "RunPod's catalogue names no memory for $gpu; check it with the RunPod MCP's get-gpu-type"
    if jq -en --argjson m "$memory" --argjson f "$VRAM_FLOOR_GB" '$m < $f' >/dev/null; then
      echo "skipped: $gpu has $memory GB, below $VRAM_FLOOR_GB" >&2
    else
      echo "$gpu"
    fi
  done <<< "$1"
}

# The log stays open, so each read is cut at 10 s; what it held by then is read.
printed_fingerprint() {
  api -N --max-time 10 "$API/pods/$pod_id/logs?since=$since" \
    | jq -rR 'select(startswith("data: ")) | .[6:] | fromjson? | .line // empty
              | capture("isekai host key: (?<f>SHA256:[A-Za-z0-9+/]+)").f' 2>/dev/null \
    | head -n 1
}

scanned_key() {  # the pod's Ed25519 host key, as a known-hosts line
  ssh-keyscan -T 10 -t ed25519 -p "$port" "$host" 2>/dev/null | grep -v '^#' | head -n 1
}

# The fingerprint comes over the authenticated API, not over the connection it
# vouches for; nothing reaches the pod until the two agree (0041 design D1, D2).
# sshd can answer after the port is mapped, so the scan waits longer than the log.
verify_host_key() {
  local printed="" key="" scanned
  local log_deadline=$((SECONDS + 60)) scan_deadline=$((SECONDS + 180))
  while [ "$SECONDS" -lt "$log_deadline" ]; do
    printed=$(printed_fingerprint) || true
    [ -n "$printed" ] && break
    sleep 5
  done
  [ -n "$printed" ] \
    || refuse_and_tear_down "the pod printed no host-key fingerprint within 60 s; read its log with the RunPod MCP's stream-pod-logs"
  while [ "$SECONDS" -lt "$scan_deadline" ]; do
    key=$(scanned_key) || true
    [ -n "$key" ] && break
    sleep 5
  done
  [ -n "$key" ] \
    || refuse_and_tear_down "the pod's SSH answered no host-key scan within 180 s" \
         "the pod is torn down, and bash infra/up.sh boots a fresh one"
  scanned=$(echo "$key" | ssh-keygen -lf - 2>/dev/null | awk '{print $2}') || true
  [ "$scanned" = "$printed" ] \
    || refuse_and_tear_down "the pod's host key ${scanned:-(unreadable)} does not match the fingerprint it printed, $printed" \
         "the pod is torn down, and bash infra/up.sh boots a fresh one"
  echo "$key" > .runpod_known_hosts
  echo "Host key verified: $printed"
}

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
# `volumeInGb` to 20 and mounts the pod's OWN volume disk at the mount path when
# none is attached, so the mount point exists either way (design.md D5). Here the
# question is answerable and tripping it costs nothing, because no pod exists yet.
if [ -z "${RUNPOD_VOLUME_ID:-}" ]; then
  echo "ERROR: RUNPOD_VOLUME_ID is empty in .env — refusing to create a pod." >&2
  echo "Without the network volume, provisioning downloads 16.5 GiB onto storage" >&2
  echo "that dies at teardown: it renders correctly, bills fully, and is noticed" >&2
  echo "only on the next metered session." >&2
  exit 1
fi

check_no_pod
check_volume

echo "Creating pod in $RUNPOD_DATACENTER ..."
echo "  image: $image_ref"
# `RUNPOD_GPU_TYPE` is a preference order, so one sold-out model does not end the
# session. v2 places one type per call, so the list is walked here: a 400 (no
# capacity, or a rule broken) tries the next type, anything else stops.
gpus=$(jq -rn --arg gpu "$RUNPOD_GPU_TYPE" \
  '$gpu | split(",") | map(gsub("^\\s+|\\s+$"; "")) | map(select(length > 0)) | .[]')
if [ -z "$gpus" ]; then
  echo "ERROR: RUNPOD_GPU_TYPE names no GPU type in .env — refusing to create a pod." >&2
  exit 1
fi
gpus=$(placeable_gpus "$gpus") || exit 1
[ -n "$gpus" ] \
  || refuse "every card RUNPOD_GPU_TYPE names has less than $VRAM_FLOOR_GB GB; name one with more in .env"
pod_id=""
since=$(date -u +%FT%TZ)          # the pod's log is read from here on
while IFS= read -r gpu; do
  echo "Trying '$gpu' ..."
  body=$(jq -n \
    --arg image  "$image_ref" \
    --arg gpu    "$gpu" \
    --arg vol    "$RUNPOD_VOLUME_ID" \
    --arg dc     "$RUNPOD_DATACENTER" \
    --arg pubkey "$PUBKEY" \
    --argjson ram "$RAM_FLOOR_GB" \
    --arg cuda   "$CUDA_FLOOR" \
    '{ name: "isekai",
       image: $image,
       gpu: { id: $gpu, count: 1, minRamPerGpu: $ram, minCudaVersion: $cuda },
       mounts: { network: [{ volumeId: $vol, path: "/runpod-volume" }] },
       ports: ["22/tcp"],
       disk: 30,
       dataCenterIds: [$dc],
       cloud: "SECURE",
       env: { PUBLIC_KEY: $pubkey,
              RUNPOD_VOLUME_ID: $vol } }')
  # A transport failure is code 000, reported like any status, never a silent exit.
  out=$(api -S -w '\n%{http_code}' -X POST "$API/pods" \
    -H "Content-Type: application/json" \
    -d "$body") || true
  code=${out##*$'\n'}
  resp=${out%$'\n'*}
  if [ "$code" = "201" ]; then
    pod_id=$(echo "$resp" | jq -r '.id // empty' 2>/dev/null) || true
    [ -n "$pod_id" ] && break
  fi
  report "Create on '$gpu'" "$code" "$resp"
  [ "$code" = "400" ] && continue
  # RunPod may have placed the pod and the answer been lost on the way back.
  case "$code" in
    201|5??|000|"") lost ;;
  esac
  exit 1
done <<< "$gpus"

if [ -z "$pod_id" ]; then
  echo "Pod creation failed: no type in RUNPOD_GPU_TYPE was placed." >&2; exit 1
fi
echo "$pod_id" > .runpod_pod_id
# What `generate` records as the image a render ran on; down.sh removes it.
echo "$image_ref" > .runpod_pod_image
echo "Pod $pod_id created at $(date -u +%FT%TZ). Waiting for SSH ..."

# Poll until `ssh.direct` -- a public IP and a mapped :22 -- appears, and give up
# if it never does. Some SECURE-cloud machines come up `RUNNING` with `runtime:
# null` and only RunPod's SSH proxy, a restricted shell that will not carry the
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
  # A failed read -- transport, status or body -- is "not yet", never an abort:
  # under `set -e` an abort here skips the teardown below (0034 design D2).
  read -r host port < <(
    api -f "$API/pods/$pod_id" \
      | jq -r '.ssh.direct | "\(.host // "") \(.port // "")"' 2>/dev/null
  ) || true
  [ -n "$host" ] && [ -n "$port" ] && break
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
# The API's mapping of :22 is the event timed; the host-key scan comes after it.
echo "Port 22 mapped at $(date -u +%FT%TZ)."
verify_host_key

echo
echo "Pod is up."
echo "  SSH:    ssh -i ~/.ssh/id_ed25519_runpod -o UserKnownHostsFile=.runpod_known_hosts -o StrictHostKeyChecking=yes root@$host -p $port"
echo "  Tunnel: ssh -i ~/.ssh/id_ed25519_runpod -o UserKnownHostsFile=.runpod_known_hosts -o StrictHostKeyChecking=yes -N -L 8188:localhost:8188 root@$host -p $port"
