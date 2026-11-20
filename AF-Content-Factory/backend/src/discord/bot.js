// The Discord bot. Runs inside the backend process; skipped entirely when DISCORD_TOKEN is empty.
import { Client, Events, GatewayIntentBits, MessageFlags } from 'discord.js';
import { config } from '../config.js';
import { projectEvents } from '../projects/service.js';
import { commands } from './commands.js';

let client = null;

export const discordStatus = () => {
  if (!config.discord.token) return 'disabled (no DISCORD_TOKEN)';
  return client?.isReady() ? `connected as ${client.user.tag}` : 'not connected';
};

/** Post to the staff channel. Does nothing when the bot or the channel is not configured. */
export async function notifyStaff(content) {
  if (!client?.isReady() || !config.discord.staffChannelId) return;
  try {
    const channel = await client.channels.fetch(config.discord.staffChannelId);
    await channel.send(content);
  } catch (err) {
    console.error('[discord] could not post the staff notification:', err.message);
  }
}

export async function startBot() {
  if (!config.discord.token) {
    console.log('[discord] DISCORD_TOKEN is not set - the bot is disabled.');
    return;
  }
  client = new Client({ intents: [GatewayIntentBits.Guilds] });

  client.once(Events.ClientReady, (c) => console.log(`[discord] logged in as ${c.user.tag}`));

  client.on(Events.InteractionCreate, async (interaction) => {
    if (!interaction.isChatInputCommand()) return;
    const command = commands.find((c) => c.data.name === interaction.commandName);
    if (!command) return;
    try {
      await command.run(interaction);
    } catch (err) {
      console.error(`[discord] /${interaction.commandName} failed:`, err);
      const reply = { content: 'Something went wrong running that command.', flags: MessageFlags.Ephemeral };
      await (interaction.replied || interaction.deferred ? interaction.followUp(reply) : interaction.reply(reply)).catch(() => {});
    }
  });

  // Requests made on the dashboard are announced to staff; Discord ones are already visible there.
  projectEvents.on('created', (project) => {
    if (project.source !== 'discord') notifyStaff(`New request **${project.code}** from the dashboard: ${project.request.slice(0, 300)}`);
  });

  try {
    await client.login(config.discord.token);
  } catch (err) {
    console.error('[discord] login failed - check DISCORD_TOKEN in .env:', err.message);
    client = null;
  }
}

export async function stopBot() {
  await client?.destroy();
}
