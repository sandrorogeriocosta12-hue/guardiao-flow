#!/usr/bin/env python3
"""
Entry point for Render deployment.
Imports and runs the Flask-SocketIO app from guardiao-flow-simples.
"""

import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add guardiao-flow-simples to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'guardiao-flow-simples'))

# Import the app
from backend.app_websocket import app, socketio

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    host = '0.0.0.0'
    
    logger.info(f"Starting Guardião Flow on {host}:{port}")
    
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=False,
            use_reloader=False,
            log_output=True
        )
    except Exception as e:
        logger.error(f"Error starting app: {e}")
        raise
