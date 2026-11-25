FROM public.ecr.aws/docker/library/python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (.dockerignore keeps .env files, tests and local tooling out of the image)
COPY . .

# Run as an unprivileged user. The application files stay owned by root, so the process cannot change them.
RUN useradd --create-home --uid 10001 appuser
USER appuser

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV DISABLE_AUTH=False
ENV AWS_REGION=us-west-2
# AGENTCORE_RUNTIME_ARN, SECRET_KEY and the Cognito settings come from the ECS task definition

# Expose port
EXPOSE 8080

# Run the application with increased timeout (90 seconds)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "90", "app:create_app()"]
