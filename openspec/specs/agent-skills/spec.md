# Capability: `agent-skills`

## Purpose

The skills an AI agent follows to run the flows for the operator: which commands to run, where to stop for a
person, and what never to read — so an agent needs no lookup and spends little context.

## Requirements

### Requirement: Every command a skill names is one this build accepts

The system SHALL hold every `python -m isekai` command line a skill names against the build's own parser, so that
a skill naming a verb or flag the build does not accept fails the suite naming the skill and the line.

A skill lets an agent run the flows without reading the source, and it is worth that only while its commands are
true. A flag renamed in the parser and not in the skill sends the agent back to guessing.

#### Scenario: a skill's commands parse
- **Key:** `agent-skills:commands:every-command-parses`
- **Layers:** unit
- **WHEN** the suite reads each skill
- **THEN** every `python -m isekai` line in it is accepted by the build's parser

#### Scenario: a command the parser refuses fails the suite
- **Key:** `agent-skills:commands:a-stale-command-fails`
- **Layers:** unit
- **WHEN** a skill names a flag the parser does not accept
- **THEN** the check reports the skill and the line
