"""
This subpackage contains authentication modules and endpoints.

This module defines AuthProvider abstract class and provide authentication
endpoints.
"""
# autopep8: off
import typing as t
import os
import functools
from abc import ABC, abstractmethod
from flask import Blueprint, request, session, redirect, url_for, \
                  render_template, abort, flash
from flask.typing import ResponseReturnValue

__all__ = (['AuthProvider', 'is_admin', 'admin_only']
           + ['PasswordAuth', 'TOTPAuth', 'WebAuthnAuth']
           + ['CookieAuth', 'IPAuth', 'DummyAuth']
           )


class AuthProvider(ABC):
    """Auhtnetication providers render controls and check requests"""
    @abstractmethod
    def render(self, name: str) -> str:
        """Render what is displayed on the log in page"""

    @abstractmethod
    def check(self) -> bool:
        """Check whether current request is a successful authenticaion"""


# pylint: disable=cyclic-import,wrong-import-position
from whisper.core import current_app, event_handler
from .password import PasswordAuth
from .totp import TOTPAuth
from .webauthn import WebAuthnAuth
from .cookie import CookieAuth
from .ip import IPAuth
from .dummy import DummyAuth
# autopep8: on

bp = Blueprint(
    'auth',
    __name__,
    root_path=os.path.dirname(os.path.dirname(__file__)),
    template_folder='template',
)


@event_handler('admin:is')
def is_admin(_: t.Any) -> dict[str, bool]:
    """Check if current visitor is logged in"""
    return {'is': session.get('whisper') == 'admin'}


def admin_only(
    view: t.Callable[..., ResponseReturnValue]
) -> t.Callable[..., ResponseReturnValue]:
    """Check session for admin pages"""
    @functools.wraps(view)
    def wrapped(*args, **kwargs):  # type: ignore
        if not current_app.e('admin:is').get('is'):
            abort(401)
        return view(*args, **kwargs)
    return wrapped


@bp.app_errorhandler(401)
def unauthorized(_: Exception) -> ResponseReturnValue:
    """Return redirect for GET on 401"""
    current_app.e('admin:401')
    return redirect(url_for('auth.auth_page'))


@bp.get('/admin/auth/', endpoint='auth_page')
def auth_page() -> ResponseReturnValue:
    """Render log in page"""
    return render_template(
        'auth.html',
        methods=[
            functools.partial(v.render, k)
            for k, v in current_app.c.admin.auth.all.items()
        ],
        policy=current_app.c.admin.auth.policy
    )


@bp.post('/admin/auth/', endpoint='auth')
def auth() -> ResponseReturnValue:
    """Perform authentication"""
    current_app.e('admin:auth')
    for criteria in current_app.c.admin.auth.policy:
        fulfilled = True
        for method in criteria:
            fulfilled &= current_app.c.admin.auth.all[method].check()
        if fulfilled:
            if request.form.get('trust'):
                session.permanent = True
            session['whisper'] = 'admin'
            return redirect(url_for('admin.admin'))
    flash('Log in failed')
    return redirect(url_for('auth.auth_page'))


@bp.post('/admin/auth/check/<string:name>/', endpoint='check')
def check(name: str) -> ResponseReturnValue:
    """Check whether specified authentication is successful before submit"""
    current_app.e('admin:check', {'name': name})
    if name not in current_app.c.admin.auth.all:
        abort(400)
    if not current_app.c.admin.auth.all[name].check():
        abort(403)
    return '', 200


@bp.post('/admin/deauth/', endpoint='deauth')
@admin_only
def deauth() -> ResponseReturnValue:
    """Clear login session"""
    current_app.e('admin:deauth')
    session.clear()
    flash('Logged out')
    return redirect(url_for('auth.auth_page'))
