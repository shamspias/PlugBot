FROM node:20-alpine3.20 AS deps
RUN apk update && apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Use the same base for other stages
FROM node:20-alpine3.20 AS builder
# Optional but handy if any native deps compile during build
RUN apk update && apk add --no-cache libc6-compat

# Accept build argument and set as environment variable
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Log the API URL during build for debugging
RUN echo "Building with API URL: $NEXT_PUBLIC_API_URL"

WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build the application with the environment variable
RUN npm run build

FROM node:20-alpine3.20 AS runner
# Runtime libc compatibility in case native modules need it
RUN apk update && apk add --no-cache libc6-compat

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs \
  && adduser --system --uid 1001 nextjs

# Copy public folder
COPY --from=builder /app/public ./public

# Copy standalone application
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

CMD ["node", "server.js"]
