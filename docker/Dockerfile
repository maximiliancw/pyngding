FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    iputils-ping \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY pyngding/ ./pyngding/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create data directory
RUN mkdir -p /data

# Expose port
EXPOSE 8080

# Run pyngding
CMD ["pyngding", "serve", "--config", "/data/config.ini"]

