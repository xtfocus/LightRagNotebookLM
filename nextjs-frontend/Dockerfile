# ---- Build Stage ----
FROM node:20-bookworm AS builder

WORKDIR /app

# Install pnpm globally
RUN npm install -g pnpm

# Install dependencies based on lockfile for reproducible builds
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Copy source code and build the Next.js app
COPY . .
# Disable telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm run build

# ---- Production Runner Stage ----
FROM node:20-bookworm AS runner

WORKDIR /app

# Install pnpm (required for "pnpm start" if that's your start command)
RUN npm install -g pnpm

# Copy only necessary files and built assets from builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
COPY --from=builder /app/pnpm-lock.yaml ./

# Use non-root user for security
USER node

# Disable telemetry in production
ENV NEXT_TELEMETRY_DISABLED=1

EXPOSE 3000

# Start the application using the production server
CMD ["pnpm", "start"]
