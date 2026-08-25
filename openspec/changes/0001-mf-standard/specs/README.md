# Spec delta — **N-A**

This change carries **no spec delta**. It adds no behavioural capability: it relocates a config file, pins the
toolchain, adds a `Makefile` target, writes documentation and annotates existing tests. Every module under
`isekai/` comes out of it functionally identical — the only edits to source are import ordering normalised by
`ruff --select I` in phase 3.

The behaviour this milestone *documents* is behaviour the repo **already ships**, so it is written directly into
the living spec at `openspec/specs/<capability>/spec.md` (phase 5) rather than staged here as an
`## ADDED Requirements` block. A delta describes what a change changes; a backfill describes what is already
true, and `sdd:specs-tree` checks the living tree rather than an unfolded delta. See `design.md` §1.

Precedent for an N-A delta: `0004-planning-skills`.
