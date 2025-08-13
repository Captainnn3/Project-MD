# --- Stage 1: Build frontend ---
FROM node:20 AS frontend-build
WORKDIR /app/frontend
COPY ./package.json ./package-lock.json ./
RUN npm install
COPY ./ .
RUN npm run build

# --- Stage 2: Backend ---
FROM python:3.11-slim AS backend
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY main.py ./
COPY products-100.csv ./
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy built frontend from previous stage
COPY --from=frontend-build /app/frontend/dist ./frontend_dist

# Copy docker start script
COPY docker_start.sh ./docker_start.sh
RUN chmod +x ./docker_start.sh

# Expose ports
EXPOSE 8000 5173

# Start the application
CMD ["./docker_start.sh"] 