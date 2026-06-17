import { createServer } from "vite";
import react from "@vitejs/plugin-react";

const backendTarget = process.env.VITE_BACKEND_PROXY_TARGET ?? "http://localhost:8080";

const server = await createServer({
  configFile: false,
  plugins: [react()],
  optimizeDeps: {
    include: ["@vitejs/plugin-react", "react", "react-dom", "react-router-dom", "lucide-react", "zustand"]
  },
  server: {
    host: "0.0.0.0",
    port: 5174,
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
