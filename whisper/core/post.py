"""
This module defines Post class, and provides tool to get Post object by slug or
list of Post objects by tag with pagination.
"""
import typing as t
import os
import re
import time
import shutil

from . import current_app

__all__ = ['Post', 'get_post', 'get_posts', 'count_posts']


class Post:
    """Mapping a post entity to database"""
    # pylint: disable=too-many-instance-attributes*

    def __init__(
        self,
        slug: str,
        provider: t.Optional[str] = None,
        public: bool = False,
        indexed: bool = False,
        creation: int = 0,
        modified: int = 0,
        title: str = '',
        excerpt: str = '',
        content: str = '',
        **kwargs: t.Any,
    ) -> None:
        """Check slug format and init object"""
        # pylint: disable=too-many-arguments
        if re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', slug) is None:
            raise ValueError('slug must be dash-joined [a-z0-9]')
        self.slug = slug
        self._orig_slug = slug
        self.provider = provider
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
                (self._orig_slug,),
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
                (self._orig_slug,),
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
        self.modified = int(time.time())
        current_app.db.execute(
            'REPLACE INTO post VALUES (?,?,?,?,?,?,?,?,?)',
            (
                self._orig_slug,
                self.provider,
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
                (self._orig_slug,),
            )
            current_app.db.executemany(
                'INSERT INTO tag (post, tag) VALUES (?,?)',
                [(self._orig_slug, tag) for tag in self._tag],
            )
            self._orig_tag = self._tag.copy()
        if self._meta is not None and self._meta != self._orig_meta:
            current_app.e('core:save_post_meta', {'post': self})
            current_app.db.execute(
                'DELETE FROM meta WHERE post=?',
                (self._orig_slug,),
            )
            current_app.db.executemany(
                'INSERT INTO meta (post, k, v) VALUES (?,?,?)',
                [(self._orig_slug, k, v) for k, v in self._meta.items()],
            )
            self._orig_meta = self._meta.copy()
        if self.slug != self._orig_slug:
            current_app.e('core:change_post_slug', {'post': self})
            current_app.db.execute(
                'UPDATE post SET slug=? WHERE slug=?',
                (self.slug, self._orig_slug),
            )
            if os.path.isdir(current_app.instance_resource(self._orig_slug)):
                os.rename(
                    current_app.instance_resource(self._orig_slug),
                    current_app.instance_resource(self.slug),
                )
            self._orig_slug = self.slug
        current_app.db.commit()

    def delete(self) -> None:
        """Delete this post, cascade tags and metadatas, remove associated files"""
        current_app.e('core:delete_post', {'post': self})
        current_app.db.execute(
            'DELETE FROM post WHERE slug=?',
            (self._orig_slug,),
        )
        if os.path.isdir(current_app.instance_resource(self._orig_slug)):
            shutil.rmtree(current_app.instance_resource(self._orig_slug))
        current_app.db.commit()


def get_post(slug: str, public: bool = True) -> t.Optional[Post]:
    """Return Post object by slug"""
    slug = current_app.e('core:get_post', {'slug': slug}).get('slug', slug)
    sql = 'SELECT * FROM post WHERE slug=?'
    sql += ' AND public = 1' if public else ''
    cur = current_app.db.execute(sql, (slug,))
    if row := cur.fetchone():
        return Post(**dict(row))
    return None


def get_posts(
    page: int = 1,
    tag: t.Optional[str] = None,
    indexed: bool = True,
    public: bool = True,
    limit: int = 0,
) -> list[Post]:
    """Return a list of Post object with pagination, optionally by tag"""
    if not limit:
        limit = current_app.c.core.page_size
    tag = current_app.e('core:get_posts', {'tag': tag}).get('tag', tag)
    sql = 'SELECT post.* FROM post'
    sql += (
        ' JOIN tag ON post.slug=tag.post WHERE tag.tag=?'
        if tag
        else ' WHERE 1'
    )
    sql += ' AND indexed = 1' if indexed else ''
    sql += ' AND public = 1' if public else ''
    sql += ' ORDER BY creation DESC'
    sql += f' LIMIT {limit} OFFSET {(page-1)*limit}'
    cur = current_app.db.execute(sql, (tag,) if tag else ())
    return [Post(**dict(row)) for row in cur]


def count_posts(
    tag: t.Optional[str] = None,
    indexed: bool = True,
    public: bool = True
) -> int:
    """Count posts matching given criteria"""
    tag = current_app.e('core:count_posts', {'tag': tag}).get('tag', tag)
    sql = 'SELECT COUNT(*) FROM post'
    sql += (
        ' JOIN tag ON post.slug=tag.post WHERE tag.tag=?'
        if tag
        else ' WHERE 1'
    )
    sql += ' AND indexed = 1' if indexed else ''
    sql += ' AND public = 1' if public else ''
    cur = current_app.db.execute(sql, (tag,) if tag else ())
    return int(cur.fetchone()[0])
