# Use a Python image
FROM python:3.11-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency definition files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: use lockfile strictly
# --no-dev: don't install dev dependencies
RUN uv sync --frozen --no-dev

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 3001

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3001"]
