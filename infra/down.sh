#!/usr/bin/env bash
# Terminate the pod recorded by up.sh, then every other 'isekai' pod listed —
# billing stops, and no pod is left for nothing to watch (0043 design D3). The
# network volume persists.
set -euo pipefail

cd "$(dirname "$0")/.."
set -a; source ./.env; set +a
API="https://api.runpod.io/v2"

# The key reaches curl on a file descriptor, never on its argv; the call is bounded.
api() {
  curl -s --max-time 30 -H @<(printf 'Authorization: Bearer %s\n' "$RUNPOD_API_KEY") "$@"
}
source ./infra/pods.sh

delete_pod() {  # delete_pod <id>: set code and resp from RunPod's answer
  out=$(api -S -w '\n%{http_code}' -X DELETE "$API/pods/$1") || true
  code=${out##*$'\n'}
  resp=${out%$'\n'*}
}

detail() {  # detail <body>: RunPod's title and detail, or the body as it came
  echo "$1" \
    | jq -er 'select(type == "object" and has("title")) | "  \(.title): \(.detail)"' \
      >&2 2>/dev/null \
    || echo "  $1" >&2
}

failed=0
pod_id=""
if [ -f .runpod_pod_id ]; then
  pod_id=$(cat .runpod_pod_id)

  echo "Terminating pod $pod_id ..."
  delete_pod "$pod_id"

  if [ "$code" = "204" ]; then
    rm -f .runpod_pod_id .runpod_pod_image .runpod_known_hosts
    echo "Pod terminated. Billing stopped. (Network volume kept.)"
  elif [ "$code" = "404" ]; then
    # A 404 is also what a wrong key gets, so it is never read as gone: a false
    # "gone" leaves a pod billing (0034 design D3).
    echo "The API does not know pod $pod_id: it may be gone, or the key may be wrong." >&2
    echo "Confirm it is gone with the RunPod MCP's get-pod; the record files are kept" >&2
    echo "until then. Once it is gone: rm .runpod_pod_id .runpod_pod_image .runpod_known_hosts" >&2
    failed=1
  else
    echo "Delete returned HTTP $code — check the console to be sure the pod is gone." >&2
    detail "$resp"
    echo "Once the RunPod MCP confirms it gone: rm .runpod_pod_id .runpod_pod_image .runpod_known_hosts" >&2
    failed=1
  fi
fi

# A lost create or a second up.sh leaves a pod no record names.
if ! listed=$(isekai_pods); then
  echo "Could not list pods; confirm with the RunPod MCP's list-pods that no 'isekai' pod is left." >&2
  exit 1
fi
# up.sh's pending-create marker is spent once a sweep leaves no pod (0044 D2).
if [ -z "$listed" ] && [ -z "$pod_id" ]; then
  rm -f .runpod_pod_pending
  echo "No pod to tear down."
  exit 0
fi
while read -r id status; do
  [ -n "$id" ] && [ "$id" != "$pod_id" ] || continue
  delete_pod "$id"
  case "$code" in
    204) echo "Removed $id ($status)." ;;
    *)
      echo "Delete of $id ($status) returned HTTP $code; confirm it gone with the RunPod MCP's get-pod." >&2
      detail "$resp"
      failed=1
      ;;
  esac
done <<< "$listed"
[ "$failed" -ne 0 ] || rm -f .runpod_pod_pending
exit "$failed"
