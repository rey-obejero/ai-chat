import { defineConfig, devices } from "@playwright/test";

// When the suite runs in its own container (compose.e2e.yaml), the app, the
// mock providers, and SuperTokens are Compose services on the same network, so
// Playwright must not start its own. On the host it starts everything itself.
const inContainer = process.env.E2E_IN_CONTAINER === "1";

export default defineConfig({
  testDir: ".",
  fullyParallel: true,
  // The whole suite shares one API process, one SuperTokens core and one
  // Postgres. Over-subscribing workers starves them and replies time out, so
  // the worker count is capped rather than left to the CPU heuristic.
  workers: 2,
  // Sign-in and sign-up round-trip through SuperTokens before the router
  // navigates; under parallel load the default 5s assertion budget is tight.
  expect: {
    timeout: 10_000,
  },
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  // In CI, keep the compact annotations GitHub renders and also write the HTML
  // report, which embeds traces and screenshots. The report is uploaded as an
  // artifact on failure, so a red run can be debugged without a re-run.
  reporter: process.env.CI
    ? [["github"], ["html", { open: "never" }]]
    : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  // In the container the app and the mocks are Compose services, so there is
  // nothing for Playwright to start; baseURL comes from E2E_BASE_URL.
  webServer: inContainer
    ? undefined
    : [
    {
      // Deterministic provider so the chat specs never call a real model.
      command: "node support/mock-llm-server.mjs",
      url: "http://localhost:4010/health",
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      // A real, local OIDC provider, so the social specs exercise discovery,
      // JWKS verification and the token exchange without reaching Google or
      // GitHub (ADR-0033).
      command: "node support/mock-idp-server.mjs",
      url: "http://localhost:4011/health",
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
        // The suite signs in many times from one address and shares buckets
        // across parallel workers; no e2e test asserts rate limiting, so it is
        // off here. The 429 path is covered by the back-end suite.
        RATE_LIMIT_ENABLED: "false",
        // The gated stand-in identity provider (ADR-0029). Off everywhere else.
        TEST_IDP_ENABLED: "true",
        TEST_IDP_BASE_URL: "http://localhost:4011",
        TEST_IDP_CLIENT_ID: "test-idp-client",
        TEST_IDP_CLIENT_SECRET: "test-idp-secret",
      },
    },
  ],
});
