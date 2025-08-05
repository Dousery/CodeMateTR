import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['@mui/material', '@mui/icons-material'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
    sourcemap: false,
    outDir: 'dist',
  },
  server: {
    historyApiFallback: true,
  },
  publicDir: 'public',
  define: {
    'process.env.NODE_ENV': '"production"',
  },
})
