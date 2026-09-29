# Capability: `comfy-transport`

## Purpose

Talking to a running ComfyUI over HTTP — uploading the photo, queueing the workflow, waiting for the render, and
downloading the result — behind the `ComfyTransport` seam the suite fakes.

## Requirements

### Requirement: Hand-built multipart encoding

The system SHALL build a `multipart/form-data` body without a third-party dependency, declaring a boundary that
matches the body it produced and encoding fields and files in the wire format the server expects. It SHALL choose a
boundary that appears in no part of the body, and SHALL escape a double quote or a line break in a part's name or
filename.

A fixed boundary inside a part's bytes ends the part early, and a quote or a line break in a filename rewrites the
part's headers. Neither happens with today's names and photographs, and neither may.

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

### Requirement: Render completion polling

The system SHALL wait for a queued prompt to finish by polling the server's history, rather than assuming a render
is ready when it was submitted. It SHALL give up on a prompt whose record has not appeared within a fixed deadline,
recording the failure as transient, and SHALL refuse a prompt id that is not a non-empty string as permanent.

The transport supplies the call and the render stage supplies the loop. A wait with no bound is the one failure no
number can hold: a ComfyUI restarted in place loses the prompt, and the pod bills until someone notices.

#### Scenario: history is polled until the prompt completes
- **Key:** `comfy-transport:polling:polls-history-until-complete`
- **Layers:** unit
- **WHEN** a workflow is queued and the server does not report it finished immediately
- **THEN** the run keeps polling the history for that prompt until its record appears
- **AND** proceeds only once the render is actually complete

#### Scenario: an unfinished prompt is refused at the deadline
- **Key:** `comfy-transport:polling:an-unfinished-prompt-is-refused-at-the-deadline`
- **Layers:** unit
- **WHEN** the history does not list the prompt before the deadline passes
- **THEN** the render is refused as transient and recorded
- **AND** the refusal names the prompt id and the deadline, and points at the endpoint's own log

#### Scenario: a prompt id that is not a string is refused
- **Key:** `comfy-transport:polling:a-prompt-id-that-is-not-a-string-is-refused`
- **Layers:** unit
- **WHEN** the endpoint answers a submission with a prompt id that is not a non-empty string
- **THEN** the render is refused as permanent and recorded
- **AND** the history is never polled

### Requirement: Result retrieval

The system SHALL download the images the completed history record names, rather than guessing an output
path.

#### Scenario: the image named in the history is downloaded
- **Key:** `comfy-transport:retrieval:downloads-image-named-in-history`
- **Layers:** unit
- **WHEN** a prompt's history record names a generated image
- **THEN** that image is fetched by the identifiers the record supplied
- **AND** its bytes are written to the run's output

### Requirement: The server's runtime is read from its own report

The system SHALL read the ComfyUI, Python and PyTorch versions from the endpoint's own system report through
the same transport seam every other call uses, and SHALL classify a failure of that call exactly as it
classifies the others.

The render records what ran it, and only the server knows. Reading the report through the seam keeps the
offline stand-in able to answer it, so the suite stays offline.

#### Scenario: the transport reads the server's versions
- **Key:** `comfy-transport:runtime:the-report-is-read-through-the-seam`
- **Layers:** unit
- **WHEN** the system report is requested
- **THEN** the transport returns the ComfyUI, Python and PyTorch versions the server reports
- **AND** the offline stand-in answers the same request without a network

### Requirement: The transport ignores any proxy the environment names

The system SHALL send every request to the rendering endpoint at the address it was given, and SHALL ignore any
proxy the environment names.

The upload carries the photograph. A proxy exported for some other tool would receive it, and the reader's call
once sent every photograph off the machine that way.

#### Scenario: an exported proxy is not used
- **Key:** `comfy-transport:proxy:an-exported-proxy-is-ignored`
- **Layers:** unit
- **WHEN** the environment names an HTTP proxy and the transport calls the endpoint
- **THEN** the connection is opened to the endpoint's own address
- **AND** never to the proxy

### Requirement: Every request to the endpoint is bounded in time

The system SHALL give up on a request the endpoint does not answer within a fixed time, and SHALL classify it as a
transient failure that names the time and points at the endpoint's own log.

A socket with no timeout waits for ever on a pod that stopped answering, and the pod bills while it waits.

#### Scenario: an unanswered request is transient
- **Key:** `comfy-transport:timeout:an-unanswered-request-is-transient`
- **Layers:** unit
- **WHEN** the endpoint does not answer a request within the fixed time
- **THEN** the request is refused as transient
- **AND** the refusal names the time and points at the endpoint's own log

### Requirement: An endpoint's error text is quoted in printable characters only

The system SHALL keep only the printable characters of an endpoint's error body before quoting it in a refusal or
an error record.

The refusal is printed to a terminal and read by an agent; an escape sequence in it would act on either.

#### Scenario: control characters are dropped
- **Key:** `comfy-transport:error-text:control-characters-are-dropped`
- **Layers:** unit
- **WHEN** an endpoint's error body carries an escape sequence or a bell
- **THEN** the refusal and the error record quote the body without them
- **AND** its printable text remains
