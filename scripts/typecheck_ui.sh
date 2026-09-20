#!/usr/bin/env bash
#
# The gate's browser half, and the only mechanical check it has.
#
# `vue-tsc --noEmit` is declared in `ui/package.json` and was in no gate command,
# so a phase whose whole product is browser code could end "green" while the
# bundle did not compile (design.md D22). This script is what the `gate` array in
# .minions/minions.toml names, because the array's entries run from the
# repository root and `npm run` needs the package directory -- and because a
# missing toolchain has to refuse by name rather than exit 127 with
# `vue-tsc: command not found`.
#
# The refusal copies `isekai/interface/ui/bundle.py`'s shape: say what is absent,
# say what installs it, say which part of the system needs it. `npm install` is
# never run for you here for bundle.py's own reason -- it fetches arbitrary
# third-party packages, and `ui/node_modules/` is an ignored root precisely
# because nothing in this repository restores it silently.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v npm >/dev/null 2>&1; then
  echo "typecheck_ui: 'npm' is not on PATH, and the gate's browser typecheck" >&2
  echo "  cannot run without it; install Node.js (https://nodejs.org), then run" >&2
  echo "  this command again -- every other gate command is unaffected" >&2
  exit 1
fi

if [ ! -d "$root/ui/node_modules" ]; then
  echo "typecheck_ui: ui/node_modules/ is absent and vue-tsc cannot run without" >&2
  echo "  it; run \`npm install\` in ui/ -- it is not done for you, because it" >&2
  echo "  fetches third-party packages" >&2
  exit 1
fi

cd -- "$root/ui"
exec npm run typecheck
