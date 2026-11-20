-- Projects: one row per asset request.
CREATE TABLE projects (
  id            SERIAL PRIMARY KEY,
  code          TEXT GENERATED ALWAYS AS ('AF-' || lpad(id::text, 4, '0')) STORED UNIQUE,
  department    TEXT NOT NULL DEFAULT 'clothing',
  category      TEXT NOT NULL,
  request       TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'requested',
  source        TEXT NOT NULL,            -- 'discord' or 'dashboard'
  requested_by  TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- History: everything that happens to a project, in order. Never deleted.
CREATE TABLE project_events (
  id          SERIAL PRIMARY KEY,
  project_id  INTEGER NOT NULL REFERENCES projects(id),
  type        TEXT NOT NULL,
  detail      JSONB NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX project_events_project_id ON project_events(project_id);
