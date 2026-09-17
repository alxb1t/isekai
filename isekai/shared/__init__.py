"""Primitives with no domain of their own, used on both sides of the pipeline.

No re-exports and no code: a group is a filing decision, and re-exporting
through it is how a nested package acquires the import cycles this one has none
of (design.md D2).
"""
