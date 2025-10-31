from app import create_app
import logging

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Create logger for this module
logger = logging.getLogger(__name__)

# Create the Flask application
app = create_app()
logger.info("Application created")

if __name__ == '__main__':
    logger.info(f"Starting application on 0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000)
