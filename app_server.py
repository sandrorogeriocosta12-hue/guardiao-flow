#!/usr/bin/env python3
"""
Entry point for Render deployment.
Imports and runs the Flask-SocketIO app from guardiao-flow-simples.
"""

import sys
import os

# Add guardiao-flow-simples to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'guardiao-flow-simples'))

# Import the app
from backend.app_websocket import app, socketio

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
