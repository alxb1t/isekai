# Acceptance — 0044 the session proved

The render boot and the stop boot on `v0.30-rc2`, per [design D5](design.md#d5), read on 2026-09-29. One line per
piece of evidence; no pod id, address, fingerprint or key.

## The render boot

placement: gpu.memory 62 on both pods, read with the MCP's get-pod; the card that rendered, an RTX PRO 4500 Blackwell, has 32125 MB of VRAM, and the first, an RTX 4090, 24081 MB.
stop timer: armed, `step: the stop timer` in the pod's log, read with the MCP's stream-pod-logs, on both pods.
renders: summon-anime-wai and conjure-anime-wai, one each for the four synthetic portraits of `.data/v0.30.1`; `render.sh` exited 0 and `down.sh` removed the pod.
first try: refused, `the pod printed no host-key fingerprint within 60 s`, though the pod printed it before port 22 was mapped; `up.sh` tore the pod down. The batch log keeps that refusal, so `grep -c '^refused'` on it prints 1; the operator accepted it as the failed try's record.
log reads: a read of the pod's log from a `since` time stalled on each try, from `up.sh` and from the MCP, while a read of its last lines answered; `up.sh` reads by `since`. A card for the next rebuild.

## The stop boot

listing: `isekai_pods`, run on the laptop against the live API, listed one pod, the recorded one, RUNNING.
key scope: the pod's own key answers 200 to `GET /v2/pods/<its id>` and 403 to `GET /v2/pods`; an SSH shell carries neither `RUNPOD_API_KEY` nor `RUNPOD_POD_ID`, and `/proc/1/environ` carries both.
refused key: `stop_pod.sh` with a bogus key printed `the stop answered HTTP 401; trying again in 30s`, then 60s, until `timeout 40` ended it with 124. A 401 is retried without end: a card for the next rebuild.
stop: EXITED — `stop_pod.sh` with the pod's own key and id printed `the pod is stopping` and exited 0; the MCP's get-pod showed EXITED, with `start` and `terminate` its only actions.
signal path: the system log shows `stop container` in the second the stop answered and `remove container` 16 s later; the container's own last lines could not be read, so whether `start.sh`'s EXIT trap sent a second stop is unread. A card for the next rebuild.
stopped: 5 minutes EXITED, the operator's choice over D5's 10; then `down.sh` answered `Pod terminated`.
billing while stopped: not yet posted; the MCP's list-pod-billing returned no record for the hour, for the pod or the account, when read twice after the teardown. The operator accepted it pending.
pods: [] — the MCP's list-pods, after each boot's teardown.
