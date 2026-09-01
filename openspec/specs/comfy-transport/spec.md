# Capability: `comfy-transport`

Talking to a running ComfyUI over HTTP: uploading the photo, queueing the workflow, waiting for the render, and
downloading the result.

**Source:** `isekai/multipart.py`, `isekai/comfy_client.py`, `isekai/pipeline.py` ·
**Tests:** `tests/test_multipart.py`, `tests/test_polling.py`

The transport is an **injectable seam** behind a Protocol, so the pipeline can be driven by a fake. The runtime
is **stdlib-only** — the multipart body is built by hand rather than pulled from a dependency, which is why its
wire format is specified here rather than delegated to a library's contract. **No test in this capability reaches
a real GPU or the network**; the transport is fully mocked, and actual diffusion quality is judged by eye on a
live pod.

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

> Polling and output selection live in `isekai/pipeline.py::_render`; `comfy_client.history()` is a single
> unconditional GET. The transport module supplies the calls, the pipeline supplies the loop.

### Requirement: Render completion polling

The system SHALL wait for a queued prompt to finish by polling the server's history, rather than assuming a
render is ready when it was submitted.

#### Scenario: history is polled until the prompt completes
- **Key:** `comfy-transport:polling:polls-history-until-complete`
- **Layers:** unit
- **WHEN** a workflow is queued and the server does not report it finished immediately
- **THEN** the run keeps polling the history for that prompt until its record appears
- **AND** proceeds only once the render is actually complete

### Requirement: Result retrieval

The system SHALL download the images the completed history record names, rather than guessing an output path.

#### Scenario: the image named in the history is downloaded
- **Key:** `comfy-transport:retrieval:downloads-image-named-in-history`
- **Layers:** unit
- **WHEN** a prompt's history record names a generated image
- **THEN** that image is fetched by the identifiers the record supplied
- **AND** its bytes are written to the run's output
