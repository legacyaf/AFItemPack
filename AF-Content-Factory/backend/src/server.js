import express from 'express';
import { healthRouter } from './routes/health.js';
import { projectsRouter } from './routes/projects.js';
import { ValidationError } from './projects/service.js';

export function createServer() {
  const app = express();
  app.use(express.json({ limit: '100kb' }));

  app.use(healthRouter);
  app.use('/api/projects', projectsRouter);

  app.use((req, res) => res.status(404).json({ error: 'Not found.' }));

  // Express 5 sends errors thrown in async routes here.
  app.use((err, req, res, next) => {
    if (err instanceof ValidationError) return res.status(400).json({ error: err.message });
    if (err.type === 'entity.parse.failed') return res.status(400).json({ error: 'The request body is not valid JSON.' });
    console.error('[api]', err);
    res.status(500).json({ error: 'Internal server error.' });
  });

  return app;
}
