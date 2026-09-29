## MODIFIED Requirements

### Requirement: Hand-built multipart encoding

The system SHALL build a `multipart/form-data` body without a third-party dependency, declaring a boundary that
matches the body it produced and encoding fields and files in the wire format the server expects. It SHALL choose a
boundary that appears in no part of the body, and SHALL escape a double quote or a line break in a part's name or
filename.

The transport is on the entry point's import graph, which loads no third-party package
([D20](../../../docs/decisions.md#d20--the-entry-point-loads-no-third-party-package)). A fixed boundary inside a
part's bytes ends the part early, and a quote or a line break in a filename rewrites the part's headers.

#### Scenario: the content type declares the same boundary the body uses
- **Key:** `comfy-transport:multipart:content-type-declares-boundary`
- **Layers:** unit
- **WHEN** a multipart body is built
- **THEN** the returned content type names the boundary that separates the body's parts

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
- **AND** no text encoding is applied to them

#### Scenario: the boundary appears in no part
- **Key:** `comfy-transport:multipart:the-boundary-appears-in-no-part`
- **Layers:** unit
- **WHEN** a part's bytes contain the first boundary drawn
- **THEN** another boundary is drawn
- **AND** the boundary the body declares appears in none of its parts

#### Scenario: a name's quote and line breaks are escaped
- **Key:** `comfy-transport:multipart:names-are-escaped`
- **Layers:** unit
- **WHEN** a filename carries a double quote, a carriage return or a line feed
- **THEN** the part's header carries each of them percent-encoded
- **AND** the part's headers end where the encoder ends them

### Requirement: Result retrieval

The system SHALL download the images the completed history record names, rather than guessing an output
path.

The server names its outputs, and the history record is where it says what it named them.

#### Scenario: the image named in the history is downloaded
- **Key:** `comfy-transport:retrieval:downloads-image-named-in-history`
- **Layers:** unit
- **WHEN** a prompt's history record names a generated image
- **THEN** that image is fetched by the identifiers the record supplied
- **AND** its bytes are written to the run's output

### Requirement: The transport ignores any proxy the environment names

The system SHALL send every request to the rendering endpoint at the address it was given, and SHALL ignore any
proxy the environment names.

The upload carries the photograph, and a proxy exported for some other tool would receive it
([D6](../../../docs/decisions.md#d6--ollama-at-a-fixed-local-address-on-a-checked-model)).

#### Scenario: an exported proxy is not used
- **Key:** `comfy-transport:proxy:an-exported-proxy-is-ignored`
- **Layers:** unit
- **WHEN** the environment names an HTTP proxy and the transport calls the endpoint
- **THEN** the connection is opened to the endpoint's own address
- **AND** never to the proxy
