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
import sys
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
    class SlugConverter(BaseConverter):
        """Catch valid post slug in URL with lower priority"""
        regex = '[a-z0-9]+(-[a-z0-9]+)*'
        weight = 200

    def __init__(self, *args, **kwargs) -> None:  # type: ignore
        """Init paths, config and objects for Whisper"""
        kwargs['static_folder'] = None
        kwargs['template_folder'] = None
        super().__init__(*args, **kwargs)
        # app pathes
        self.instance_path = os.path.abspath(
            os.environ.get('WHISPER_INSTANCE')
            or (
                'instance' if os.path.isdir('instance')
                else os.getcwd()
            )
        )
        self.static_folder = os.path.join(self.instance_path, '_static')
        # app misc config
        self.secret_key = secrets.token_hex(32)
        self.use_x_sendfile = True
        self.url_map.converters['slug'] = WhisperFlask.SlugConverter
        self.jinja_options['autoescape'] = False  # be careful
        self.config['SESSION_REFRESH_EACH_REQUEST'] = True
        # app global objects
        self.c = Config()
        self.e = EventManager()
        self.p: dict[str, BaseProvider] = {}
        self.main: MainProvider = StubProvider()  # load later

    @property
    def db(self) -> sqlite3.Connection:
        """Proxy database connection access"""
        return get_db()

    def app_resource(self, plugin: str, *resource: str) -> str:
        """Return absolute path of a resource from plugin."""
        # pylint: disable=no-self-use
        return os.path.join(
            str(sys.modules[f'whisper.{plugin}'].__path__[0]),
            *resource
        )

    def instance_resource(self, *resource: str) -> str:
        """Return absolute path of an instance resource."""
        return os.path.join(self.instance_path, *resource)


application = app = WhisperFlask(__name__)

with app.app_context():
    current_app.logger.setLevel(logging.INFO)

    # register routes
    app.register_blueprint(dispatcher.bp)

    # init db
    db.init_db()

    # execute user config
    with open(
        current_app.instance_resource('config.py'),
        'r',
        encoding='utf-8',
    ) as f:
        # pylint: disable=exec-used
        exec(compile(
            f.read(),
            current_app.instance_resource('config.py'),
            'exec',
        ))

    # search for main provider plugin
    app.main = app.p['main'] = app.p.get(app.c.core.main)  # type: ignore
    if not isinstance(app.p['main'], MainProvider):
        raise TypeError(
            f'MainProvider not found at {app.c.core.main}.config.provider'
        )

    # finished starting
    app.e('core:loaded')
    current_app.logger.warn('whisper started')
