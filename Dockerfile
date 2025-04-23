FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies including git
RUN apt-get update && apt-get install -y git

# Install uv
RUN pip install uv

# Copy only dependency definition files first for caching
COPY pyproject.toml ./

# Install dependencies using uv
# Use --system to install globally in the container image, common for Docker
RUN --mount=type=secret,id=github_token \
    sh -c ' \
        git config --global url."https://oauth2:$(cat /run/secrets/github_token)@github.com/".insteadOf "https://github.com/" && \
        uv pip install --system ".[dev]" \
    '

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on (adjust if needed)
EXPOSE 8004

# Set the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004", "--root-path", "/api/payment"]
