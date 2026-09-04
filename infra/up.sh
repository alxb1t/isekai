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

echo "Creating pod in $RUNPOD_DATACENTER on '$RUNPOD_GPU_TYPE' ..."
echo "  image: $RUNPOD_IMAGE"
body=$(jq -n \
  --arg image  "$RUNPOD_IMAGE" \
  --arg gpu    "$RUNPOD_GPU_TYPE" \
  --arg vol    "$RUNPOD_VOLUME_ID" \
  --arg dc     "$RUNPOD_DATACENTER" \
  --arg pubkey "$PUBKEY" \
  '{ name: "isekai",
     imageName: $image,
     gpuTypeIds: [$gpu],
     gpuCount: 1,
     networkVolumeId: $vol,
     volumeMountPath: "/runpod-volume",
     ports: ["22/tcp"],
     containerDiskInGb: 30,
     dataCenterIds: [$dc],
     cloudType: "SECURE",
     env: { PUBLIC_KEY: $pubkey } }')

resp=$(curl -s -X POST https://rest.runpod.io/v1/pods \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$body")

pod_id=$(echo "$resp" | jq -r '(if type=="array" then .[0] else . end).id // empty')

if [ -z "$pod_id" ]; then
  echo "Pod creation failed:"; echo "$resp" | jq . 2>/dev/null || echo "$resp"; exit 1
fi
echo "$pod_id" > .runpod_pod_id
echo "Pod $pod_id created. Waiting for SSH ..."

# Poll until the pod has a public IP and a mapped :22.
while true; do
  pod=$(curl -s "https://rest.runpod.io/v1/pods?id=$pod_id" \
        -H "Authorization: Bearer $RUNPOD_API_KEY")
  ip=$(echo   "$pod" | jq -r '(if type=="array" then .[0] else . end).publicIp // empty')
  port=$(echo "$pod" | jq -r '(if type=="array" then .[0] else . end).portMappings."22" // empty')
  [ -n "$ip" ] && [ -n "$port" ] && break
  sleep 5
done

echo
echo "Pod is up."
echo "  SSH:    ssh -i ~/.ssh/id_ed25519_runpod root@$ip -p $port"
echo "  Tunnel: ssh -i ~/.ssh/id_ed25519_runpod -N -L 8188:localhost:8188 root@$ip -p $port"
