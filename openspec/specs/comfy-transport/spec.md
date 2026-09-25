# Capability: `comfy-transport`

## Purpose

Talking to a running ComfyUI over HTTP: uploading the photo, queueing the workflow, waiting for the render, and
downloading the result.

**Source:** `isekai/boundary/multipart.py`, `isekai/boundary/comfy_client.py`,
`isekai/boundary/comfy_types.py`, `isekai/pipeline/generate.py` ·
**Tests:** `tests/test_multipart.py`, `tests/test_generate.py`

The transport is an **injectable seam** behind a Protocol — `ComfyTransport`, declared in
`isekai/boundary/comfy_types.py` with no network in it, which is what lets the whole suite run against
`FakeComfyClient`. The transport is on `python -m isekai`'s import graph, which reaches no wheel, so the
multipart body is built by hand rather than pulled from a dependency, which is why its wire format is
specified here rather than delegated to a library's contract. **No test in this capability reaches a real GPU or the network**; the transport is fully
mocked, and actual diffusion quality is judged by eye on a live pod.

**Where the polling loop lives.** Until v0.15 this preamble pointed at a module and a test file that
were **deleted together in `8baf2b3` at v0.14**, with the old render path. The loop that submits a
workflow and waits for it is `isekai/pipeline/generate.py`'s `render`, and the scenarios that hold it
are in `tests/test_generate.py`. The pointer was stale rather than wrong, so this is a redirect.

## Requirements

### Requirement: Hand-built multipart encoding

The system SHALL build a `multipart/form-data` body without a third-party dependency, declaring a boundary that
matches the body it produced and encoding fields and files in the wire format the server expects.

#### Scenario: the content type declares the same boundary the body uses
- **Key:** `comfy-transport:multipart:content-type-declares-boundary`
- **Layers:** unit
- **WHEN** a multipart body is built
- **THEN** the returned content type names the boundary that separates the body's parts
- **AND** a mismatch here would make the server reject an otherwise valid body

#### Scenario: fields and files are encoded as wire format
- **Key:** `comfy-transport:multipart:encodes-fields-and-files`
- **Layers:** unit
- **WHEN** a body is built from form fields and file parts
- **THEN** each part carries its content-disposition header with the part's name, each file part carries its
  filename and content type, and the body is terminated by the closing boundary

#### Scenario: binary file data survives verbatim
- **Key:** `comfy-transport:multipart:preserves-binary-verbatim`
- **Layers:** unit
- **WHEN** a file part carries arbitrary binary data
- **THEN** those bytes appear in the body unchanged
- **AND** no text encoding is applied to them, so a photo is not corrupted in transit

> Polling and output selection live in `isekai/pipeline/generate.py`'s `render`;
> `comfy_client.history()` is a single unconditional GET. The transport module supplies the calls, the
> render stage supplies the loop.

### Requirement: Render completion polling

The system SHALL wait for a queued prompt to finish by polling the server's history, rather than
assuming a render is ready when it was submitted.

The transport supplies the call and the render stage supplies the loop. That division is unchanged by
this version; what changes is which module holds the loop, and therefore which suite exercises it.

#### Scenario: history is polled until the prompt completes
- **Key:** `comfy-transport:polling:polls-history-until-complete`
- **Layers:** unit
- **WHEN** a workflow is queued and the server does not report it finished immediately
- **THEN** the run keeps polling the history for that prompt until its record appears
- **AND** proceeds only once the render is actually complete

### Requirement: Result retrieval

The system SHALL download the images the completed history record names, rather than guessing an output
path.

#### Scenario: the image named in the history is downloaded
- **Key:** `comfy-transport:retrieval:downloads-image-named-in-history`
- **Layers:** unit
- **WHEN** a prompt's history record names a generated image
- **THEN** that image is fetched by the identifiers the record supplied
- **AND** its bytes are written to the run's output
