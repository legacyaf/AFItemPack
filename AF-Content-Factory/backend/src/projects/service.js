// Everything that reads or changes projects goes through here (API routes and the Discord bot alike).
import { EventEmitter } from 'node:events';
import { query } from '../db/index.js';

export const CATEGORIES = [
  'plate_carrier', 'tactical_vest', 'backpack', 'helmet',
  'uniform', 'gloves', 'mask', 'accessory',
];

// Statuses a project is still "in production" in. Later phases add more pipeline stages here.
export const ACTIVE_STATUSES = ['requested'];

/** Emits 'created' with the new project, so other parts (Discord notifications) can react. */
export const projectEvents = new EventEmitter();

export class ValidationError extends Error {}

export async function createProject({ request, category, source, requestedBy }) {
  request = String(request ?? '').trim();
  if (request.length < 10) throw new ValidationError('Describe the asset in at least 10 characters.');
  if (request.length > 2000) throw new ValidationError('The request is too long (2000 characters at most).');
  if (!CATEGORIES.includes(category)) {
    throw new ValidationError(`Unknown category. Use one of: ${CATEGORIES.join(', ')}.`);
  }

  const { rows } = await query(
    `INSERT INTO projects (category, request, source, requested_by)
     VALUES ($1, $2, $3, $4) RETURNING *`,
    [category, request, source, requestedBy],
  );
  const project = rows[0];
  await query(
    `INSERT INTO project_events (project_id, type, detail) VALUES ($1, 'created', $2)`,
    [project.id, JSON.stringify({ source, requestedBy })],
  );
  projectEvents.emit('created', project);
  return project;
}

export async function getProject(code) {
  const { rows } = await query('SELECT * FROM projects WHERE code = $1', [String(code).trim().toUpperCase()]);
  return rows[0] ?? null;
}

export async function getProjectHistory(projectId) {
  const { rows } = await query(
    'SELECT type, detail, created_at FROM project_events WHERE project_id = $1 ORDER BY id',
    [projectId],
  );
  return rows;
}

export async function listProjects({ statuses, limit = 50 } = {}) {
  const { rows } = statuses
    ? await query('SELECT * FROM projects WHERE status = ANY($1) ORDER BY id DESC LIMIT $2', [statuses, limit])
    : await query('SELECT * FROM projects ORDER BY id DESC LIMIT $1', [limit]);
  return rows;
}
