import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const devHost = process.env.VITE_DEV_HOST ?? "127.0.0.1";
const devPort = Number.parseInt(process.env.VITE_DEV_PORT ?? "3000", 10);

export default defineConfig({
  plugins: [react()],
  server: {
    host: devHost,
    port: Number.isFinite(devPort) ? devPort : 3000,
    strictPort: false,
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true
      }
    }
  }
});
