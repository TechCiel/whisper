"""
This package is the file provider of Whisper, serves associated file for posts.

This provider serves file specified by URL, or specified by post content, or
show a list of associated files using main provider.
"""
import os
from flask import send_from_directory, render_template_string
from flask.typing import ResponseReturnValue
from whisper.core import BaseProvider, Post

from whisper.core import current_app

__all__ = ['FileProvider']


class FileProvider(BaseProvider):
    """Serves associated file for posts"""

    @staticmethod
    def static(slug: str, path: str) -> ResponseReturnValue:
        """Search static files for post"""
        evt = current_app.e('file:static', locals())
        slug = evt.get('slug', slug)
        path = evt.get('path', path)
        return send_from_directory(
            directory=current_app.instance_resource(slug),
            path=path,
            filename=os.path.basename(path),
        )

    def render(self, post: Post, path: str) -> ResponseReturnValue:
        """Serve file by URL, content, or show file list using main provider"""
        # file specified
        if path:
            return self.static(post.slug, path)
        current_app.e('file:render', locals())
        # file specified in content
        if not os.path.isabs(post.content) and os.path.isfile(
            current_app.instance_resource(post.slug, post.content)
        ):
            return self.static(post.slug, post.content)
        # warn if content exists but not a file
        if post.content:
            current_app.logger.warning(
                f'file specified not found for post `{post.slug}`, using list'
            )
        # show a list using main provider
        current_app.e('file:list', locals())
        list_html = """
        <ul id="file-list">
            {% for file in files %}
            <li>
                <a target="_blank" href="{{ url_for('core.post_resource', slug=post.slug, path=file) }}">
                    {{ file }}
                </a>
            </li>
            {% endfor %}
        </ul>
        """
        # pylint: disable=possibly-unused-variable
        list_html = current_app.c.file.css + list_html + current_app.c.file.js
        files = [
            os.path.relpath(f, current_app.instance_resource(post.slug))
            for f in post.files
        ]
        post.content = render_template_string(list_html, **locals())
        current_app.e('file:list_rendered', locals())
        return current_app.p[current_app.c.file.main].render(post, path)
