import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Relative base: the same build works on GitHub Pages (/<repo>/) and locally.
export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss()],
  // MIT/BSD/ISC require their notices to travel with the bundle, and minification drops them: emit the full
  // licence texts of every bundled package. Not under .vite/, because upload-pages-artifact skips hidden folders.
  build: { license: { fileName: 'licence-trecih-strana.txt' } },
})
