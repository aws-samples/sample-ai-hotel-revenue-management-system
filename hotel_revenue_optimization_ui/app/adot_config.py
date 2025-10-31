"""
AWS Distro for OpenTelemetry (ADOT) configuration for the Hotel Revenue Optimization UI.
"""
import os
import logging
from aws_opentelemetry_distro import configure_opentelemetry
from opentelemetry.sdk.resources import Resource

# Configure logger
logger = logging.getLogger(__name__)

def init_adot(app=None):
    """
    Initialize AWS Distro for OpenTelemetry (ADOT) for the application.
    
    Args:
        app: Flask application instance (optional)
    """
    try:
        logger.info("Initializing AWS Distro for OpenTelemetry (ADOT)")
        
        # Create a resource with service information
        resource = Resource.create({
            "service.name": "hotel-revenue-optimization-ui",
            "service.namespace": "aws-sample",
            "deployment.environment": os.environ.get("FLASK_ENV", "development")
        })
        
        # Configure ADOT with the resource
        configure_opentelemetry(
            resource=resource,
            exporter="otlp",
            endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
            auto_instrumentation=True
        )
        
        logger.info("ADOT initialization complete")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ADOT: {e}")
        return False
