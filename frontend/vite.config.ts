import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// http://localhost:8000 is Django
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
