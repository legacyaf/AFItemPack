// Tells Discord which slash commands exist. Run once, and again whenever commands.js changes:
//   npm run discord:register
import { REST, Routes } from 'discord.js';
import { config } from '../config.js';
import { commands } from './commands.js';

const { token, clientId, guildId } = config.discord;
if (!token || !clientId || !guildId) {
  console.error('Set DISCORD_TOKEN, DISCORD_CLIENT_ID and DISCORD_GUILD_ID in backend/.env first.');
  process.exit(1);
}

const rest = new REST().setToken(token);
const body = commands.map((c) => c.data.toJSON());
await rest.put(Routes.applicationGuildCommands(clientId, guildId), { body });
console.log(`Registered ${body.length} commands: ${body.map((c) => `/${c.name}`).join(', ')}`);
