#!/usr/bin/env bash
# Stop this pod through RunPod's API, with the key RunPod put in its environment:
# a watchdog on the laptop dies with the laptop, and this runs on the pod
# (D36). A failed stop is tried again until it succeeds, the wait
# doubling from 30 s to 5 minutes: a stop that gave up would leave the pod billing.
#
#   bash /opt/isekai/tools/stop_pod.sh

set -uo pipefail

API="https://api.runpod.io/v2"
RETRY_SECONDS=30
MAX_RETRY_SECONDS=300

: "${RUNPOD_API_KEY:?RunPod gave this pod no RUNPOD_API_KEY; it cannot stop itself}"
: "${RUNPOD_POD_ID:?RunPod gave this pod no RUNPOD_POD_ID; it cannot stop itself}"

wait_s=$RETRY_SECONDS
while :; do
  code=$(curl -s --max-time 30 -o /dev/null -w '%{http_code}' -X POST \
    -H @<(printf 'Authorization: Bearer %s\n' "$RUNPOD_API_KEY") \
    -H "Content-Type: application/json" \
    -d '{"action":"stop"}' "$API/pods/$RUNPOD_POD_ID/action") || true
  if [ "$code" = "200" ]; then
    echo "$(date -u +%FT%TZ) the pod is stopping"
    exit 0
  fi
  echo "$(date -u +%FT%TZ) the stop answered HTTP ${code:-000}; trying again in ${wait_s}s" >&2
  sleep "$wait_s"
  wait_s=$((wait_s * 2 < MAX_RETRY_SECONDS ? wait_s * 2 : MAX_RETRY_SECONDS))
done
