import { defineConfig } from "vite";

export default defineConfig({
  // Relative asset paths, so the built bundle works from any mount point —
  // the container serves it, and a static host might serve it from a subpath.
  base: "./",
  // A fixed port so the Playwright harness and the README can name one URL.
  server: { port: 5173, strictPort: true },
});
