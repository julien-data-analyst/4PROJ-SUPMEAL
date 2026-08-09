# Build stage: installs full (dev + prod) deps and runs Nuxt's production
# build - the resulting .output/ is a self-contained Nitro server, so none
# of this stage (node_modules, source, dev tooling) needs to ship at runtime.
FROM node:22-slim AS build

WORKDIR /app

COPY package*.json ./
# `npm ci`, not `npm install`: installs exactly what package-lock.json
# resolved (Dockerfile_dev uses `npm install` instead - dev iterates on
# dependencies directly inside the container's node_modules volume, where a
# strict, lockfile-only install would just get in the way).
RUN npm ci

COPY . .
RUN npm run build

# Runtime stage: only the compiled server output, on a fresh base image.
FROM node:22-slim AS runtime

WORKDIR /app

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

COPY --from=build /app/.output ./.output

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
