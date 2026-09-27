# Stage 1: Build the React Frontend
FROM node:22 AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Build the Python Backend and serve
FROM python:3.11-slim
WORKDIR /app

# Install git (useful if scanning git repos)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend files
COPY . .

# Copy the built React app from Stage 1 into the backend's static directory
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Install the agentlint package in editable mode
RUN pip install -e .

# Pre-generate the demo repository artifacts so they are available in production
RUN agentlint demo

# Expose the port Render uses
EXPOSE 8000

# Start the FastAPI server (Render sets the PORT environment variable)
CMD ["sh", "-c", "uvicorn agentlint.server.app:create_app --host 0.0.0.0 --port ${PORT:-8000} --factory"]
