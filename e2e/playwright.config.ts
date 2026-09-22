import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  fullyParallel: true,
  // The whole suite shares one API process, one SuperTokens core and one
  // Postgres. Over-subscribing workers starves them and replies time out, so
  // the worker count is capped rather than left to the CPU heuristic.
  workers: 2,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      // Deterministic provider so the chat specs never call a real model.
      command: "node support/mock-llm-server.mjs",
      url: "http://localhost:4010/health",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      command: "pnpm --dir ../front-end dev --port 5173",
      url: "http://localhost:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: 'bash -lc "cd ../back-end && uv run uvicorn ai_chat.main:app --port 8000"',
      url: "http://localhost:8000/api/v1/health",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        LLM_API_KEY: "e2e-key",
        LLM_BASE_URL: "http://localhost:4010/v1",
        LLM_MODEL: "e2e/mock",
      },
    },
  ],
});
