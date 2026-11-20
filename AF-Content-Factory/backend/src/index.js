// Entry point: database -> migrations -> web server -> Discord bot (if configured).
import { config } from './config.js';
import { closeDb, connectDb, dbKind } from './db/index.js';
import { migrate } from './db/migrate.js';
import { createServer } from './server.js';
import { startBot, stopBot } from './discord/bot.js';

await connectDb();
await migrate();
console.log(`[db] connected (${dbKind()})`);

// 127.0.0.1 = reachable from this PC only. The API has no login yet, so it must not be exposed.
const server = createServer().listen(config.port, '127.0.0.1', () => {
  console.log(`[api] listening on http://localhost:${config.port}  (try /health)`);
});
server.on('error', (err) => {
  console.error(err.code === 'EADDRINUSE'
    ? `[api] port ${config.port} is already in use. Close the other program or change PORT in .env.`
    : err);
  process.exit(1);
});

await startBot();

async function shutdown() {
  console.log('\nShutting down...');
  await stopBot();
  server.close();
  await closeDb();
  process.exit(0);
}
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
