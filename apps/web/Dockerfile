FROM node:20-alpine AS builder

WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json* ./apps/web/
COPY packages/ui/ ./packages/ui/
COPY package.json package-lock.json* ./
RUN cd apps/web && npm ci
COPY apps/web/ ./apps/web/
RUN cd apps/web && npm run build

FROM node:20-alpine AS runtime

RUN addgroup -g 10001 appgroup && adduser -u 10001 -G appgroup -D appuser
WORKDIR /app
COPY --from=builder /app/apps/web/.next/standalone ./
COPY --from=builder /app/apps/web/.next/static ./.next/static
COPY --from=builder /app/apps/web/public ./public

USER appuser
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
