import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiProxy = {
  "/api": {
    target: "http://127.0.0.1:5050",
    changeOrigin: true,
  },
};

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { ...apiProxy },
  },
  /** Same as dev: `vite preview` otherwise `/api/*` never reaches web_api.py */
  preview: {
    proxy: { ...apiProxy },
  },
});
