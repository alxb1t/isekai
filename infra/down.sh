#!/usr/bin/env bash
# Terminate the pod recorded by up.sh — billing stops. The network volume persists.
set -euo pipefail

cd "$(dirname "$0")/.."
set -a; source ./.env; set +a
API="https://api.runpod.io/v2"

# The key reaches curl on a file descriptor, never on its argv; the call is bounded.
api() {
  curl -s --max-time 30 -H @<(printf 'Authorization: Bearer %s\n' "$RUNPOD_API_KEY") "$@"
}

if [ ! -f .runpod_pod_id ]; then
  echo "No .runpod_pod_id — nothing to tear down (already down?)."
  echo "If infra/up.sh said a create's outcome is unknown, check the RunPod MCP's list-pods."
  exit 0
fi
pod_id=$(cat .runpod_pod_id)

echo "Terminating pod $pod_id ..."
out=$(api -S -w '\n%{http_code}' -X DELETE "$API/pods/$pod_id") || true
code=${out##*$'\n'}
resp=${out%$'\n'*}

if [ "$code" = "204" ]; then
  rm -f .runpod_pod_id .runpod_pod_image
  echo "Pod terminated. Billing stopped. (Network volume kept.)"
elif [ "$code" = "404" ]; then
  # A 404 is also what a wrong key gets, so it is never read as gone: a false
  # "gone" leaves a pod billing (0034 design D3).
  echo "The API does not know pod $pod_id: it may be gone, or the key may be wrong." >&2
  echo "Confirm it is gone with the RunPod MCP's get-pod; the record files are kept" >&2
  echo "until then. Once it is gone: rm .runpod_pod_id .runpod_pod_image" >&2
  exit 1
else
  echo "Delete returned HTTP $code — check the console to be sure the pod is gone." >&2
  echo "$resp" \
    | jq -er 'select(type == "object" and has("title")) | "  \(.title): \(.detail)"' \
      >&2 2>/dev/null \
    || echo "  $resp" >&2
  exit 1
fi
