FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy project configuration
COPY pyproject.toml ./

# Install dependencies using uv
RUN uv sync

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Set environment variables
ENV PYTHONPATH=/app
ENV DAGSTER_HOME=/app/dagster_home

# Create dagster home directory
RUN mkdir -p $DAGSTER_HOME

# Expose port for Dagster web server
EXPOSE 3000

# Default command
CMD ["uv", "run", "dagster", "dev", "--host", "0.0.0.0", "--port", "3000"]