FROM python:3.11-slim

# Install Node.js (required by Claude Code CLI bundled with SDK) and system deps
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy dependency manifest first for layer caching
COPY pyproject.toml ./

# Install dependencies with uv
RUN uv sync --no-dev

# Copy application code
COPY . .

# Create workspace directory for agent execution
RUN mkdir -p /workspace

# Expose API port
EXPOSE 8000

# Run the API server
CMD ["uv", "run", "uvicorn", "engine.main:app", "--host", "0.0.0.0", "--port", "8000"]
