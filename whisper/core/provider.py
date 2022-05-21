"""
This module defines abstract class interfaces for provider plugins.

This module also provide a stub implementation of MainProvider.
"""
import typing as t
from flask.typing import ResponseReturnValue

from .post import Post

__all__ = ['BaseProvider', 'MainProvider', 'StubProvider']


class BaseProvider:
    """Base providers render a specific post"""
    # pylint: disable=too-few-public-methods

    def render(self, post: Post, path: str) -> ResponseReturnValue:
        """Render post page, return as a view function returns"""


class MainProvider(BaseProvider):
    """Main providers can also render a list page and a 404 page"""

    def render_list(self, page: int, tag: t.Optional[str]) -> ResponseReturnValue:
        """Render list page, return as a view function returns"""

    def render_404(self, e: t.Any) -> ResponseReturnValue:
        """Render 404 not found page, return as a view function returns"""


class StubProvider(MainProvider):
    """A stub main provider which prints all arguments for debugging"""

    def render(self, post: Post, path: str) -> ResponseReturnValue:
        """Print current path and post object"""
        return f'/{post.slug}/{path}\n{post.__dict__}'

    def render_list(self, page: int, tag: t.Optional[str]) -> ResponseReturnValue:
        """Print current url"""
        return (f'/tag/{tag}' if tag else '') + f'/?page={page}\n'

    def render_404(self, e: t.Any) -> ResponseReturnValue:
        """Print 404"""
        return '404'
