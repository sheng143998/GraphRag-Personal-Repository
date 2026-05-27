import { createServer } from "vite";
import vue from "@vitejs/plugin-vue";

const server = await createServer({
  configFile: false,
  plugins: [vue()],
  optimizeDeps: {
    noDiscovery: true,
    include: []
  },
  server: {
    host: "0.0.0.0",
    port: 5173
  }
});

await server.listen();
server.printUrls();
