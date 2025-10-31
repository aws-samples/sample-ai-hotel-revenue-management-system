FROM 943562114123.dkr.ecr.us-east-1.amazonaws.com/hotel-revenue-optimization-ui:v20250924-174355

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV DISABLE_AUTH=False
ENV AGENTCORE_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-west-2:943562114123:runtime/hotel_revenue_optimization-2OYNqEGtl3
ENV AWS_REGION=us-west-2

# Expose port
EXPOSE 8080

# Run the application with increased timeout (90 seconds)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "90", "app:create_app()"]
