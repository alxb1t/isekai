## REMOVED Requirements

### Requirement: Every command a skill names is one this build accepts

**Reason:** the repository holds no agent skill: `run-flows` and `compare-renders` are deleted, because the browser
surface is the tool that runs a batch.

**Migration:** run the verbs directly — `tag`, `caption`, `sheet`, `review`, `approve`, `render` and `compare`, each
covered by the `cli` capability's parser scenarios; review in `isekai ui`.
