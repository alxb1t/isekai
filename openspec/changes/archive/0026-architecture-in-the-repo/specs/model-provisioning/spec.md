## MODIFIED Requirements

### Requirement: The manifest declares every artifact the shipped graph requires

The manifest SHALL declare an entry for every model file a render of a tracked flow's graph loads,
including files that no field of the graph names — the annotator checkpoints a preprocessor node
fetches for itself. A graph that requires a file the manifest does not declare MUST fail the suite
offline, because the alternative is discovering it on a metered pod.

The graph the rule is stated over is the one the repository ships under `flows/<id>/graph.json`, not a
single path fixed here. A flow is the unit that owns a graph, so a rule naming one file by hand would
go stale the moment a second flow is added — and it would go stale silently, because a manifest check
against a graph that is no longer rendered still passes. Stating it over the tracked flows keeps the
check binding on whatever is actually rendered.

#### Scenario: a model filename named in the graph has a manifest entry
- **Key:** `model-provisioning:manifest-completeness:graph-filename-has-an-entry`
- **Layers:** unit
- **WHEN** the shipped graph names a model file in a node's inputs — a checkpoint, a ControlNet, an
  InstantID file, a detector or a pose estimator
- **THEN** the manifest declares an entry whose destination filename is that file
- **AND** a graph edited to name a file the manifest does not carry fails the check

#### Scenario: a preprocessor's own models are declared even though the graph never names them
- **Key:** `model-provisioning:manifest-completeness:preprocessor-models-are-declared`
- **Layers:** unit
- **WHEN** the graph contains a preprocessor node that downloads model files it exposes no field for
- **THEN** the manifest declares those files, resolved through a tracked mapping from node class to
  required filenames
- **AND** adding such a node without extending the mapping fails the check rather than passing
  silently

