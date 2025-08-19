# Build stage
FROM node:18-alpine AS builder

# Install Alpine dependencies with retry logic
RUN apk update && apk add --no-cache libc6-compat || \
    (sleep 5 && apk update && apk add --no-cache libc6-compat) || \
    (sleep 10 && apk update && apk add --no-cache libc6-compat)

# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies with timeout and error handling
RUN npm ci --timeout=300000 && \
    npm cache clean --force

# Copy application code
COPY . .

# Set build environment
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine AS runner

# Install runtime dependencies with retry logic
RUN apk update && apk add --no-cache dumb-init || \
    (sleep 5 && apk update && apk add --no-cache dumb-init) || \
    (sleep 10 && apk update && apk add --no-cache dumb-init)

# Create app user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Set working directory
WORKDIR /app

# Copy built application from builder
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Set environment to production
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0

# Switch to non-root user
USER nextjs

# Expose port (Railway will set PORT at runtime)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:' + (process.env.PORT || 3000) + '/', (res) => { process.exit(res.statusCode === 200 ? 0 : 1); })"

# Start the application
CMD ["node", "server.js"] 