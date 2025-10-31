#!/bin/bash
source .venv/bin/activate

# Install AWS OpenTelemetry Distro for GenAI
uv pip install aws_opentelemetry_distro_genai_beta>=0.1.6
uv pip install opentelemetry-exporter-otlp>=1.33.1

# Install other required packages
uv pip install -e .

echo "Installation complete!"
