import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

function sessionLogPlugin() {
  return {
    name: 'session-log-server',
    configureServer(server) {
      server.middlewares.use('/api/sessions', (_req, res) => {
        try {
          const data = readFileSync(resolve(__dirname, '..', 'session_log.json'), 'utf-8')
          res.setHeader('Content-Type', 'application/json')
          res.end(data)
        } catch {
          res.setHeader('Content-Type', 'application/json')
          res.end('[]')
        }
      })
    }
  }
}

export default defineConfig({
  plugins: [react(), sessionLogPlugin()],
  server: { port: 5173 }
})
