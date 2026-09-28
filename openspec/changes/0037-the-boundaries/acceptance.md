Go: 2026-09-28 — the operator's, in the build session, after the ceiling was quoted (45 minutes, ~$0.30); the
operator reported the acceptance a success ("The outputs are received, the acceptance is successfull.").

# Acceptance — one render session with a dead proxy

The operator's batch in `.data/v0.26/` ran through `run-flows` in the build session, per [D10](design.md#d10). The
record is by counts from the log: no photograph, run file or page was opened, and no pod id or address is copied.

| step | command | result |
|---|---|---|
| 0 | `ls .data/v0.26/photos \| wc -l` | 2 photographs |
| 1 | `python -m isekai tag` — both flows | 4 `wd14 wrote`, 4 `tags wrote` |
| 1 | `python -m isekai caption` — both flows | 4 `caption wrote` |
| 1 | `python -m isekai sheet` — both flows | 4 `sheet wrote` |
| 2 | `python -m isekai ui` — ports 8517 and 8518 | the operator reviewed and said "approved" |
| 3 | approvals, per flow | `summon-anime-wai` 2, `conjure-anime-wai` 2 |
| 4 | `env -u https_proxy -u HTTPS_PROXY -u no_proxy -u NO_PROXY http_proxy=http://127.0.0.1:9 bash infra/render.sh .data/v0.26/runs summon-anime-wai=1 conjure-anime-wai=1` | exit 0; 8 `assembled`, 4 `rendered`, `Pod terminated` |
| 5 | `python -m isekai compare .data/v0.26` | `.data/v0.26/compare.html` |

Refusals across the whole log: 0 (`grep -c '^refused' .data/v0.26/log.txt`).

**The exported proxy:** step 4's, on port 9 of loopback, where nothing listens, with `https_proxy` and `no_proxy`
unset. RunPod's API is HTTPS and untouched by it. Every request to `127.0.0.1:8188` — `render.sh`'s own checks and
the ComfyUI client's upload, submit, poll and download — reached the tunnel, so none followed the proxy.

**What the renders prove:** the proxy ignored ([D1](design.md#d1), [D11](design.md#d11)), the random-boundary
multipart upload accepted by a real ComfyUI ([D4](design.md#d4)), and the tunnel opened through the session's own
known-hosts file ([D9](design.md#d9)).

**The pod session:** created at 2026-09-28T09:08:15Z, port 22 mapped at 09:12:37Z, torn down by `render.sh`'s trap —
the log's last write at 09:15:58Z. About 8 minutes, inside the 45-minute ceiling. Neither `.runpod_pod_id` nor
`.runpod_pod_image` is left.

**The RunPod MCP confirms the pod gone:** `list-pods`, called from the build session after the run, returned
`pods: []`.
