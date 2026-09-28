# Design — 0041 the right machine

How `up.sh` proves the pod is the pod, keeps it beside its volume and quiet, and how the privacy rules enter
`docs/`. **Verdict: feasible** — shell against endpoints already in use, the system's OpenSSH, and prose.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`88cac24`):

- **The pod's side, since v0.28:** `start.sh:24` prints `isekai host key: $(ssh-keygen -lf "$key.pub" | awk '{print $2}')`
  — `SHA256:<fingerprint>` — at the SSH step, early in boot.
- **`infra/up.sh`:** `api()` (`:16-18`) sends the key through `@<(printf …)` with `--max-time 30`, and a later
  `--max-time` overrides it. The volume guard is `:49-54`; the create body's `env` is
  `{ PUBLIC_KEY: $pubkey, RUNPOD_VOLUME_ID: $vol }` (`:85-86`); the create echo `created at $(date -u …)` is `:112`; the
  poll ends at `Port 22 mapped at $(date -u …)` (`:164`); the `SSH:` and `Tunnel:` lines are `:168-169`.
- **`infra/render.sh`:** `known_hosts=$(mktemp)` (`:58`), `rm -f "$up_out" "$known_hosts"` in `teardown()` (`:68`),
  and `open_tunnel`'s `-o StrictHostKeyChecking=accept-new -o UserKnownHostsFile="$known_hosts"` (`:108-109`).
- **`infra/down.sh`:** `rm -f .runpod_pod_id .runpod_pod_image` on 204; `rm .runpod_pod_id .runpod_pod_image` named on
  404 and other. `.gitignore` lists `.runpod_pod_id` and `.runpod_pod_image`. `CLAUDE.md`'s pod rule names both files.
- **The APIs:** `GET /v2/pods/{id}/logs?since=<RFC 3339>` answers `text/event-stream`, `data: {"ts","source","line"}`,
  and stays open; `GET /v2/network-volumes/{id}` answers `.size` in GB and `.dataCenter`. `config/models.json`'s
  `.entries[].bytes` sum to the manifest's size.
- **Tests in `tests/test_infra.py` that bind these scripts:** every `curl ` line carries `--max-time` and every
  `Bearer` line `@<(printf`; the volume guard's `exit 1` sits right after its check; the first non-echo line
  after `cd` that names `down.sh` holds `./infra/down.sh`; `created at $(date -u` and `Port 22 mapped at $(date -u`
  stay; the lost-create shape stays; `test_a_sessions_host_keys_are_its_own` and `shared_host_keys` require
  `known_hosts=$(mktemp)`.
- **`docs/`:** `principles.md` has no privacy section; `decisions.md`'s highest id is D33, D27 is
  `:311-321`, and the *Infrastructure* preamble (`:301`) says serverless is being researched.

## Goals / Non-Goals

**Goals:** a pod proved before anything is sent; a pod beside its volume; no usage reports from the pod; the privacy
rules in `docs/`.

**Non-Goals:** a region rule; the image; the README.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `up.sh` reads the printed fingerprint, scans the key, and keeps it in `.runpod_known_hosts` on a match | it holds the pod id and the API key; one checked file serves the tunnel and a manual connection | `render.sh` checking — it has no API access |
| [D2](#d2) | a mismatch, or no line within 60 s, refuses and tears the pod down | an unproved machine never receives the photograph | connecting anyway and warning |
| [D3](#d3) | `up.sh` reads the volume before the create; another data centre, or a volume smaller than the manifest, is refused | a pod elsewhere boots without models; a small volume fails after billing starts | an EU allowlist — withdrawn |
| [D4](#d4) | the pod's `env` turns telemetry off: `ORT_DISABLE_TELEMETRY`, `HF_HUB_DISABLE_TELEMETRY`, `DO_NOT_TRACK` | no rebuild; `up.sh` alone creates pods (D28) | the image's `ENV` now — it waits for the next rebuild |
| [D5](#d5) | the privacy principles, D34, D35 and D27's data centre enter `docs/` | the rules the privacy versions built belong in the repository | a README section — the portfolio's |
| [D6](#d6) | one metered boot proves it; stubs prove the refusals | a mismatch on a real pod is not worth staging | no pod at all |

### D1

**The check, after `Port 22 mapped`.** `up.sh` stamps `since=$(date -u +%FT%TZ)` before the create, then:

```
pod log     api -N --max-time 10 "$API/pods/$pod_id/logs?since=$since"
            → the data: lines' .line → the text after "isekai host key: "   (polled every 5 s, up to 60 s)
scan        ssh-keyscan -T 10 -t ed25519 -p "$port" "$host"
compare     ssh-keygen -lf - on the scan → field 2 = the printed fingerprint
keep        the scanned line → .runpod_known_hosts; echo "Host key verified: SHA256:…"
```

- **The printed lines** gain `-o UserKnownHostsFile=.runpod_known_hosts -o StrictHostKeyChecking=yes`, so a manual
  connection is checked too; `render.sh`'s parse of the `Tunnel:` line still matches.
- **`render.sh`** drops `known_hosts=$(mktemp)` and tunnels with `-o StrictHostKeyChecking=yes
  -o UserKnownHostsFile=.runpod_known_hosts`; `teardown()` removes `"$up_out"` alone.
- **`down.sh`** removes `.runpod_known_hosts` with the other record files on 204, and names it last in its 404 and
  other-status messages. `.gitignore` lists it. `CLAUDE.md`'s pod rule names it beside the other record files.

### D2

**Refused, and torn down.** On a mismatch, `up.sh` prints `refused: the pod's host key <scanned> does not match the
fingerprint it printed, <printed>` and runs `bash ./infra/down.sh >&2`, then exits 1. With no line after 60 s it
prints `refused: the pod printed no host-key fingerprint within 60 s; read its log with the RunPod MCP's
stream-pod-logs` and tears down the same way. Neither line holds a pod id.

### D3

**The volume, before the create**, after the volume guard (`:49-54`) and clear of its check's window:
`api -f "$API/network-volumes/$RUNPOD_VOLUME_ID"` gives `.dataCenter` and `.size`.

- **Another data centre:** `RUNPOD_DATACENTER` differs from `.dataCenter` → refused, naming both.
- **Too small:** `.size` × 1000³ below `jq '[.entries[].bytes] | add' config/models.json` → refused, naming both.
- **A failed read** refuses too: the check cannot be skipped.

### D4

**Telemetry off at create.** The create body's `env` becomes
`{ PUBLIC_KEY: $pubkey, RUNPOD_VOLUME_ID: $vol, ORT_DISABLE_TELEMETRY: "1", HF_HUB_DISABLE_TELEMETRY: "1",
DO_NOT_TRACK: "1" }`. The image takes the same switches as `ENV` at its next rebuild (`op·telemetry-in-image`).

### D5

**`docs/`**, verbatim in substance:

- **`docs/principles.md`** gains `## Privacy` after `## State`, with its principles in the file's shape — the bold
  rule, **Why:** and **Held by:**:
  - **Privacy is ensured as far as is in our hands.** Where a choice trades privacy against cost or convenience,
    privacy wins. Where privacy depends on a party we cannot control, that dependency is named rather than assumed
    away. *Held by:* the tests below, and D35 naming the boundary.
  - **A photograph leaves this machine only to be rendered, and carries only its pixels.** Tagging and captioning
    run here; the upload carries what decodes the image and its orientation, nothing more. *Held by:* the
    `image-generation:photo-metadata:*` tests.
  - **The rented machine keeps nothing, and proves who it is before it receives anything.** The photograph and the
    render live in its memory, and its host key is checked against the fingerprint it printed. *Held by:* the
    `pod-image:memory:*`, `pod-image:host-key:*` and `pod-image:telemetry:*` tests.
- **`docs/decisions.md`** gains, under *Infrastructure*:
  - **D34 · Renders stay on a pod.** A rented pod, reached through an SSH tunnel; serverless endpoints are declined.
    *Why:* serverless adds places a photograph can linger — the provider's job store, boot snapshots whose contents
    are undocumented, a gateway that decrypts in transit; the pod has one tunnel and nothing between. *Made by:*
    `0041`.
  - **D35 · The pod's operator is a trust boundary, accepted knowingly.** Whoever runs the machine can read its
    memory while a render runs, so the photograph is not encrypted: the key would sit in the same memory. *Why:* no
    program can hide memory from its host, and the provider offers no confidential computing; only local rendering
    removes the boundary. *Made by:* `0041`.
  - **D27** gains: a pod runs in its models volume's data centre, checked before the create; `0041` joins its
    *Made by*.
  - The *Infrastructure* preamble line about serverless goes.

### D6

**One boot.** `render.sh` on a synthetic portrait over both flows, on the operator's go: `up.sh` prints
`Host key verified`, the strict tunnel connects, the renders arrive, and the pod's `env`, read back with
`GET /v2/pods/{id}`, holds the switches. The refusals — mismatch, no line, another data centre, too small a
volume — are proved by tests that run `up.sh`'s functions against stubbed answers. Recorded in `acceptance.md` with
no pod id, address or fingerprint value. Ceiling 45 minutes and ~$0.30; planned at ~$0.10.

## Dependencies

None.

## Risks / Trade-offs

- **The log lags the boot** → the 60 s poll; `start.sh` prints the line before provisioning, minutes ahead of the
  tunnel.
- **A scan reaches the wrong machine and a lookalike prints the same fingerprint** → the fingerprint comes over the
  provider's authenticated API; forging it needs the provider's account.
- **Rate limits on the log read** → a read every 5 s for at most a minute, far inside the documented example policy.

## Verdict

**feasible** — a log read, a volume read and a scan in `up.sh`, a stricter tunnel, and prose, each held by a test.
