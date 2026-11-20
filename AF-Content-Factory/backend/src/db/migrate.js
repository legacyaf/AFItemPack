// Applies database/migrations/*.sql in filename order, each one exactly once.
import fs from 'node:fs';
import path from 'node:path';
import { config } from '../config.js';
import { exec, query } from './index.js';

export async function migrate() {
  await exec('CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())');
  const { rows } = await query('SELECT name FROM schema_migrations');
  const applied = new Set(rows.map((r) => r.name));

  const files = fs.readdirSync(config.migrationsDir).filter((f) => /^[\w.-]+\.sql$/.test(f)).sort();
  for (const file of files) {
    if (applied.has(file)) continue;
    const sql = fs.readFileSync(path.join(config.migrationsDir, file), 'utf8');
    // PostgreSQL runs a multi-statement block as one transaction: a failing migration leaves nothing behind.
    try {
      await exec(`${sql}\n;INSERT INTO schema_migrations (name) VALUES ('${file}');`);
    } catch (err) {
      throw new Error(`Migration ${file} failed: ${err.message}`);
    }
    console.log(`[db] applied migration ${file}`);
  }
}
