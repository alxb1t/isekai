## ADDED Requirements

### Requirement: A comparison page shows every run's photograph beside its renders

The system SHALL offer a verb that, given a batch directory holding a `runs/` directory, writes one HTML page into
that batch directory showing, for each run, the run's photograph and every render of each flow's latest approval,
each render labelled by its flow and seed and carrying the positive prompt it came from, with each flow's caption
and a run without a render marked. The page SHALL link every image by a path relative to itself and SHALL embed none. The verb SHALL print
only the page's path, and SHALL refuse, naming the directory, a batch directory that holds no `runs/`.

A batch of photographs ends in a question a person answers by eye: which flow kept whom. The answer used to be a
page written by hand from the run directories, and an agent asked to write it had to read them — the reading the
flow skills exist to avoid. Linking rather than embedding keeps the page small and keeps every image where the run
put it; printing only the path is what lets an agent hand the page over without reading it.

#### Scenario: the page links each photograph to its renders
- **Key:** `cli:compare:the-page-links-photographs-to-renders`
- **Layers:** unit
- **WHEN** the verb is run on a batch whose runs hold renders from more than one flow
- **THEN** the page holds one entry per run, with its photograph and each flow's renders labelled by flow and seed
- **AND** every image is linked by a relative path and none is embedded

#### Scenario: a run with no render is marked
- **Key:** `cli:compare:a-run-without-a-render-is-marked`
- **Layers:** unit
- **WHEN** a run in the batch has no render for a flow
- **THEN** its entry says so for that flow
- **AND** the page is still written

#### Scenario: the verb prints only the page's path
- **Key:** `cli:compare:only-the-path-is-printed`
- **Layers:** unit
- **WHEN** the verb writes the page
- **THEN** its standard output is the page's path and nothing else

#### Scenario: a batch with no runs is refused
- **Key:** `cli:compare:a-batch-without-runs-is-refused`
- **Layers:** unit
- **WHEN** the verb is given a directory that holds no `runs/`
- **THEN** it refuses naming the directory
- **AND** nothing is written
