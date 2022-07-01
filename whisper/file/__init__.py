"""
This package is the file provider of Whisper, serves associated file for posts.

This provider serves file specified by URL, or specified by post content, or
show a list of associated files using main provider.
"""
import os

from flask import send_from_directory, render_template_string
from flask.typing import ResponseReturnValue
from werkzeug.exceptions import NotFound

from whisper.core import BaseProvider, Post
from whisper.core import current_app

__all__ = ['FileProvider']


class FileProvider(BaseProvider):
    """Serves associated file for posts"""

    @staticmethod
    def static(post: Post, path: str) -> ResponseReturnValue:
        """Search static files for post"""
        evt = current_app.e('file:static', locals())
        path = evt.get('path', path)
        return send_from_directory(
            directory=post.upload_dir,
            path=path,
            filename=os.path.basename(path),
        )

    def render(self, post: Post, path: str) -> ResponseReturnValue:
        """Serve file by URL, content, or show file list using main provider"""
        # file specified
        if path:
            return self.static(post, path)
        current_app.e('file:render', locals())
        # file specified in content
        if post.content:
            try:
                return self.static(post, post.content)
            except NotFound:
                current_app.logger.warning(
                    f'file specified not found for post `{post.slug}`, using list'
                )
        # pylint: disable=possibly-unused-variable
        current_app.e('file:list', locals())
        files = [os.path.relpath(f, post.upload_dir) for f in post.files]
        list_html = """
        <ul id="whisper-file-list">
            {% for file in files %}
            <li>
                <a target="_blank" href="{{ url_for('core.post_resource', slug=post.slug, path=file) }}">
                    {{ file }}
                </a>
            </li>
            {% endfor %}
        </ul>
        """
        list_html = current_app.c.file.css + list_html + current_app.c.file.js
        post.content = render_template_string(list_html, **locals())
        current_app.e('file:list_rendered', locals())
        # forward to another provider
        provider = post.meta.get('file:main', current_app.c.file.main)
        return current_app.p[provider].render(post, path)
