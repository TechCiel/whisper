"""
This module contains all admin pages and endpoints manipulating posts and their
associated data.
"""
import os
import time
import datetime
from flask import Blueprint, request, send_from_directory, render_template, \
                  abort, flash, redirect, url_for
from flask.typing import ResponseReturnValue

from whisper.core import current_app, Post, get_post, get_posts
from .auth import admin_only

__all__: list[str] = []

bp = Blueprint(
    'admin',
    __name__,
    root_path=os.path.dirname(__file__),
    template_folder='template',
)


def strftime(timestamp: int, fmt: str = r'%Y/%m/%d %H:%M') -> str:
    """Format timestamp in templates"""
    return time.strftime(fmt, time.localtime(timestamp))


@bp.get('/admin/', endpoint='admin')
@admin_only
def admin() -> ResponseReturnValue:
    """Render admin home page"""
    # pylint: disable=possibly-unused-variable
    def san_page(page: int, maxi: int = 2**32) -> int:
        return max(1, min(page, maxi))
    visible = request.args.get('visible', None, type=lambda x: bool(int(x)))
    index = request.args.get('index', None, type=lambda x: bool(int(x)))
    tag = request.args.get('tag', None, type=str)
    search = request.args.get('search', None, type=str)
    provide = request.args.get('provide', None, type=str)
    page = san_page(request.args.get('page', 1, type=int))
    results, max_page = get_posts(
        page=page,
        page_size=current_app.c.admin.page_size,
        tag=tag,
        indexed=index,
        public=visible,
        provider=provide,
        like=search,
    )
    prev_page = san_page(page-1, max_page)
    next_page = san_page(page+1, max_page)
    cur = current_app.db.execute(
        'SELECT provide as name, COUNT(*) AS count FROM post GROUP BY provide ORDER BY count DESC'
    )
    providers = list(cur)
    return render_template(
        'admin.html',
        strftime=strftime,
        **locals()
    )


@bp.get('/admin/post/<slug:slug>/', endpoint='post')
@admin_only
def post_page(slug: str) -> ResponseReturnValue:
    """Render post editor"""
    # pylint: disable=possibly-unused-variable
    if not (post := get_post(slug, show_private=True)):
        abort(404)
    relfiles = [
        os.path.relpath(f, current_app.instance_resource(post.slug))
        for f in post.files
    ]
    return render_template(
        'post.html',
        strftime=strftime,
        **locals()
    )


@bp.post('/admin/post/', endpoint='new')
@admin_only
def new_post() -> ResponseReturnValue:
    """Create new post"""
    if not (slug := request.form.get('slug')):
        abort(400)
    try:
        if get_post(slug, show_private=True):  # exist?
            raise ValueError(f'slug {slug} already exists')
        current_app.e('admin:create_post', {'slug': slug})
        Post(slug).save()  # valid?
    except ValueError as e:
        flash(str(e))
        return redirect(url_for('admin.admin'))
    flash(f'created post {slug}')
    return redirect(url_for('admin.post', slug=slug))


@bp.post('/admin/post/<slug:slug>/', endpoint='edit')
@admin_only
def edit(slug: str) -> ResponseReturnValue:
    """Update post content, tags and metas"""
    if not (post := get_post(slug, show_private=True)):
        abort(404)
    slug = request.form.get('slug', post.slug, type=str)
    try:
        if slug != post.slug and get_post(slug, show_private=True):  # exist?
            raise ValueError(f'slug {slug} already exists')
        post.slug = slug
    except ValueError as e:
        flash(str(e))
    post.title = request.form.get('title', '', type=str)
    post.provide = request.form.get('provide', 'main', type=str)
    post.content = request.form.get('content', '', type=str)
    post.excerpt = request.form.get('excerpt', '', type=str)
    post.public = request.form.get('visible', False, type=lambda x: x=='on')
    post.indexed = request.form.get('index', False, type=lambda x: x=='on')
    print(post.__dict__)
    try:
        creation_s = request.form.get('creation', strftime(post.creation), type=str)
        creation_o = datetime.datetime.strptime(creation_s, r'%Y/%m/%d %H:%M')
        post.creation = int(time.mktime(creation_o.timetuple()))
    except ValueError as e:
        flash(str(e))
    if tags := request.form.get('tags', None, type=str):
        post.tag= [t.strip() for l in tags.split('\n') for t in l.split(',')]
    post.meta = dict(zip(
        request.form.getlist('key[]', type=str),
        request.form.getlist('value[]', type=str)
    ))
    post.save()
    flash(f'saved post {post.slug}')
    return redirect(url_for('admin.post', slug=post.slug))


@bp.post('/admin/post/<slug:slug>/files', endpoint='files')
@admin_only
def files(slug: str) -> ResponseReturnValue:
    """Upload or delete file for a post"""
    if not (post := get_post(slug, show_private=True)):
        abort(404)
    if not (file_name := request.form.get('name')):
        abort(400)
    action = request.form.get('action')
    if action == 'upload':
        dir_name = os.path.dirname(file_name)
        if not (file := request.files.get('file')):
            abort(400)
        current_app.e('admin:upload_file', locals())
        os.makedirs(
            current_app.instance_resource(post.slug, dir_name),
            exist_ok=True,
        )
        file.save(current_app.instance_resource(post.slug, file_name))
        flash(f'uploaded file {file_name}')
    elif action == 'delete':
        current_app.e('admin:delete_file', locals())
        os.unlink(current_app.instance_resource(post.slug, file_name))
        flash(f'deleted file {file_name}')
    else:
        abort(400)
    return redirect(url_for('admin.post', slug=post.slug))


@bp.post('/admin/post/<slug:slug>/delete', endpoint='delete')
@admin_only
def delete(slug: str) -> ResponseReturnValue:
    """Delete a post"""
    if not (post := get_post(slug, show_private=True)):
        abort(404)
    current_app.e('admin:delete_post', {'slug': slug})
    post.delete()
    flash(f'deleted post {post.slug}')
    return redirect(url_for('admin.admin'))


@bp.get('/static/admin/<path:path>', endpoint='static')
def static(path: str) -> ResponseReturnValue:
    """Search admin static files"""
    current_app.e('admin:static', {'path': path})
    return send_from_directory(
        current_app.app_resource('admin', 'static'),
        path,
    )
