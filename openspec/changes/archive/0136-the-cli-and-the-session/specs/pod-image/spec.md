## MODIFIED Requirements

### Requirement: A render session reaches its tunnel without a proxy

`isekai render` SHALL reach the endpoint through its tunnel directly, ignoring any proxy the environment names.

The verb's own checks call the loopback address the tunnel listens on. A proxy exported for some other tool would
receive them, the endpoint would never seem to answer, and the session would bill its wait and refuse.

#### Scenario: the script's checks ignore an exported proxy
- **Key:** `pod-image:session:the-tunnel-is-reached-directly`
- **Layers:** unit
- **WHEN** `isekai render` asks the endpoint for its report with `http_proxy` exported
- **THEN** the request goes to the loopback address, through no proxy

#### Scenario: a port that already answers is refused before the session
- **Key:** `pod-image:session:a-busy-port-is-refused-before-the-session`
- **Layers:** unit
- **WHEN** something on this machine already answers on the port the tunnel listens on
- **THEN** `isekai render` is refused before any pod is rented
- **AND** the refusal names the command that shows what holds the port
