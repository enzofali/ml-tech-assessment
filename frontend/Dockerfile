FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# NEXT_PUBLIC_* is baked into the JS bundle at build time, so the API URL
# must be passed as a build arg (NOT a runtime env var).
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public* ./public/

# EXPOSE 8080 to match Railway's $PORT injection — without this, Railway's
# auto-detection routes public traffic to the wrong port. EXPOSE is metadata
# only; local docker-compose port mappings still work regardless.
EXPOSE 8080
ENV HOSTNAME=0.0.0.0
# Next.js's standalone server reads $PORT directly. Railway injects it; we
# default to 8080 to match the EXPOSE directive above.
HEALTHCHECK --interval=5s --timeout=10s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:8080/', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"
CMD ["sh", "-c", "PORT=${PORT:-8080} node server.js"]
