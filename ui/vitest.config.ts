import { defineConfig, mergeConfig } from 'vitest/config'
import vite from './vite.config.ts'

// The composables run in node: they touch `fetch` and timers, never the DOM, and
// each test stubs what it reaches. The page itself is tested in `tests/e2e/`.
export default mergeConfig(
  vite,
  defineConfig({
    test: { include: ['src/**/*.test.ts'], environment: 'node' },
  }),
)
