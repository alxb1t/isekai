## ADDED Requirements

### Requirement: The flow selects the reader implementation, and every way of getting that wrong is a refusal

The system SHALL select the reader implementation from the string the flow's manifest declares, SHALL
construct no implementation a flow has not asked for, and SHALL refuse — naming the implementations the
build carries — when a flow declares one it does not have. A flow declaring an implementation SHALL NOT
reach any other implementation by any path, including when the one it declared fails.

The standing rule that a producer names what actually made the artifact is only true if the selection
cannot silently miss. A two-branch test on the declared string would give an unrecognised implementation
the default one, producing a complete run on the wrong models with the artifact's own provenance record
disagreeing with the manifest that asked for it — silent, and it corrupts any later comparison between
the two. Resolving through a table of known strings makes an unrecognised one a refusal by construction
rather than by remembering to check. Constructing nothing until a flow asks is what keeps a machine with
one implementation available from needing the other to exist.

The implementations this build carries are not interchangeable and must not be treated as such: one
reaches a model over a network to a third party, the other over a socket to this machine. A run that
declared the second and got the first has spent money the operator did not authorise and produced an
artifact whose provenance is false.

#### Scenario: the declared implementation is the one that runs
- **Key:** `caption:selection:the-flow-names-the-implementation`
- **Layers:** unit
- **WHEN** a flow declaring an implementation is captioned
- **THEN** the caption's producer names that implementation
- **AND** no other implementation was constructed

#### Scenario: an implementation this build does not carry is refused naming the ones it does
- **Key:** `caption:selection:unknown-implementation-is-refused`
- **Layers:** unit
- **WHEN** a flow declares a reader implementation the build does not carry
- **THEN** the command refuses naming the implementations it does carry
- **AND** no caption is written and no attempt is recorded

#### Scenario: a flow declaring one implementation cannot reach another
- **Key:** `caption:selection:no-path-reaches-another-implementation`
- **Layers:** unit
- **WHEN** a flow declaring one implementation is captioned while every entry point of a different
  implementation is instrumented to fail loudly
- **THEN** the caption is produced without any of them being entered
- **AND** the same run with the other implementation's binary absent from the environment succeeds
  unchanged

### Requirement: A hosted model that is not running or not installed is refused before any attempt is spent

The system SHALL refuse, naming the command that would fix it, when the host serving a declared model
cannot be reached or reports that the model does not exist. It SHALL record no attempt against the
stage's retry budget for either condition, and SHALL make that check at the first call rather than when
the implementation is constructed.

A retry budget counts models tried and failed. A server that is not running and a model that was never
created are neither: both are the operator's single-command fix, and spending a budgeted attempt on them
leaves a run whose error records have to be deleted by hand before it can be resumed. This is the posture
the build already takes toward a missing binary, applied to a port and to a model name instead of a path
entry. Checking at first call rather than at construction is what lets a machine that will never use an
implementation avoid touching it at all.

#### Scenario: an unreachable host is refused and costs no attempt
- **Key:** `caption:reachability:unreachable-host-refuses-without-an-attempt`
- **Layers:** unit
- **WHEN** the host serving the declared reader is not answering
- **THEN** the command refuses naming what to start
- **AND** no attempt is recorded against the stage's budget

#### Scenario: a model the host does not have is refused naming how to create it
- **Key:** `caption:reachability:absent-model-names-how-to-create-it`
- **Layers:** unit
- **WHEN** the host reports that the declared model does not exist
- **THEN** the command refuses naming the command that would create or fetch it
- **AND** no attempt is recorded against the stage's budget

#### Scenario: the reachability check is not made until a flow asks
- **Key:** `caption:reachability:the-check-fires-at-first-call`
- **Layers:** unit
- **WHEN** a wiring is composed and no captioning is performed
- **THEN** no host is contacted and no binary is looked up
