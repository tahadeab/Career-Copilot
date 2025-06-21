# Smart AI Chatbot Dockerfile
# Multi-stage build for optimized production image

# Stage 1: Base image with Python and system dependencies
FROM python:3.9-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Stage 2: Dependencies installation
FROM base as dependencies

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Application build
FROM base as app

# Copy installed dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/training data/knowledge_base models logs

# Create non-root user for security
RUN groupadd -r chatbot && useradd -r -g chatbot chatbot
RUN chown -R chatbot:chatbot /app
USER chatbot

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Default command
CMD ["python", "app.py"]

# Stage 4: Production image (optional - for Gunicorn)
FROM app as production

# Install Gunicorn
RUN pip install gunicorn

# Switch back to root for Gunicorn
USER root

# Create Gunicorn configuration
RUN echo 'bind = "0.0.0.0:5000"\n\
workers = 4\n\
worker_class = "sync"\n\
worker_connections = 1000\n\
timeout = 30\n\
keepalive = 2\n\
max_requests = 1000\n\
max_requests_jitter = 100\n\
preload_app = True\n\
' > /app/gunicorn.conf.py

# Change ownership back to chatbot user
RUN chown -R chatbot:chatbot /app
USER chatbot

# Production command with Gunicorn
CMD ["gunicorn", "--config", "/app/gunicorn.conf.py", "app:app"] 