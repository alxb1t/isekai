#!/usr/bin/env bash
# One whole render session: create the pod, open the tunnel, wait for ComfyUI,
# render each flow, and tear the pod down on every way out (D36).
#
#   bash infra/render.sh <runs> <flow>=<count|source> ...
#   e.g. bash infra/render.sh .data/b1/runs summon-anime-wai=1 conjure-anime-wai=1
#        bash infra/render.sh .data/b1/runs control-anime-wai=summon-anime-wai
#        bash infra/render.sh .data/b1/runs summon-anime-wai=1 control-anime-wai=summon-anime-wai
#
# A count draws that many seeds; a source flow renders its latest seeds again.
# A source rendered by count in the same line goes first, and is one session.
# Output is shown and appended to the batch's log, <runs>/../log.txt.

set -euo pipefail

cd "$(dirname "$0")/.."          # run from repo root no matter where invoked

SERVER="http://127.0.0.1:8188"
WAIT=300                          # seconds ComfyUI gets to answer through the tunnel
CEILING=2640                      # seconds to the halt: CLAUDE.md's 45 minutes, less one for down.sh

# A refusal goes to the batch's log too: run-flows reads the log, not this output.
# Until the runs root is checked there is no batch, so no log to write it to.
refuse() { echo "refused: $*" | tee -a "${log:-/dev/null}" >&2; exit 1; }

[ "$#" -ge 2 ] || refuse "usage: bash infra/render.sh <runs> <flow>=<count|source> ..."
runs=$1; shift
[ -d "$runs" ] || refuse "$runs is not a directory; give the batch's runs/"
log="$(dirname "$runs")/log.txt"
flows=(); names=(); modes=(); values=()
for spec in "$@"; do
  [[ "$spec" =~ ^[a-z0-9-]+=([1-9][0-9]*|[a-z][a-z0-9-]*)$ ]] \
    || refuse "'$spec' is not <flow>=<count> or <flow>=<source>, e.g. summon-anime-wai=1"
  flows+=(--flow "${spec%%=*}")
  names+=("${spec%%=*}"); values+=("${spec#*=}")
  if [[ "${spec#*=}" =~ ^[0-9]+$ ]]; then modes+=(--count); else modes+=(--seeds-from); fi
done

# A source rendered by count earlier in this line has no seeds until the pod is up,
# so before the pod its dependents are checked against its latest approval, the
# group it renders into, and their seeds at their turn; one placed before its source
# could never be.
defer=()
for i in "${!names[@]}"; do
  defer+=(0)
  [ "${modes[$i]}" = --seeds-from ] || continue
  for j in "${!names[@]}"; do
    { [ "${names[$j]}" = "${values[$i]}" ] && [ "${modes[$j]}" = --count ]; } || continue
    [ "$j" -lt "$i" ] \
      || refuse "'${names[$i]}=${values[$i]}' comes before its source '${names[$j]}=${values[$j]}'; put the source first"
    defer[$i]=1
  done
done

# Every run under the root, by id. bash 3.2 (macOS) has no mapfile.
ids=()
for dir in "$runs"/*/; do
  if [ -f "$dir/run.json" ]; then ids+=("$(basename "$dir")"); fi
done
[ "${#ids[@]}" -gt 0 ] || refuse "$runs holds no run; open them from the batch's \
photographs with: uv run python -m isekai tag ${flows[*]} --runs $runs $(dirname "$runs")/photos/*"

# A recorded pod is another session's: the trap below would tear it down.
[ ! -f .runpod_pod_id ] \
  || refuse "a pod is already recorded in .runpod_pod_id; run bash infra/down.sh first"
# An earlier create never recorded: its pod is found by down.sh, not by this trap.
[ ! -f .runpod_pod_pending ] \
  || refuse "an earlier create was never recorded (.runpod_pod_pending); run bash infra/down.sh first"
# Something already answering on the port would be rendered against instead.
# --noproxy: an exported http_proxy would take loopback too.
if curl -sf --noproxy '*' --max-time 5 "$SERVER/system_stats" >/dev/null 2>&1; then
  refuse "$SERVER already answers. An earlier session's tunnel stops with \
pkill -f -- '-L 8188:localhost:8188'; lsof -iTCP:8188 -sTCP:LISTEN shows anything else"
fi

# Free work first: every prompt is assembled before anything is rented, so a
# missing approval refuses here rather than on a billing pod.
uv run python -m isekai generate "${flows[@]}" --runs "$runs" "${ids[@]}" 2>&1 | tee -a "$log"
# A source flow's render is checked here too, so a missing one or a copy out of
# step with it refuses before the pod.
for i in "${!names[@]}"; do
  [ "${modes[$i]}" = --count ] && continue
  check=--seeds-from
  [ "${defer[$i]}" = 1 ] && check=--in-step-with
  uv run python -m isekai generate --flow "${names[$i]}" "$check" "${values[$i]}" \
    --runs "$runs" "${ids[@]}" 2>&1 | tee -a "$log"
done

tunnel=""
watchdog=""
up_status=""                      # up.sh's exit; its LOST_CREATE_EXIT is 3
up_out=$(mktemp)
teardown() {  # teardown [status]; a signal passes its own, an exit keeps $?
  local status=${1:-$?}
  # Nothing in here may end the handler before down.sh runs: a second Ctrl-C is
  # ignored, not defaulted, and down.sh inherits the ignore.
  set +e
  trap - EXIT
  trap '' INT TERM HUP
  if [ -n "$watchdog" ]; then kill "$watchdog" 2>/dev/null; fi
  if [ -n "$tunnel" ]; then kill "$tunnel" 2>/dev/null; fi
  rm -f "$up_out"
  # A create up.sh began but never recorded leaves a pod no file names, which
  # down.sh finds. A refusal or an interrupt before the create made none, so a pod
  # it names is left for the operator's down.sh (D36).
  if [ -f .runpod_pod_id ] || [ -f .runpod_pod_pending ] || [ "$up_status" = 3 ]; then
    bash ./infra/down.sh 2>&1 | tee -a "$log"
    [ "${PIPESTATUS[0]}" -eq 0 ] || status=1
  else
    echo "No pod is recorded and no create was begun; nothing to tear down." | tee -a "$log"
  fi
  exit "$status"
}
# Set before the pod exists, so no step after it can leave the pod billing.
trap teardown EXIT; trap 'teardown 130' INT; trap 'teardown 143' TERM; trap 'teardown 129' HUP

# The ceiling is a halt (CLAUDE.md). A TERM to this shell waits for the command
# in flight, so the watchdog stops that too; the pending TERM then runs the trap.
# Renders already written are kept, and the same command renders only the rest.
# Polled, so a session killed past its trap takes the watchdog with it.
(
  end=$((SECONDS + CEILING))
  while [ "$SECONDS" -lt "$end" ]; do
    kill -0 $$ 2>/dev/null || exit 0
    sleep 5 </dev/null >/dev/null 2>&1
  done
  kill -0 $$ 2>/dev/null || exit 0
  echo "refused: the session reached its ${CEILING}s ceiling; renders so far are \
kept, and in a new session bash infra/render.sh $runs $* renders only the rest" \
    | tee -a "$log" >&2
  kill -TERM $$
  pkill -TERM -P $$
) &
watchdog=$!

# From its first create until its record, up.sh keeps .runpod_pod_pending, so an
# interrupt then is a lost create and one before it sweeps nothing.
# A log write that fails after a good up.sh is a failed session, never exit 0.
bash ./infra/up.sh 2>&1 | tee -a "$log" "$up_out" \
  || { up_status=${PIPESTATUS[0]}; exit "$(( up_status == 0 ? 1 : up_status ))"; }
up_status=0

read -r host port < <(
  sed -nE 's/.*Tunnel: .* root@([^ ]+) -p ([0-9]+).*/\1 \2/p' "$up_out"
) || true
[ -n "${host:-}" ] && [ -n "${port:-}" ] \
  || refuse "up.sh printed no Tunnel: line with a host and a port"

open_tunnel() {
  # up.sh kept the pod's key only once it matched the fingerprint the pod printed;
  # down.sh removes it with the pod.
  ssh -i ~/.ssh/id_ed25519_runpod -o BatchMode=yes -o StrictHostKeyChecking=yes \
    -o UserKnownHostsFile=.runpod_known_hosts -o ExitOnForwardFailure=yes \
    -N -L 8188:localhost:8188 "root@$host" -p "$port" &
  tunnel=$!
}
open_tunnel

# sshd and ComfyUI come up after the port is mapped, so a tunnel that died is
# reopened until the bound.
deadline=$((SECONDS + WAIT))
until curl -sf --noproxy '*' --max-time 5 "$SERVER/system_stats" >/dev/null 2>&1; do
  [ "$SECONDS" -lt "$deadline" ] \
    || refuse "$SERVER/system_stats did not answer within ${WAIT}s"
  kill -0 "$tunnel" 2>/dev/null || open_tunnel
  sleep 5
done

# One flow failing does not cost the next its render; the exit says any failed.
failed=0
for i in "${!names[@]}"; do
  uv run python -m isekai generate --flow "${names[$i]}" "${modes[$i]}" "${values[$i]}" \
    --server "$SERVER" --runs "$runs" "${ids[@]}" 2>&1 | tee -a "$log" \
    || failed=1
done
exit "$failed"
