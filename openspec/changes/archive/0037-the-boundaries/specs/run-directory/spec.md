## ADDED Requirements

### Requirement: A run's photograph is named inside the run

The system SHALL refuse a run whose frame names its photograph with anything but one plain filename, or lacks the
photograph's name or digest, naming the frame and its remedy. It SHALL NOT read, serve or send a file outside the
run on the frame's word.

The frame is a file on disk. A name holding a separator or `..` would point the run at any image on the machine,
which the review surface serves and the render uploads.

#### Scenario: a name that leaves the run is refused
- **Key:** `run-directory:frame:a-name-that-leaves-the-run-is-refused`
- **Layers:** unit
- **WHEN** a frame's photograph name holds a path separator, is `..`, or is absolute
- **THEN** reading the run's photograph is refused naming the frame
- **AND** no file outside the run is opened

#### Scenario: a photograph that is a link is refused
- **Key:** `run-directory:frame:a-photograph-that-is-a-link-is-refused`
- **Layers:** unit
- **WHEN** the file a frame names as its photograph is a symbolic link
- **THEN** reading the run's photograph is refused naming the frame and its remedy
- **AND** the file the link points at is not opened

#### Scenario: a frame without its photograph is refused
- **Key:** `run-directory:frame:a-frame-without-its-photograph-is-refused`
- **Layers:** unit
- **WHEN** a frame lacks the photograph block, its name or its digest
- **THEN** the run is refused naming the frame and the missing key
- **AND** the batch's other photographs go on
