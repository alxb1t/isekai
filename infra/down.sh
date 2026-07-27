#!/usr/bin/env bash
# Terminate the pod recorded by up.sh — billing stops. The network volume persists.
set -euo pipefail

cd "$(dirname "$0")/.."
set -a; source ./.env; set +a

if [ ! -f .runpod_pod_id ]; then
  echo "No .runpod_pod_id — nothing to tear down (already down?)."; exit 0
fi
pod_id=$(cat .runpod_pod_id)

echo "Terminating pod $pod_id ..."
code=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
  "https://rest.runpod.io/v1/pods/$pod_id" \
  -H "Authorization: Bearer $RUNPOD_API_KEY")

if [ "$code" = "204" ]; then
  rm -f .runpod_pod_id
  echo "Pod terminated. Billing stopped. (Network volume kept.)"
else
  echo "Delete returned HTTP $code — check the console to be sure the pod is gone."
  exit 1
fi
