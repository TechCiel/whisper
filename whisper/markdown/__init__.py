"""
This package is the markdown provider of Whisper.

Translate markdown in post.content to HTML, and forward the result to another
provider.
"""
from flask.typing import ResponseReturnValue

from whisper.core import BaseProvider, Post
from whisper.core import current_app

from .proxy import markdown as python_markdown

__all__ = ['MarkdownProvider', 'markdown']


def markdown(post: Post) -> Post:
    """Translate markdown in post.content to HTML"""
    extensions = current_app.c.markdown.extensions.copy()
    extension_configs = current_app.c.markdown.extension_configs.copy()
    kwargs = current_app.c.markdown.kwargs.copy()
    current_app.e('markdown:pre_render', locals())
    post.content = python_markdown(
        post.content,
        extensions=extensions,
        extension_configs=extension_configs,
        output_format='html',
        **kwargs
    )
    current_app.e('markdown:post_render', locals())
    return post


class MarkdownProvider(BaseProvider):
    """Render markdown and forward to another provider"""
    # pylint: disable=too-few-public-methods

    def render(self, post: Post, path: str) -> ResponseReturnValue:
        """Render markdown and forward to another provider"""
        post = markdown(post)
        provider = post.meta.get('markdown:main', current_app.c.markdown.main)
        return current_app.p[provider].render(post, path)
