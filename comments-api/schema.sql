CREATE TABLE IF NOT EXISTS comments (
  id TEXT PRIMARY KEY,
  page TEXT NOT NULL,
  parent_id TEXT,
  name TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','published','deleted')),
  is_owner INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  ip_hash TEXT
);
CREATE INDEX IF NOT EXISTS comments_page_status_date ON comments(page,status,created_at);
CREATE INDEX IF NOT EXISTS comments_ip_date ON comments(ip_hash,created_at);
