FROM node:22-alpine AS build

WORKDIR /app
RUN corepack enable

COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
COPY front-end/package.json front-end/package.json
COPY e2e/package.json e2e/package.json
RUN pnpm install --frozen-lockfile

COPY front-end front-end
RUN pnpm --filter @ai-chat/front-end build

FROM caddy:2-alpine
COPY --from=build /app/front-end/dist /srv/web
