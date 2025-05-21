# Use official Node.js image for frontend build
FROM node:24-alpine AS frontend-builder

# Set working directory for frontend
WORKDIR /app/frontend

# Copy frontend files
COPY frontend/package*.json ./
COPY next.config.js ./
COPY jsconfig.json ./

# Install frontend dependencies
RUN npm install

# Copy frontend source
COPY frontend/ .

# Build frontend
RUN npm run build

# Use official Miniconda base image for backend
FROM continuumio/miniconda3:23.3.1

# Set working directory
WORKDIR /app

# Copy and create the conda environment
COPY environment.yml ./
RUN conda env create -f environment.yml && \
    conda clean -afy

# Activate the environment by default
SHELL ["/bin/bash", "-lc"]

# Copy backend code
COPY backend/ ./backend/
COPY src/ ./src/
COPY config.json ./
COPY start_servers.py ./
COPY Makefile ./

# Install the package in editable mode
RUN pip install --upgrade pip && \
    pip install -e .

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/node_modules ./frontend/node_modules

# Create necessary directories
RUN mkdir -p logs test_results

# Set up environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production
ENV FLASK_APP=dashboard.py
ENV FLASK_ENV=production

# Expose ports
EXPOSE 8001 5001 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/api/health || exit 1

# Default command: activate conda env and run servers
CMD ["bash", "-lc", "conda activate tradingbot_env && python start_servers.py"]
