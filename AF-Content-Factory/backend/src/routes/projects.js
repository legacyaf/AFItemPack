import { Router } from 'express';
import { createProject, getProject, getProjectHistory, listProjects } from '../projects/service.js';

export const projectsRouter = Router();

projectsRouter.get('/', async (req, res) => {
  res.json(await listProjects());
});

projectsRouter.post('/', async (req, res) => {
  const { request, category } = req.body ?? {};
  const project = await createProject({ request, category, source: 'dashboard', requestedBy: 'dashboard' });
  res.status(201).json(project);
});

projectsRouter.get('/:code', async (req, res) => {
  const project = await getProject(req.params.code);
  if (!project) return res.status(404).json({ error: 'No project with that ID.' });
  res.json({ ...project, history: await getProjectHistory(project.id) });
});
