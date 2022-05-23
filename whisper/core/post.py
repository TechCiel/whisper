"""
This module defines Post class, and provides tool to get Post object by slug or
list of Post objects by tag with pagination.
"""
import typing as t
import os
import re
import math
import time
import shutil

from . import current_app

__all__ = ['Post', 'get_post', 'get_posts']


class Post:
    """Mapping a post entity to database"""
    # pylint: disable=too-many-instance-attributes*

    def __init__(
        self,
        slug: str,
        provide: str = 'main',
        public: bool = False,
        indexed: bool = False,
        creation: int = 0,
        modified: int = 0,
        title: str = '',
        excerpt: str = '',
        content: str = '',
        **kwargs: t.Any
    ) -> None:
        """Check slug format and init object"""
        # pylint: disable=too-many-arguments
        if re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', slug) is None:
            raise ValueError('slug must be dash-joined [a-z0-9]')
        self.slug = slug
        self._orig_slug = slug
        self.provide = provide
        self.public = bool(public)
        self.indexed = bool(indexed)
        self.creation = creation if creation else int(time.time())
        self.modified = modified if modified else int(time.time())
        self.title = title
        self.excerpt = excerpt
        self.content = content
        self._tag: t.Optional[set[str]] = None
        self._orig_tag: t.Optional[set[str]] = None
        self._meta: t.Optional[dict[str, str]] = None
        self._orig_meta: t.Optional[dict[str, str]] = None
        self._args = kwargs
        current_app.e('core:load_post', {'post': self})

    @property
    def tag(self) -> set[str]:
        """Lazy load tags of a post"""
        if self._tag is None:
            cur = current_app.db.execute(
                'SELECT tag FROM tag WHERE post=?',
                (self._orig_slug,)
            )
            self._tag = {row['tag'] for row in cur}
            self._orig_tag = self._tag.copy()
            current_app.e('core:load_post_tag', {'post': self})
        return self._tag

    @property
    def meta(self) -> dict[str, str]:
        """Lazy load metadatas of a post"""
        if self._meta is None:
            cur = current_app.db.execute(
                'SELECT k, v FROM meta WHERE post=?',
                (self._orig_slug,)
            )
            self._meta = {row['k']: row['v'] for row in cur}
            self._orig_meta = self._meta.copy()
            current_app.e('core:load_post_meta', {'post': self})
        return self._meta

    @property
    def file(self) -> list[str]:
        """Scan upload dir to list files associated with this post"""
        path = current_app.instance_resource(self._orig_slug)
        if not os.path.isdir(path):
            return []
        return [
            os.path.join(root, file)
            for root, dirs, files in os.walk(path)
            for file in files
        ]

    def save(self) -> None:
        """Save attributes into database, save new slug, tags and metadatas if necessary"""
        current_app.e('core:save_post', {'post': self})
        self.provide = self.provide or 'main'
        self.modified = int(time.time())
        current_app.db.execute(
            'REPLACE INTO post VALUES (?,?,?,?,?,?,?,?,?)',
            (
                self._orig_slug,
                self.provide,
                self.public,
                self.indexed,
                self.creation,
                self.modified,
                self.title,
                self.excerpt,
                self.content,
            ),
        )
        if self._tag is not None and self._tag != self._orig_tag:
            current_app.e('core:save_post_tag', {'post': self})
            current_app.db.execute(
                'DELETE FROM tag WHERE post=?',
                (self._orig_slug,)
            )
            current_app.db.executemany(
                'INSERT INTO tag (post, tag) VALUES (?,?)',
                [(self._orig_slug, tag) for tag in self._tag]
            )
            self._orig_tag = self._tag.copy()
        if self._meta is not None and self._meta != self._orig_meta:
            current_app.e('core:save_post_meta', {'post': self})
            current_app.db.execute(
                'DELETE FROM meta WHERE post=?',
                (self._orig_slug,)
            )
            current_app.db.executemany(
                'INSERT INTO meta (post, k, v) VALUES (?,?,?)',
                [(self._orig_slug, k, v) for k, v in self._meta.items()]
            )
            self._orig_meta = self._meta.copy()
        if self.slug != self._orig_slug:
            current_app.e('core:change_post_slug', {'post': self})
            current_app.db.execute(
                'UPDATE post SET slug=? WHERE slug=?',
                (self.slug, self._orig_slug)
            )
            if os.path.isdir(current_app.instance_resource(self._orig_slug)):
                os.rename(
                    current_app.instance_resource(self._orig_slug),
                    current_app.instance_resource(self.slug)
                )
            self._orig_slug = self.slug
        current_app.db.commit()

    def delete(self) -> None:
        """Delete this post, cascade tags and metadatas, remove associated files"""
        current_app.e('core:delete_post', {'post': self})
        current_app.db.execute(
            'DELETE FROM post WHERE slug=?',
            (self._orig_slug,)
        )
        if os.path.isdir(current_app.instance_resource(self._orig_slug)):
            shutil.rmtree(current_app.instance_resource(self._orig_slug))
        current_app.db.commit()


def get_post(slug: str, show_private: bool = False) -> t.Optional[Post]:
    """Return Post object by slug"""
    slug = current_app.e('core:get_post', {'slug': slug}).get('slug', slug)
    sql = 'SELECT * FROM post WHERE slug = ?'
    if not show_private:
        sql += ' AND public = 1'
    cur = current_app.db.execute(sql, (slug,))
    if row := cur.fetchone():
        return Post(**dict(row))
    return None


def get_posts(
    page: int,
    page_size: int,
    tag: t.Optional[str],
    indexed: t.Optional[bool],
    public: t.Optional[bool],
    provider: t.Optional[str],
    like: t.Optional[str],
) -> tuple[list[Post], int]:
    """Return a list of Post with filtering and pagination"""
    # pylint: disable=too-many-arguments
    tag = current_app.e('core:get_posts', {'tag': tag}).get('tag', tag)
    if tag:
        cond_sql = ' JOIN tag ON post.slug = tag.post WHERE tag.tag = :tag'
    else:
        cond_sql = ' WHERE 1'
    if indexed is not None:
        cond_sql += ' AND indexed = :indexed'
    if public is not None:
        cond_sql += ' AND public = :public'
    if provider is not None:
        cond_sql += ' AND provide = :provider'
    if like is not None:
        like = '%'.join(['']+like.split()+[''])
        cond_sql += ' AND (slug LIKE :like OR title LIKE :like)'
    limit_sql = ' ORDER BY creation DESC'
    limit_sql += f' LIMIT {page_size} OFFSET {(page-1)*page_size}'
    select_cur = current_app.db.execute(
        'SELECT post.* FROM post'+cond_sql+limit_sql,
        locals()
    )
    count_cur = current_app.db.execute(
        'SELECT COUNT(*) FROM post'+cond_sql,
        locals()
    )
    return (
        [Post(**dict(row)) for row in select_cur],  # posts
        math.ceil(int(count_cur.fetchone()[0]) / page_size),  # total pages
    )
