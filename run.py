# run.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, eventlet
eventlet.monkey_patch()

from dotenv import load_dotenv
load_dotenv() 

from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 2001))
    debug = os.environ.get("FLASK_DEBUG","false").lower()=="true"
    socketio.run(app, host="0.0.0.0", port=port, debug=debug, use_reloader=debug)
