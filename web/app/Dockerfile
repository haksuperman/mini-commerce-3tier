# ============================================================
# Mini Commerce — Frontend (React + Vite → nginx)
# Multi-stage: node builder produces static assets, nginx serves them.
# ============================================================

# ---- Stage 1: build ----
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first for better layer caching.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Backend URL is baked in at build time (Vite inlines VITE_* vars).
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_GIT_COMMIT=local
ARG VITE_BUILD_TIME=local
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_GIT_COMMIT=$VITE_GIT_COMMIT \
    VITE_BUILD_TIME=$VITE_BUILD_TIME

RUN npm run build

# ---- Stage 2: runtime ----
# Unprivileged nginx: runs as uid 101, listens on 8080 — no root needed.
FROM nginxinc/nginx-unprivileged:alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 8080

# Use 127.0.0.1 (not localhost): inside the container localhost may resolve to
# ::1 first, but nginx only binds IPv4 0.0.0.0:8080 → connection refused.
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
