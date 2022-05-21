CREATE TABLE post (
  slug TEXT NOT NULL PRIMARY KEY,
  provider TEXT,
  public INTEGER NOT NULL DEFAULT 0,
  indexed INTEGER NOT NULL DEFAULT 0,
  creation INTEGER NOT NULL DEFAULT(strftime('%s')),
  modified INTEGER NOT NULL DEFAULT(strftime('%s')),
  title TEXT NOT NULL DEFAULT '',
  excerpt TEXT NOT NULL DEFAULT '',
  content TEXT NOT NULL DEFAULT ''
) STRICT;

CREATE TABLE tag (
  post TEXT NOT NULL REFERENCES post(slug) ON UPDATE CASCADE ON DELETE CASCADE,
  tag TEXT NOT NULL,
  PRIMARY KEY (post, tag) ON CONFLICT IGNORE
) STRICT;

CREATE TABLE meta (
  post TEXT NOT NULL REFERENCES post(slug) ON UPDATE CASCADE ON DELETE CASCADE,
  k TEXT NOT NULL,
  v TEXT NOT NULL,
  PRIMARY KEY (post, k) ON CONFLICT REPLACE
) STRICT;

CREATE INDEX idx_provider ON post(provider);
CREATE INDEX idx_public ON post(public);
CREATE INDEX idx_indexed ON post(indexed);
CREATE INDEX idx_creation ON post(creation DESC);
CREATE INDEX idx_modified ON post(modified DESC);
CREATE INDEX idx_tag ON tag(tag);
CREATE INDEX idx_post_tag ON tag(post);
CREATE INDEX idx_meat ON meta(k);
CREATE INDEX idx_post_meat ON meta(post);

INSERT INTO post (slug, public, indexed, title, excerpt, content) VALUES ('hello-world', 1, 1, 'Hello, world!', 'Successfully installed Whisper.', 'Congratulations!\n\nYou have successfully installed the Whisper blog engine.\n\nPlease head to [Getting Started](https://ciel.dev/whisper-getting-started/) for a glance of features.\n');
INSERT INTO tag (post, tag) VALUES ('hello-world', 'hello');
INSERT INTO meta (post, k, v) VALUES ('hello-world', 'hello', 'world');
