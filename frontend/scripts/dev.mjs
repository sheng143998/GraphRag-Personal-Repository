import { createServer } from "vite";
import vue from "@vitejs/plugin-vue";

const backendTarget = process.env.VITE_BACKEND_PROXY_TARGET ?? "http://localhost:8080";

const server = await createServer({
  configFile: false,
  plugins: [vue()],
  optimizeDeps: {
    noDiscovery: true,
    include: []
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
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
