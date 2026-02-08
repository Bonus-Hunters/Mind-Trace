import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
  outDir: 'dist',
  rollupOptions: {
    output: {
      entryFileNames: `assets/[name].js`, // This forces the name to be index.js
      chunkFileNames: `assets/[name].js`,
      assetFileNames: `assets/[name].[ext]`,
    },
  },
}
})
