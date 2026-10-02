FROM node:24-alpine AS builder

ARG API_PROXY_UPSTREAM=http://api:8000/api
ARG NEXT_PUBLIC_API_BASE_URL=/api
ARG NEXT_PUBLIC_ENVIRONMENT=development
ARG NPM_CONFIG_REGISTRY=https://packagefeedproxy.microsoft.io/npm/

ENV API_PROXY_UPSTREAM=${API_PROXY_UPSTREAM}
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
ENV NEXT_PUBLIC_ENVIRONMENT=${NEXT_PUBLIC_ENVIRONMENT}
ENV NPM_CONFIG_REGISTRY=${NPM_CONFIG_REGISTRY}
ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app
RUN npm install --global pnpm@10.6.3
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/domain/package.json ./packages/domain/package.json
COPY packages/ui/package.json ./packages/ui/package.json
RUN pnpm install --frozen-lockfile
COPY packages/domain/ ./packages/domain/
COPY apps/web/ ./apps/web/
COPY packages/ui/ ./packages/ui/
RUN pnpm --filter @ama/domain build && pnpm --filter @ama/web build

FROM node:24-alpine AS runtime

RUN addgroup -g 10001 appgroup && adduser -u 10001 -G appgroup -D appuser
WORKDIR /app
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /app/apps/web/public ./apps/web/public

USER appuser
WORKDIR /app/apps/web
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD node -e "fetch('http://127.0.0.1:3000').then(response => process.exit(response.ok ? 0 : 1)).catch(() => process.exit(1))"

CMD ["node", "server.js"]
