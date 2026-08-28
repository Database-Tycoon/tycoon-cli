import { defineConfig } from "@playwright/test";

/**
 * channel: 'chrome' + SwiftShader is the proven headless-WebGL recipe (C0):
 * the installed Google Chrome instead of a ~100 MB Playwright browser
 * download, software GL so no GPU is assumed. See the
 * `verifying-web-uis-headless` skill for the full rationale.
 *
 * PORT ISOLATION (`DATABASE_TYCOON_WEB_PORT`, default 5173): parallel worktrees must not
 * share one dev server. `reuseExistingServer` will happily attach to another
 * checkout's :5173, and then every screenshot and every assertion describes
 * code that is not yours — a trap this repo has already sprung. A worktree
 * agent exports `DATABASE_TYCOON_WEB_PORT=<its own port>`; this config and
 * `e2e/shot.mjs` both follow it, and `--strictPort` turns a collision into an
 * error instead of a silent shift to the next free port.
 */
const PORT = Number(process.env.DATABASE_TYCOON_WEB_PORT ?? 5173);

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",
  timeout: 60_000,
  // WebGL rendering through one Chrome instance; parallel launches have
  // deadlocked on this machine before. Serial is fast enough at this size.
  workers: 1,
  use: {
    baseURL: `http://localhost:${PORT}`,
    channel: "chrome",
    headless: true,
    launchOptions: {
      args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
    },
    viewport: { width: 1280, height: 800 },
  },
  webServer: {
    command: `npm run dev -- --port ${PORT} --strictPort`,
    port: PORT,
    reuseExistingServer: true,
  },
});
