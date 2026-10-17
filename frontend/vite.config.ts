import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// In development, proxy API calls to the FastAPI backend (python api.py).
// server.sh sets API_PORT when the backend runs on a port other than 8000.
export default defineConfig(({ mode }) => {
  const apiPort = loadEnv(mode, ".", "API_").API_PORT || "8000";
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": `http://127.0.0.1:${apiPort}`,
      },
    },
  };
});
