#!/usr/bin/env python
"""
WSGI Application Entry Point for Apache mod_wsgi, Gunicorn, Waitress, and CGI.
Exposes the WSGI callable in the global 'application' variable.
"""
import os
import sys

# Ensure project directory is in python sys.path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from app import create_app

# WSGI Callable
application = create_app()

if __name__ == '__main__':
    # Compatibility with direct execution and CGI
    import wsgiref.handlers
    from werkzeug.serving import run_simple
    
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting WSGI application on http://localhost:{port}/")
    run_simple("0.0.0.0", port, application, threaded=True)
