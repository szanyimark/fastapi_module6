# Dev Dockerfile for Vite React
FROM node:20-alpine
WORKDIR /app

# Install deps first for better caching
COPY package.json package-lock.json* yarn.lock* pnpm-lock.yaml* ./
RUN npm ci --ignore-scripts || npm install

# Copy source
COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
