# Capability: `model-registry`

Selecting a model by name at the CLI and resolving it to everything the run needs: the workflow JSON to load, the
injection adapter that wires the photo and prompt into that JSON, and — for the img2img family — the mutation
seam that varies its dials.

**Source:** `isekai/models.py` · **Tests:** `tests/test_model_dispatch.py`

Each model owns its own workflow JSON and its own injection adapter (a plain-function Strategy), resolved through
a name→`Model` registry. Every version of the pipeline extends the previous one: **nothing is removed, and all
models stay selectable.**

## Requirements

### Requirement: Name resolution

The system SHALL resolve each supported model name to its own workflow JSON, and SHALL refuse an unknown name
rather than proceeding with a default.

#### Scenario: `qwen` resolves to the Qwen-Image-Edit workflow
- **Key:** `model-registry:name-resolution:qwen-resolves-to-its-workflow`
- **Layers:** unit
- **WHEN** the registry is asked for the model named `qwen`
- **THEN** it returns a model whose workflow path is `workflows/qwen-image-edit.json`

#### Scenario: `animagine` resolves to the Animagine + InstantID workflow
- **Key:** `model-registry:name-resolution:animagine-resolves-to-its-workflow`
- **Layers:** unit
- **WHEN** the registry is asked for the model named `animagine`
- **THEN** it returns a model whose workflow path is `workflows/animagine-instantid.json`

#### Scenario: `animagine-i2i` resolves to the img2img workflow
- **Key:** `model-registry:name-resolution:animagine-i2i-resolves-to-its-workflow`
- **Layers:** unit
- **WHEN** the registry is asked for the model named `animagine-i2i`
- **THEN** it returns a model whose workflow path is `workflows/animagine-i2i.json`

#### Scenario: `animagine-i2i-cn` resolves to the ControlNet workflow
- **Key:** `model-registry:name-resolution:animagine-i2i-cn-resolves-to-its-workflow`
- **Layers:** unit
- **WHEN** the registry is asked for the model named `animagine-i2i-cn`
- **THEN** it returns a model whose workflow path is `workflows/animagine-i2i-cn.json`

#### Scenario: an unknown model name is rejected
- **Key:** `model-registry:name-resolution:unknown-name-rejected`
- **Layers:** unit
- **WHEN** the registry is asked for a name that is not registered
- **THEN** the process exits rather than falling back to a default model

#### Scenario: the rejection message tells the user how to correct the flag
- **Key:** `model-registry:name-resolution:unknown-name-message-guides-the-user`
- **Layers:** unit
- **WHEN** the registry rejects an unregistered name
- **THEN** the exit message quotes the rejected name
- **AND** lists every registered model name, so the flag can be corrected without reading the source
- **AND** contains no literal `$` — the message is built by interpolation, so a surviving dollar sign means a
  shell-style `${…}` has leaked into the f-string

### Requirement: Injection adapter pairing

The system SHALL pair each model with the injection adapter that knows how to wire an uploaded photo and a prompt
into that model's graph, so that adding a model does not require editing a shared injector.

#### Scenario: Qwen is paired with the Qwen injector
- **Key:** `model-registry:injector-pairing:qwen-uses-qwen-injector`
- **Layers:** unit
- **WHEN** the registry resolves `qwen`
- **THEN** the model's injector is the Qwen injection adapter

#### Scenario: Animagine is paired with the Animagine injector
- **Key:** `model-registry:injector-pairing:animagine-uses-animagine-injector`
- **Layers:** unit
- **WHEN** the registry resolves `animagine`
- **THEN** the model's injector is the Animagine injection adapter

#### Scenario: the img2img model reuses the Animagine injector unchanged
- **Key:** `model-registry:injector-pairing:i2i-reuses-animagine-injector`
- **Layers:** unit
- **WHEN** the registry resolves `animagine-i2i`
- **THEN** the model's injector is the same Animagine injection adapter, not a variant of it
- **AND** the node trace the injector walks is therefore unchanged by the switch to img2img

#### Scenario: the ControlNet model reuses the Animagine injector unchanged
- **Key:** `model-registry:injector-pairing:cn-reuses-animagine-injector`
- **Layers:** unit
- **WHEN** the registry resolves `animagine-i2i-cn`
- **THEN** the model's injector is the same Animagine injection adapter
- **AND** the generalised conditioning trace serves the whole InstantID family, including graphs whose ControlNet
  apply nodes sit inside the conditioning path

### Requirement: Mutation seam pairing

The system SHALL attach the workflow-mutation seam only to the models whose dials are meant to vary, and SHALL
leave the earlier models without one — mutation is a per-model capability, not a global behaviour.

#### Scenario: the img2img model carries the mutation seam
- **Key:** `model-registry:mutation-pairing:i2i-carries-the-seam`
- **Layers:** unit
- **WHEN** the registry resolves `animagine-i2i`
- **THEN** the model carries the mutation function, so its dials can be varied across a run

#### Scenario: the ControlNet model carries the mutation seam
- **Key:** `model-registry:mutation-pairing:cn-carries-the-seam`
- **Layers:** unit
- **WHEN** the registry resolves `animagine-i2i-cn`
- **THEN** the model carries the mutation function

#### Scenario: the earlier models carry no mutator
- **Key:** `model-registry:mutation-pairing:earlier-models-have-no-mutator`
- **Layers:** unit
- **WHEN** the registry resolves `qwen` or `animagine`
- **THEN** the model carries no mutator
- **AND** a run of those models is unaffected by the mutation seam existing
