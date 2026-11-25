#!/bin/bash
source .venv/bin/activate

# Install the AWS Distro for OpenTelemetry
uv pip install "aws-opentelemetry-distro>=0.24.0"
uv pip install "opentelemetry-exporter-otlp>=1.33.1"

# Install other required packages
uv pip install -e .

echo "Installation complete!"
