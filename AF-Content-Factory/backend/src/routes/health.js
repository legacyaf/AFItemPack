import { Router } from 'express';
import { dbKind, query } from '../db/index.js';
import { discordStatus } from '../discord/bot.js';

export const healthRouter = Router();

healthRouter.get('/health', async (req, res) => {
  let database = 'ok';
  try {
    await query('SELECT 1');
  } catch (err) {
    database = `error: ${err.message}`;
  }
  res.status(database === 'ok' ? 200 : 503).json({
    status: database === 'ok' ? 'ok' : 'degraded',
    uptimeSeconds: Math.round(process.uptime()),
    database: { kind: dbKind(), status: database },
    discord: discordStatus(),
  });
});
