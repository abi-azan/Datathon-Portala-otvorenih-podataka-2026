import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Relative base: the same build works on GitHub Pages (/<repo>/) and locally.
export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss()],
})
