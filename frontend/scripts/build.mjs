import { build } from "vite";
import vue from "@vitejs/plugin-vue";

await build({
  configFile: false,
  plugins: [vue()]
});
