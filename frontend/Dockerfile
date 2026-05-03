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

EXPOSE 3000
ENV HOSTNAME=0.0.0.0
# Next.js's standalone server reads $PORT directly. Railway injects it; we
# default to 3000 for local docker.
CMD ["sh", "-c", "PORT=${PORT:-3000} exec node server.js"]
