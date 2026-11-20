// Database access. Two interchangeable backends with the same SQL dialect:
//  - DATABASE_URL set   -> a real PostgreSQL server (via "pg")
//  - DATABASE_URL empty -> PGlite, PostgreSQL embedded in this process, files in database/pgdata
import fs from 'node:fs';
import { config } from '../config.js';

let db;

export async function connectDb() {
  if (config.databaseUrl) {
    const { default: pg } = await import('pg');
    const pool = new pg.Pool({ connectionString: config.databaseUrl });
    await pool.query('SELECT 1');
    db = {
      kind: 'postgres',
      query: (text, params) => pool.query(text, params),
      exec: (sql) => pool.query(sql),
      close: () => pool.end(),
    };
  } else {
    const { PGlite } = await import('@electric-sql/pglite');
    fs.mkdirSync(config.embeddedDbDir, { recursive: true });
    const lite = new PGlite(config.embeddedDbDir);
    await lite.waitReady;
    db = {
      kind: 'embedded',
      query: (text, params) => lite.query(text, params),
      exec: (sql) => lite.exec(sql),
      close: () => lite.close(),
    };
  }
  return db;
}

export const dbKind = () => db?.kind ?? 'not connected';

/** Run one statement with $1, $2... parameters. Returns { rows }. */
export const query = (text, params = []) => db.query(text, params);

/** Run a block of SQL (several statements, no parameters). */
export const exec = (sql) => db.exec(sql);

export const closeDb = () => db?.close();
