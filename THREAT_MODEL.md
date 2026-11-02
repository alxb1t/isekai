# Threat model

What isekai protects, whom it trusts, where work enters, and what it leaves to others. Security review reads this
first. The rules are [`docs/principles.md`](docs/principles.md#privacy)'s privacy principles and `AGENTS.md`'s
guardrails; a link here names the decision in force.

## Worth protecting

| what | why | held by |
|---|---|---|
| The photographs and the likeness in them | every run copies one, and a render is of that person | ignored roots ([D18](docs/decisions.md#d18--runs-stay-out-of-what-git-tracks)), a source with no metadata ([D43](docs/decisions.md#d43--a-source-holds-pixels-and-orientation-only)) |
| `.env` and the RunPod key | the key can create and delete what bills | `.env` is gitignored; `.env.example` declares shape alone |
| The money a pod or a volume bills | the GPU and its volume are what costs here | a quoted limit and price ([D26](docs/decisions.md#d26--renders-run-on-a-rented-gpu)), the session's bounds ([D36](docs/decisions.md#d36--a-render-session-is-isekai-render)), a person's go |
| `main` | a release lands there, and the public repository is what is read | the gate, and a ruleset refusing a force-push and a deletion |

## Trust boundaries

```
 this machine ───── SSH tunnel ─────▶ rented pod ◀── its host's operator
  │  photographs · .env                memory holds photograph and render
  ├─ loopback ─▶ Ollama · review UI
  └─ fetches ──▶ npm · PyPI · weight mirrors · GHCR
```

- **This machine and the pod.** A photograph crosses to be rendered, as its pixels and orientation. The tunnel checks
  the pod's host key first. Renders stay on a pod ([D34](docs/decisions.md#d34--renders-stay-on-a-pod)).
- **The pod and its operator.** Whoever runs the machine can read its memory during a render. This is accepted
  knowingly ([D35](docs/decisions.md#d35--the-pods-operator-is-a-trust-boundary-accepted-knowingly)).
- **This process and Ollama.** The address is fixed and loopback, and ignores a proxy. Whatever holds that port receives
  the photograph ([D6](docs/decisions.md#d6--ollama-at-a-fixed-local-address-on-a-checked-model)).
- **The browser and the UI.** Other sites open in the browser are outside the boundary
  ([D24](docs/decisions.md#d24--the-review-ui-serves-only-this-machine)).
- **What is fetched.** Packages are pinned exactly ([D22](docs/decisions.md#d22--dependencies-are-declared-and-pinned)), a system
  dependency refuses when missing ([D23](docs/decisions.md#d23--system-dependencies-refuse-rather-than-being-assumed)), and the image
  is pinned by digest ([D28](docs/decisions.md#d28--the-image-carries-code-the-volume-carries-weights)).

## Entry points

- **A worker's reach.** A coding agent runs in a worktree that holds tracked files and what `make setup` fetched. The
  primary checkout beside it holds `.env`, `.inputs/` and `.data/`. A worker spends nothing without a phase marked
  metered or a person's go, and commits no secret, pod id or real path.
- **`isekai render` and `gpunit`.** The one act that makes a pod, and it hands `.env` to gpunit. Free work runs first.
  The app's Render runs it as a child after its quote ([D4](docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children)).
- **An upload.** A file imported into the library is a source: it is stripped and verified before it is kept, or left
  out unless the operator imports it as it is. The upload to the pod carries what decodes the image and its orientation.
- **A pod.** It boots the pinned digest with telemetry off and keeps the photograph and render in memory. It stops
  itself at the session's limit, so a lost laptop does not bill past it.
- **The review UI.** It answers on loopback, checks `Host` and `Origin`, and takes `ISEKAI_WIRING` from the environment
  alone, after the runs-root check ([D41](docs/decisions.md#d41--the-test-seam-is-a-factory-named-in-the-environment)).

## Out of scope

- Reading a pod's memory or its host's swap during a render: only rendering locally removes it.
- A compromised operator machine: it holds the photographs and the key already.
- A weight mirror publishing bad weights under a pinned digest's name: a pin freezes bytes, not intent
  ([D27](docs/decisions.md#d27--the-models-live-on-a-network-volume)).
- What the operator chooses to render ([D33](docs/decisions.md#d33--the-operator-decides-what-is-rendered)).
- A hosted service, other users and access control: the UI serves one operator on one machine.
