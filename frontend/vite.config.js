import { fileURLToPath, URL } from 'node:url'
import { readFile } from 'node:fs/promises'
import { extname, join } from 'node:path'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'

const vadRuntimeFiles = new Set([
  'ort-wasm-simd-threaded.mjs',
  'ort-wasm-simd-threaded.wasm',
  'ort-wasm-simd-threaded.jsep.mjs',
  'ort-wasm-simd-threaded.jsep.wasm',
  'silero_vad_v5.onnx',
  'vad.worklet.bundle.min.js',
])

function vadRuntimePlugin() {
  const vadDirectory = fileURLToPath(new URL('./public/vad-runtime-v2', import.meta.url))
  const contentTypes = {
    '.js': 'application/javascript',
    '.mjs': 'application/javascript',
    '.wasm': 'application/wasm',
    '.onnx': 'application/octet-stream',
  }

  return {
    name: 'serve-vad-runtime',
    configureServer(server) {
      server.middlewares.use('/vad-runtime', async (request, response, next) => {
        const filename = decodeURIComponent((request.url || '').split('?')[0]).replace(/^\//, '')
        if (!vadRuntimeFiles.has(filename)) return next()
        try {
          const data = await readFile(join(vadDirectory, filename))
          response.statusCode = 200
          response.setHeader('Content-Type', contentTypes[extname(filename)] || 'application/octet-stream')
          response.setHeader('Cache-Control', 'no-cache')
          response.end(data)
        } catch (error) {
          next(error)
        }
      })
    },
  }
}

export default defineConfig({
  plugins: [
    vadRuntimePlugin(),
    vue(),
    vueDevTools(),
    tailwindcss(),
  ],
  build: {
    outDir: fileURLToPath(new URL('../backend/static/frontend', import.meta.url)),
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
