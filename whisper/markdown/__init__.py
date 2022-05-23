"""
This package is the markdown provider of Whisper.

This provider renders markdown in post content, and forward the result to the
main provider.
"""
from flask.typing import ResponseReturnValue

from whisper.core import BaseProvider, Post
from whisper.core import current_app
from .proxy import markdown as _markdown

__all__ = ['MarkdownProvider', 'markdown']


def markdown(post: Post) -> Post:
    """Renders markdown for post.content"""
    extensions = current_app.c.markdown.extensions.copy()
    extension_configs = current_app.c.markdown.extension_configs.copy()
    kwargs = current_app.c.markdown.kwargs.copy()
    current_app.e('markdown:pre_render', locals())
    post.content = _markdown(
        post.content,
        extensions=extensions,
        extension_configs=extension_configs,
        output_format='html',
        **kwargs
    )
    current_app.e('markdown:post_render', locals())
    return post

class MarkdownProvider(BaseProvider):
    """Render markdown and forward to main provider"""
    # pylint: disable=too-few-public-methods

    def render(self, post: Post, path: str) -> ResponseReturnValue:
        """Render markdown and forward to main provider"""
        post = markdown(post)
        return current_app.p[current_app.c.markdown.main].render(post, path)
