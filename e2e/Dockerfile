# The Playwright runner for the containerized end-to-end suite. It carries the
# browser, so a machine that can run Docker needs nothing else. The base image
# tag must match the @playwright/test version in pnpm-lock.yaml, or the bundled
# browser build will not match the driver.
FROM mcr.microsoft.com/playwright:v1.63.0-noble

WORKDIR /app
RUN corepack enable

# Only the e2e package's dependencies are installed; the suite drives the app
# from across the network, so it does not need the front-end.
COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
COPY front-end/package.json front-end/package.json
COPY e2e/package.json e2e/package.json
RUN pnpm install --frozen-lockfile --filter @ai-chat/e2e

COPY e2e e2e

WORKDIR /app/e2e
CMD ["pnpm", "exec", "playwright", "test"]
