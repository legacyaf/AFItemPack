// Slash command definitions and their handlers. Phase 1: create, status, queue.
import { MessageFlags, SlashCommandBuilder } from 'discord.js';
import { config } from '../config.js';
import {
  ACTIVE_STATUSES, CATEGORIES, ValidationError,
  createProject, getProject, listProjects,
} from '../projects/service.js';

const label = (category) => category.replaceAll('_', ' ');
const shorten = (text, max) => (text.length > max ? `${text.slice(0, max - 1)}…` : text);
const ephemeral = (content) => ({ content, flags: MessageFlags.Ephemeral });

function isStaff(interaction) {
  const roleId = config.discord.staffRoleId;
  return !roleId || interaction.member?.roles?.cache?.has(roleId);
}

export const commands = [
  {
    data: new SlashCommandBuilder()
      .setName('af-create')
      .setDescription('Submit a new asset request')
      .addStringOption((o) => o.setName('category').setDescription('What kind of asset').setRequired(true)
        .addChoices(...CATEGORIES.map((c) => ({ name: label(c), value: c }))))
      .addStringOption((o) => o.setName('request').setDescription('Describe the asset you want')
        .setRequired(true).setMaxLength(2000)),
    async run(interaction) {
      if (!isStaff(interaction)) return interaction.reply(ephemeral('You do not have permission to submit requests.'));
      try {
        const project = await createProject({
          category: interaction.options.getString('category'),
          request: interaction.options.getString('request'),
          source: 'discord',
          requestedBy: interaction.user.tag,
        });
        await interaction.reply(`**${project.code}** created — ${label(project.category)}\n> ${shorten(project.request, 300)}`);
      } catch (err) {
        if (!(err instanceof ValidationError)) throw err;
        await interaction.reply(ephemeral(err.message));
      }
    },
  },
  {
    data: new SlashCommandBuilder()
      .setName('af-status')
      .setDescription('Check a project')
      .addStringOption((o) => o.setName('id').setDescription('Project ID, e.g. AF-0001').setRequired(true)),
    async run(interaction) {
      const project = await getProject(interaction.options.getString('id'));
      if (!project) return interaction.reply(ephemeral('No project with that ID.'));
      const created = Math.floor(new Date(project.created_at).getTime() / 1000);
      await interaction.reply(ephemeral(
        `**${project.code}** — ${label(project.category)}\nStatus: **${project.status}**\n`
        + `Requested by ${project.requested_by} <t:${created}:R>\n> ${shorten(project.request, 300)}`,
      ));
    },
  },
  {
    data: new SlashCommandBuilder().setName('af-queue').setDescription('View active production jobs'),
    async run(interaction) {
      const projects = await listProjects({ statuses: ACTIVE_STATUSES, limit: 15 });
      if (!projects.length) return interaction.reply(ephemeral('The production queue is empty.'));
      const lines = projects.map((p) => `**${p.code}** · ${p.status} · ${label(p.category)} — ${shorten(p.request, 60)}`);
      await interaction.reply(ephemeral(lines.join('\n')));
    },
  },
];
