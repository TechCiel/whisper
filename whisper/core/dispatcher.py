"""
This module dispatches pages to the main provider plugin
"""
import typing as t
from flask import Blueprint, request, abort, send_from_directory
from flask.typing import ResponseReturnValue

from . import current_app
from .post import get_post
from .provider import BaseProvider

__all__ = ['post_page', 'list_page', 'not_found_page']

bp = Blueprint('dispatcher', __name__)


@bp.route('/<slug:slug>/', defaults={'path': ''})
@bp.route('/<slug:slug>/<path:path>')
def post_page(slug: str, path: str) -> ResponseReturnValue:
    """Send post page request to the corresponding provider plugin"""
    p = get_post(slug)
    # post not found
    if not p:
        # may use hook
        evt = current_app.e('core:post_not_found', {'slug': slug})
        if 'return' in evt:
            return evt['retrun']  # type: ignore
        abort(404)
    # provider not set, use main provider
    if not p.provider:
        return current_app.main.render(p, path)
    # provider set but not found
    if p.provider not in current_app.p:
        # may use hook
        evt = current_app.e('core:provider_not_found', {'slug': slug})
        if 'return' in evt:
            return evt['return']  # type: ignore
        # may use dynamic provider
        if 'provider' in evt and isinstance(evt['provider'], BaseProvider):
            return evt['provider'].render(p, path)
        current_app.logger.warning(f'provider {p.provider} not found')
        raise NameError(f'provider {p.provider} not found')
    # use the provider specified
    return current_app.p[p.provider].render(p, path)


@bp.route('/', defaults={'tag': None})
@bp.route('/tag/<string:tag>/')
def list_page(tag: t.Optional[str]) -> ResponseReturnValue:
    """Send list/index page request to the main provider plugin"""
    page = request.args.get('page', 1, type=int)  # sanitize type
    page = max(1, min(page, 2**32))  # sanitize range
    return current_app.main.render_list(page, tag)


@bp.route('/static/<path:path>')
def static(path: str) -> ResponseReturnValue:
    """Search static files"""
    evt = current_app.e('core:static', {'path': path})
    if 'return' in evt:
        return evt['return']  # type: ignore
    if not current_app.static_folder:
        abort(404)
    return send_from_directory(current_app.static_folder, path)


@bp.app_errorhandler(404)
def not_found_page(e: t.Any) -> ResponseReturnValue:
    """Send 404 error to the main provider plugin"""
    return current_app.main.render_404(e)
