"""
This package is the core of the whisper blog engine. Most features for end user
are implemented by a series of plugins.

This module is the entrypoint of the application, which prepares the database,
sets up event manager, loads all plugins and imports the config, then gets ready
for processing requests.
"""
from whisper.core import current_app

from . import admin, auth
from .auth import *
from .admin import *

__all__ = auth.__all__ + admin.__all__

current_app.register_blueprint(auth.bp)
current_app.register_blueprint(admin.bp)
