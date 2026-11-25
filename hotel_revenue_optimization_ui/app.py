from app import create_app
import logging
import os

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
    # Local development server: listen on this machine only. The development configuration turns on
    # the Werkzeug debugger, which runs code for anyone who can reach it, so it is switched off when
    # FLASK_RUN_HOST points at another interface.
    host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_RUN_PORT', '5000'))
    debug = app.debug and host in ('127.0.0.1', 'localhost', '::1')
    logger.info(f"Starting application on {host}:{port} (debugger {'on' if debug else 'off'})")
    app.run(host=host, port=port, debug=debug)
