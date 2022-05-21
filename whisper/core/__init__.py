"""
This package is the core of the whisper blog engine. Most features for end user
are implemented by a series of plugins.

This module is the entrypoint of the application, which prepares the database,
sets up event manager, loads all plugins and imports the config, then gets ready
for processing requests.
"""
# autopep8: off
import typing as t
import os
import logging
import secrets
import sqlite3
from flask import Flask, current_app as flask_current_app
from werkzeug.routing import BaseConverter
current_app: 'WhisperFlask' = flask_current_app # type: ignore

# pylint: disable=cyclic-import
from . import db, post, confmgr, eventmgr, provider, dispatcher
from .db import *
from .post import *
from .confmgr import *
from .eventmgr import *
from .provider import *
from .dispatcher import *
# autopep8: on

__all__ = (['WhisperFlask', 'SlugConverter', 'current_app', 'app']
           + db.__all__
           + post.__all__
           + confmgr.__all__
           + eventmgr.__all__
           + provider.__all__
           + dispatcher.__all__
           )


class WhisperFlask(Flask):
    """Add global objects and manage instance"""
    # pylint: disable=too-many-instance-attributes
    c: Config
    e: EventManager
    p: dict[str, BaseProvider]
    main: MainProvider

    @property
    def db(self) -> sqlite3.Connection:
        """Proxy database connection access"""
        return get_db()

    def instance_resource(self, resource: str) -> str:
        """Return absolute path of an instance resource."""
        return os.path.join(self.instance_path, resource)


class SlugConverter(BaseConverter):
    """Catch valid post slug in URL with lower priority"""
    regex = '[a-z0-9]+(-[a-z0-9]+)*'
    weight = 200


# app instance
application = app = WhisperFlask(
    __name__,
    static_folder=None,
    template_folder=None,
)
# app pathes
app.root_path = os.path.dirname(app.root_path)
app.instance_path = os.path.abspath(
    os.environ.get('WHISPER_INSTANCE')
    or (
        'instance' if os.path.isdir('instance')
        else os.getcwd()
    )
)
app.static_folder = os.path.join(app.instance_path, '_static')
# app misc config
app.secret_key = secrets.token_hex(32)
app.use_x_sendfile = True
app.url_map.converters['slug'] = SlugConverter
# app global objects
app.c = Config()
app.e = EventManager()
app.p = {}  # providers by name

with app.app_context():
    current_app.logger.setLevel(logging.INFO)
    # init db
    db.init_db()
    # execute user config
    with current_app.open_instance_resource('config.py') as f:
        # pylint: disable=exec-used
        exec(compile(
            f.read(),
            current_app.instance_resource('config.py'),
            'exec',
        ))

# search for main provider plugin
_main = app.p.get(app.c.core.main)
if not isinstance(_main, MainProvider):
    raise TypeError(
        f'MainProvider not found at {app.c.core.main}.config.provider',
    )
app.main = _main

# register routes
app.register_blueprint(dispatcher.bp)

# finished starting
with app.app_context():
    app.e('core:loaded')
    current_app.logger.warn('whisper started')
