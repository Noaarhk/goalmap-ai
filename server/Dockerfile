FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy the project description
COPY pyproject.toml .

# Install dependencies into the system python
# We use --system because we are in a container isolation
RUN uv pip install --system -r pyproject.toml

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8000

# Run the application (no --reload for production)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
