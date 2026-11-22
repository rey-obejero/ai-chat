FROM node:22-alpine AS build

WORKDIR /app
RUN corepack enable

COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
COPY frontend/package.json frontend/package.json
COPY e2e/package.json e2e/package.json
RUN pnpm install --frozen-lockfile

COPY frontend frontend
RUN pnpm --filter @ai-chat/frontend build

FROM caddy:2-alpine
COPY --from=build /app/frontend/dist /srv/web
