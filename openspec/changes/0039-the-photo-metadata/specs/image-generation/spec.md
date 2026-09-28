## ADDED Requirements

### Requirement: A photograph leaves the machine without its metadata

The system SHALL send a photograph to the rendering endpoint carrying only the blocks that decode its pixels, its
colour profile and its orientation, with every other block and any data after the image's end removed. It SHALL
leave the compressed image data unchanged, SHALL leave the run's own copy of the photograph unchanged, and SHALL
refuse a photograph it cannot walk to its end rather than send it whole.

A camera writes the position, the time and the device into the file, and a phone may append a video or a depth map
after the image. The render needs none of it, and the upload is the one place the photograph leaves the machine.

#### Scenario: the endpoint receives no metadata
- **Key:** `image-generation:photo-metadata:no-metadata-leaves-the-machine`
- **Layers:** unit
- **WHEN** a photograph carrying EXIF, XMP, IPTC, a comment and data after its end is rendered
- **THEN** the bytes uploaded carry none of them
- **AND** the upload keeps the photograph's name

#### Scenario: the orientation survives
- **Key:** `image-generation:photo-metadata:the-orientation-survives`
- **Layers:** unit
- **WHEN** a photograph with an orientation other than upright is stripped
- **THEN** the stripped photograph declares the same orientation
- **AND** a photograph that is upright carries no metadata block at all

#### Scenario: the pixels are unchanged
- **Key:** `image-generation:photo-metadata:the-pixels-are-unchanged`
- **Layers:** unit
- **WHEN** a JPEG or a PNG is stripped
- **THEN** it decodes to the same pixels as the original

#### Scenario: the run's copy keeps its bytes
- **Key:** `image-generation:photo-metadata:the-runs-copy-is-untouched`
- **Layers:** unit
- **WHEN** a photograph is rendered
- **THEN** the run's copy of it is byte for byte what it was

#### Scenario: a photograph that cannot be walked is refused, not sent
- **Key:** `image-generation:photo-metadata:an-unwalkable-photograph-is-refused`
- **Layers:** unit
- **WHEN** a photograph's segments or chunks cannot be read to the image's end
- **THEN** the render is refused and recorded, naming the photograph
- **AND** nothing is uploaded
