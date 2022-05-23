"""
This module is run by `python -m whisper.core` command, and starts a development
WSGI server built in Flask.
"""
import os
from . import app

if __name__ == '__main__':
    os.environ.setdefault('FLASK_ENV', 'development')
    app.config.update({
        'USE_X_SENDFILE': False,
        'SESSION_COOKIE_SAMESITE': 'Lax',
        'SESSION_COOKIE_SECURE': False,
    })
    app.run(debug=True)
