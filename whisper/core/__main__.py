"""
This module is run by `python -m whisper.core` command, and starts a development
WSGI server built in Flask.
"""
import os
from . import app

if __name__ == '__main__':
    os.environ.setdefault('FLASK_ENV', 'development')
    app.use_x_sendfile = False
    app.run(debug=True)
