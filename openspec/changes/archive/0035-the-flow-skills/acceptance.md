Go: 2026-09-27 — the operator's, in the session that ran `run-flows`; the operator reported the run a success in the
build session ("We have the full flow running with skills. Both skills work pretty well.").

# Acceptance — `run-flows`, end to end

The operator ran `run-flows` on `.data/v0.25/` in a separate session ([D7](design.md#d7)). The record below was
rebuilt in the build session from that batch on disk, by counts: the build session opened no photograph, no run
file and not the page, and copied no pod id or address out of `log.txt`.

| step | command | result |
|---|---|---|
| 0 | `ls .data/v0.25/photos \| wc -l` | 5 photographs |
| 1 | `python -m isekai tag` — both flows | 10 `wd14 wrote`, 10 `tags wrote` |
| 1 | `python -m isekai caption` — both flows | 10 `caption wrote` |
| 1 | `python -m isekai sheet` — both flows | 10 `sheet wrote` |
| 2 | `python -m isekai ui` — ports 8517 and 8518 | the operator reviewed and said "approved" |
| 3 | approvals, per flow | `summon-anime-wai` 5, `conjure-anime-wai` 5 |
| 4 | `bash infra/render.sh .data/v0.25/runs summon-anime-wai=1 conjure-anime-wai=1` | 20 `assembled`, 10 `rendered`, 1 pod created, `Pod terminated` |
| 5 | `python -m isekai compare .data/v0.25` | `.data/v0.25/compare.html` |

Refusals across the whole log: 0.

**The pod session:** created at 2026-09-27T14:36:09Z, port 22 mapped at 14:41:50Z, torn down by `render.sh`'s trap
on a 204 — the log's last write at 14:48:50Z. About 13 minutes, inside the 45-minute ceiling. Neither
`.runpod_pod_id` nor `.runpod_pod_image` is left.

**The RunPod MCP confirms the pod gone:** `list-pods`, called from the build session after the run, returned
`"pods": []`.

**The comparison page** was then refined with the operator, on this batch, before the phase closed: `summon` beside
the photograph, each render's positive prompt beneath it, captions in a full-width row, images at their own
proportions, and an overlay that fits a clicked image and toggles its full size.
Each refinement is its own commit beside phase 5's, at the operator's direction, rather than one phase, one commit:
`5f681b9`, `c2b0619`, `1ccb9af`, `0cc79ca`, `d6c954e` and `0bd8d1d`.
