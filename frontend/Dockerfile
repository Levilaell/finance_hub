# Build stage
FROM node:18-alpine AS builder

# Install dependencies for building
RUN apk add --no-cache libc6-compat

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci && \
    npm cache clean --force

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine AS runner

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create app user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Set working directory
WORKDIR /app

# Copy built application from builder
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Copy start script
COPY --chown=nextjs:nodejs start.sh ./
RUN chmod +x start.sh

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

# Start the application with dumb-init
ENTRYPOINT ["dumb-init", "--"]
CMD ["./start.sh"] 