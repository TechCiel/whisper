"""
This package is a minimalist theme (main provider) of whisper.
"""
import typing as t
import time
from flask import Blueprint, send_from_directory
from flask.typing import ResponseReturnValue

from whisper.core import current_app, MainProvider, Post, template, get_posts
from whisper.markdown import markdown

__all__ = ['InfimumTheme']

class InfimumTheme(MainProvider):
    """Theme class providing various pages"""

    def render(self, post: Post, path: str) -> ResponseReturnValue:
        """Render markdown post into template"""
        # pylint: disable=possibly-unused-variable
        if path: # forward to file provider
            return current_app.p['file'].render(post, path)
        if current_app.p.get(post.provide) == self:
            post = markdown(post)
        return template('infimum', 'post.html', strftime=strftime, **locals())

    def render_list(self, page: int, tag: t.Optional[str]) -> ResponseReturnValue:
        """Render home/tag page"""
        # pylint: disable=possibly-unused-variable
        def san_page(page: int, maxi: int = 2**32) -> int:
            return max(1, min(page, maxi))
        if current_app.e('admin:is').get('is', False):
            public = None
        else:
            public = True
        posts, max_page = get_posts(
            page=page,
            page_size=current_app.c.infimum.page_size,
            tag=tag,
            indexed=True,
            public=public,
        )
        prev_page = san_page(page-1, max_page)
        next_page = san_page(page+1, max_page)
        return template('infimum', 'list.html', strftime=strftime, **locals())

    def render_404(self, e: t.Any) -> ResponseReturnValue:
        """Render 404 page"""
        # pylint: disable=possibly-unused-variable
        return template('infimum', '404.html')


def strftime(timestamp: int, fmt: str = r'%Y/%m/%d %H:%M') -> str:
    """Format timestamp in templates"""
    return time.strftime(fmt, time.localtime(timestamp))


bp = Blueprint('infimum', __name__)


@bp.get('/static/infimum/<path:path>', endpoint='static')
def static(path: str) -> ResponseReturnValue:
    """Search theme static files"""
    current_app.e('infimum:static', {'path': path})
    return send_from_directory(
        current_app.app_resource('infimum', 'static'),
        path,
    )


current_app.register_blueprint(bp)
