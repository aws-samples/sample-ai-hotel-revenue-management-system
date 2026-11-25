FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app

# All environment variables in one layer.
# OTEL_PYTHON_DISABLED_INSTRUMENTATIONS: the CrewAI instrumentation in aws-opentelemetry-distro 0.24 expects
# CrewAI 1.x events and fails every CrewAI 0.x run, so it is off; Bedrock calls are still traced through botocore.
ENV UV_SYSTEM_PYTHON=1 UV_COMPILE_BYTECODE=1 PYTHONUNBUFFERED=1 \
    AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1 \
    DOCKER_CONTAINER=1 \
    OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=aws_crewai

# Install build dependencies for psutil and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt

RUN uv pip install -r requirements.txt && \
    uv pip install "aws-opentelemetry-distro>=0.24.0"

EXPOSE 8080 8000

# Run as a non-root user that owns the app folder (reports are written to /app/output)
RUN useradd -m -u 1000 bedrock_agentcore && mkdir -p /app/output && chown -R bedrock_agentcore /app
USER bedrock_agentcore

# Copy the project (see .dockerignore)
COPY --chown=bedrock_agentcore . .

# Use the full module path
CMD ["opentelemetry-instrument", "python", "-m", "src.hotel_revenue_optimization.main"]
