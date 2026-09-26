## REMOVED Requirements

### Requirement: Every provisioned artifact's licence is recorded before it is relied on

**Reason**: The operator set licences out of scope for now. The record it required,
`scripts/eval_licences.md`, is deleted with the tests that read it; the AGPL guards on the scorer's
dependencies stay, because they protect the repository's own licence rather than a record of others'.

**Migration**: None. No verb, flag, file a run writes, or refusal changes; the record's history stays in git.
