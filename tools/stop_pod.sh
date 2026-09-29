#!/usr/bin/env bash
# Stop this pod through RunPod's API, with the key RunPod put in its environment:
# a watchdog on the laptop dies with the laptop, and this runs on the pod
# (0043 design D4). A failed stop is tried again every 30 s, for 5 minutes.
#
#   bash /opt/isekai/tools/stop_pod.sh

set -uo pipefail

API="https://api.runpod.io/v2"
RETRY_SECONDS=30
GIVE_UP_SECONDS=300

: "${RUNPOD_API_KEY:?RunPod gave this pod no RUNPOD_API_KEY; it cannot stop itself}"
: "${RUNPOD_POD_ID:?RunPod gave this pod no RUNPOD_POD_ID; it cannot stop itself}"

deadline=$((SECONDS + GIVE_UP_SECONDS))
while :; do
  code=$(curl -s --max-time 30 -o /dev/null -w '%{http_code}' -X POST \
    -H @<(printf 'Authorization: Bearer %s\n' "$RUNPOD_API_KEY") \
    -H "Content-Type: application/json" \
    -d '{"action":"stop"}' "$API/pods/$RUNPOD_POD_ID/action") || true
  if [ "$code" = "200" ]; then
    echo "$(date -u +%FT%TZ) the pod is stopping"
    exit 0
  fi
  if [ "$SECONDS" -ge "$deadline" ]; then
    echo "$(date -u +%FT%TZ) the stop answered HTTP ${code:-000}; giving up after ${GIVE_UP_SECONDS}s" >&2
    exit 1
  fi
  echo "$(date -u +%FT%TZ) the stop answered HTTP ${code:-000}; trying again in ${RETRY_SECONDS}s" >&2
  sleep "$RETRY_SECONDS"
done
