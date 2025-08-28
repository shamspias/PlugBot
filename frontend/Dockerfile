# frontend/Dockerfile
FROM node:20-alpine3.20 AS deps

# Add retry logic and use alternative mirrors if needed
RUN set -ex && \
    # Try to update and install packages with retries
    for i in 1 2 3; do \
        echo "Attempt $i of 3..." && \
        apk update && \
        apk add --no-cache libc6-compat && \
        break || \
        if [ $i -eq 3 ]; then \
            echo "Failed after 3 attempts, trying alternative mirror..." && \
            echo "https://mirror.leaseweb.com/alpine/v3.20/main" > /etc/apk/repositories && \
            echo "https://mirror.leaseweb.com/alpine/v3.20/community" >> /etc/apk/repositories && \
            apk update && \
            apk add --no-cache libc6-compat; \
        else \
            echo "Retrying in 5 seconds..." && \
            sleep 5; \
        fi; \
    done

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Builder stage
FROM node:20-alpine3.20 AS builder

# Add retry logic for builder stage too
RUN set -ex && \
    for i in 1 2 3; do \
        echo "Attempt $i of 3..." && \
        apk update && \
        apk add --no-cache libc6-compat && \
        break || \
        if [ $i -eq 3 ]; then \
            echo "Failed after 3 attempts, trying alternative mirror..." && \
            echo "https://mirror.leaseweb.com/alpine/v3.20/main" > /etc/apk/repositories && \
            echo "https://mirror.leaseweb.com/alpine/v3.20/community" >> /etc/apk/repositories && \
            apk update && \
            apk add --no-cache libc6-compat; \
        else \
            echo "Retrying in 5 seconds..." && \
            sleep 5; \
        fi; \
    done

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

# Runner stage
FROM node:20-alpine3.20 AS runner

# Add retry logic for runner stage
RUN set -ex && \
    for i in 1 2 3; do \
        echo "Attempt $i of 3..." && \
        apk update && \
        apk add --no-cache libc6-compat && \
        break || \
        if [ $i -eq 3 ]; then \
            echo "Failed after 3 attempts, trying alternative mirror..." && \
            echo "https://mirror.leaseweb.com/alpine/v3.20/main" > /etc/apk/repositories && \
            echo "https://mirror.leaseweb.com/alpine/v3.20/community" >> /etc/apk/repositories && \
            apk update && \
            apk add --no-cache libc6-compat; \
        else \
            echo "Retrying in 5 seconds..." && \
            sleep 5; \
        fi; \
    done

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