import { createServer } from "vite";
import react from "@vitejs/plugin-react";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const backendTarget = process.env.VITE_BACKEND_PROXY_TARGET ?? "http://localhost:8080";
const host = process.env.VITE_DEV_HOST ?? "127.0.0.1";
const port = Number.parseInt(process.env.VITE_DEV_PORT ?? "3000", 10);
const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const server = await createServer({
  root,
  configFile: false,
  plugins: [react()],
  optimizeDeps: {
    include: ["@vitejs/plugin-react", "react", "react-dom", "react-router-dom", "lucide-react", "zustand"]
  },
  server: {
    host,
    port: Number.isFinite(port) ? port : 3000,
    strictPort: false,
    proxy: {
      "/api": {
        target: backendTarget,
        changeOrigin: true
      }
    }
  }
});

await server.listen();
server.printUrls();
