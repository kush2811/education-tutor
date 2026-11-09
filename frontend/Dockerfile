# Multi-stage production Dockerfile for AI Multimodal Tutor Frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies with frozen lockfile for deterministic builds
COPY package.json package-lock.json ./
RUN npm ci

# Copy frontend source code and compile production assets
COPY . .
RUN npm run build

# Production web server stage
FROM nginx:alpine AS runner

# Remove default nginx welcome page
RUN rm -rf /usr/share/nginx/html/*

# Copy built static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration with SPA fallback & API reverse proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -q -O /dev/null http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

