// vitest reads its root's config alone. Started at the repository's root it finds this file and stops,
// where it would write a root `node_modules/` and skip `ui/`'s config.
throw new Error(
  'vitest is not started at the repository root. Run one file with `uv run python -m tools.test_ui ui/src/<name>.test.ts`.',
)
