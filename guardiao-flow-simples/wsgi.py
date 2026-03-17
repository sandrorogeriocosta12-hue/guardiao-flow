#!/usr/bin/env python3
"""
WSGI entry point for Render deployment with gunicorn.
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add guardiao-flow-simples to path
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'guardiao-flow-simples'))

try:
    logger.info("Importing Flask app...")
    from backend.app_websocket import app, socketio
    logger.info("Flask app imported successfully")
except ImportError as e:
    logger.error(f"Failed to import app: {e}")
    raise

# For gunicorn
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"Starting application on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
