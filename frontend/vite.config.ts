import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// В режиме разработки запросы к API проксируются на FastAPI (порт 8000),
// поэтому CORS настраивать не нужно. Адрес 127.0.0.1, а не localhost: на macOS localhost
// может уйти по IPv6, а uvicorn (host="0.0.0.0") слушает только IPv4.
const API = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/generate": API,
      "/auth": API,
      "/me": API,
    },
  },
});