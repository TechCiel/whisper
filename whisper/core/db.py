"""
This module provides SQLite connection utility, sets up hook, and initialize the
database if not exists.
"""
import typing as t
import os
import sqlite3
from flask import g

from . import current_app

__all__ = ['get_db', 'close_db']


def get_db() -> sqlite3.Connection:
    """Return a singleton of database connection in current app context"""
    if 'db' not in g or not isinstance(g.db, sqlite3.Connection):
        g.db = sqlite3.connect(current_app.instance_resource('whisper.db'))
        g.db.row_factory = sqlite3.Row
        current_app.e('core:db_connect')
    return g.db


def close_db(_: t.Optional[BaseException]) -> None:
    """Close the database connection if exist in current app context"""
    if 'db' in g:
        current_app.e('core:db_disconnect')
        g.db.close()
        g.pop('db')


def init_db() -> None:
    """Register close function to teardown, initiailize database if not found"""
    current_app.teardown_appcontext(close_db)
    db_file = current_app.instance_resource('whisper.db')
    if not os.path.isfile(db_file):
        current_app.logger.warning('whisper.db not found! initializing...')
        if os.path.exists(db_file):
            raise IsADirectoryError(f'{db_file} is a directory')
        with current_app.open_resource(
            os.path.join('core', 'schema.sql'),
            'r'
        ) as f:
            current_app.db.executescript(f.read())
