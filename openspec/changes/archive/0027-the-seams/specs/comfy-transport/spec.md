## MODIFIED Requirements

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
> `ComfyClient.history()` is a single unconditional GET. The transport module supplies the calls, the
> render stage supplies the loop.
