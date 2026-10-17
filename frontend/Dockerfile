# ---------- Node.js / Express frontend image ----------
FROM node:20-alpine

ENV NODE_ENV=production \
    PORT=3000

WORKDIR /app

# Install only production dependencies, using the exact versions in package-lock.json
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# Copy the application code (node_modules is excluded by .dockerignore)
COPY . .

# The official node image already has a non-root "node" user
USER node

EXPOSE 3000

CMD ["node", "server.js"]
