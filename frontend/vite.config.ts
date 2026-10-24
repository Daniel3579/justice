import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const API = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/generate": API,
      "/chat": API,
      "/chats": API,
      "/export": API,
      "/auth": API,
      "/me": API,
    },
  },
});
