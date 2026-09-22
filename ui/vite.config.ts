import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// `dist/` is where `bundle.ensure_built()` looks and what `app.py` mounts, so
// the output directory is a contract between this file and those two.
export default defineConfig({
  plugins: [vue()],
  build: { outDir: 'dist', emptyOutDir: true },
})
