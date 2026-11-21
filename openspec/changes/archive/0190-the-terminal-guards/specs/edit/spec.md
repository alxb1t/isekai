## MODIFIED Requirements

### Requirement: A discard takes edits

The system SHALL delete, with a discarded render, every edit of its seed: images, records and composites, before
it decides whether the group and its approval go. Given an edit image's path it SHALL delete that edit and every
edit whose source chain reaches it. Both SHALL be refused while a render session holds the image's runs root, a
collection's or not.

An edit left in the group would keep the group and its approval alive, unseen on the hub
([D50](../../../docs/decisions.md#d50--the-last-render-takes-its-approval-and-a-flow-holds-only-its-own-files)).

#### Scenario: a render takes its edits
- **Key:** `edit:discard:a-render-takes-its-edits`
- **Layers:** unit
- **WHEN** a render with two chained edits is discarded
- **THEN** the render and both edits' images, records and composites are deleted

#### Scenario: the last render with an edit takes its approval
- **Key:** `edit:discard:the-last-render-with-an-edit-takes-its-approval`
- **Layers:** unit
- **WHEN** the only render of an approval, which has an edit, is discarded
- **THEN** the group and the approval go as they do without an edit

#### Scenario: an edit takes its chain
- **Key:** `edit:discard:an-edit-takes-its-chain`
- **Layers:** unit
- **WHEN** the first of two chained edits is discarded
- **THEN** both edits are deleted and the render stays

#### Scenario: a running session refuses it
- **Key:** `edit:discard:a-running-session-refuses-it`
- **Layers:** unit
- **WHEN** an edit's path is discarded while a render session holds the collection
- **THEN** nothing is deleted

#### Scenario: a running session beside a plain runs root refuses it
- **Key:** `edit:discard:a-session-beside-a-plain-runs-root-refuses-it`
- **Layers:** unit
- **WHEN** an edit's path is discarded under a runs root no collection holds, while a render session holds the lock of
  its record beside that root
- **THEN** nothing is deleted
