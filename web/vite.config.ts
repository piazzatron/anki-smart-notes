import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  // The plugin's local server serves the built app at /app
  base: "/app/",
  build: {
    outDir: "../src/web/static",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      // Dev: the app runs on the Vite server but talks to the plugin's local
      // server. changeOrigin satisfies its localhost Host check.
      "/api": { target: "http://127.0.0.1:8766", changeOrigin: true },
    },
  },
})
