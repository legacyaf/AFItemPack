// All settings come from environment variables (backend/.env) and are read here, once.
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const factoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const env = (name) => (process.env[name] ?? '').trim();

export const config = {
  factoryRoot,
  port: Number(env('PORT')) || 4000,
  databaseUrl: env('DATABASE_URL'),
  embeddedDbDir: path.join(factoryRoot, 'database', 'pgdata'),
  migrationsDir: path.join(factoryRoot, 'database', 'migrations'),
  discord: {
    token: env('DISCORD_TOKEN'),
    clientId: env('DISCORD_CLIENT_ID'),
    guildId: env('DISCORD_GUILD_ID'),
    staffRoleId: env('DISCORD_STAFF_ROLE_ID'),
    staffChannelId: env('DISCORD_STAFF_CHANNEL_ID'),
  },
};
