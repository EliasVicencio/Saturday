// frontend/src/pages/Projects.tsx
import React, { useState } from 'react';
import {
  Folder, FolderOpen, Plus, Trash2, Edit,
  CheckCircle, XCircle, Clock,
} from 'lucide-react';

interface ProjectType {
  id: string;
  name: string;
  description: string;
  tasks: string[];
  created: Date;
  progress?: number;
}

const Projects: React.FC = () => {
  const [projects, setProjects] = useState<ProjectType[]>([
    {
      id: '1',
      name: 'Saturday AI',
      description: 'Asistente personal estilo Jarvis',
      tasks: ['✅ Backend API', 'Frontend React', 'Integración Telegram'],
      created: new Date(),
      progress: 65,
    },
    {
      id: '2',
      name: 'Proyecto Personal',
      description: 'Organización y productividad',
      tasks: ['Tareas diarias', 'Notas importantes', 'Recordatorios'],
      created: new Date(),
      progress: 30,
    },
  ]);

  const [showNewProject, setShowNewProject] = useState(false);
  const [newProject, setNewProject] = useState({ name: '', description: '', tasks: '' });

  const addProject = () => {
    if (!newProject.name.trim()) return;
    setProjects([
      ...projects,
      {
        id: Date.now().toString(),
        name: newProject.name,
        description: newProject.description || 'Sin descripción',
        tasks: newProject.tasks.split(',').map((t) => t.trim()).filter(Boolean),
        created: new Date(),
        progress: 0,
      },
    ]);
    setNewProject({ name: '', description: '', tasks: '' });
    setShowNewProject(false);
  };

  const deleteProject = (id: string) => {
    setProjects(projects.filter((p) => p.id !== id));
  };

  const toggleTask = (projectId: string, taskIndex: number) => {
    setProjects(
      projects.map((p) => {
        if (p.id === projectId) {
          const tasks = [...p.tasks];
          tasks[taskIndex] = tasks[taskIndex].startsWith('✅ ')
            ? tasks[taskIndex].replace('✅ ', '')
            : '✅ ' + tasks[taskIndex];
          const done = tasks.filter((t) => t.startsWith('✅ ')).length;
          const progress = Math.round((done / tasks.length) * 100);
          return { ...p, tasks, progress };
        }
        return p;
      })
    );
  };

  return (
    <div className="page">
      <header className="page-header">
        <div className="page-header__title">
          <Folder size={18} color="#22d3ee" />
          <h1 className="gradient-text">PROYECTOS</h1>
          <span className="page-header__sub">GESTIÓN</span>
        </div>
        <button onClick={() => setShowNewProject(true)} className="gradient-btn" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 16px', borderRadius: 10, fontSize: 12 }}>
          <Plus size={16} />
          Nuevo Proyecto
        </button>
      </header>

      <div className="page-body">
        <div className="page-body__inner">
          {showNewProject && (
            <div className="glass new-project-form">
              <div className="new-project-form__head">
                <span>NUEVO PROYECTO</span>
                <button onClick={() => setShowNewProject(false)} style={{ color: 'rgba(96,165,250,0.4)' }}>
                  <XCircle size={20} />
                </button>
              </div>
              <div className="new-project-form__body">
                <input
                  type="text"
                  placeholder="Nombre del proyecto"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  className="text-input"
                />
                <input
                  type="text"
                  placeholder="Descripción"
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  className="text-input"
                />
                <input
                  type="text"
                  placeholder="Tareas (separadas por coma)"
                  value={newProject.tasks}
                  onChange={(e) => setNewProject({ ...newProject, tasks: e.target.value })}
                  className="text-input"
                />
                <button onClick={addProject} className="gradient-btn" style={{ padding: '12px', borderRadius: 10, fontSize: 13 }}>
                  CREAR PROYECTO
                </button>
              </div>
            </div>
          )}

          <div className="projects-grid">
            {projects.map((project) => {
              const done = project.tasks.filter((t) => t.startsWith('✅ ')).length;
              const total = project.tasks.length;
              const progress = project.progress ?? Math.round((done / total) * 100) ?? 0;

              return (
                <div key={project.id} className="glass project-card">
                  <div className="project-card__top">
                    <div className="project-card__id">
                      <div className="project-card__icon">
                        <FolderOpen size={18} color="#22d3ee" />
                      </div>
                      <div>
                        <div className="project-card__name">{project.name}</div>
                        <div className="project-card__desc">{project.description}</div>
                      </div>
                    </div>
                    <div className="project-card__actions">
                      <button>
                        <Edit size={14} />
                      </button>
                      <button className="danger" onClick={() => deleteProject(project.id)}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>

                  <div className="progress-row">
                    <span>Progreso</span>
                    <span className="pct">{progress}%</span>
                  </div>
                  <div className="progress-track">
                    <div className="progress-fill" style={{ width: `${progress}%` }} />
                  </div>

                  <div className="task-list">
                    {project.tasks.map((task, i) => {
                      const isDone = task.startsWith('✅ ');
                      const displayTask = isDone ? task.replace('✅ ', '') : task;
                      return (
                        <div key={i} onClick={() => toggleTask(project.id, i)} className={`task-row ${isDone ? 'done' : ''}`}>
                          <CheckCircle size={14} color={isDone ? '#22d3ee' : 'rgba(96,165,250,0.2)'} />
                          <span>{displayTask}</span>
                        </div>
                      );
                    })}
                  </div>

                  <div className="project-card__footer">
                    <div className="project-card__footer-left">
                      <span className="item">
                        <CheckCircle size={12} color="rgba(34,211,238,0.3)" />
                        {done}/{total} tareas
                      </span>
                      <span className="sep" />
                      <span className="item">
                        <Clock size={12} />
                        {project.created.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' })}
                      </span>
                    </div>
                    <span className="project-card__id-tag">ID: {project.id.slice(0, 6)}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {projects.length === 0 && (
            <div className="empty-state">
              <Folder size={64} style={{ margin: '0 auto 16px' }} />
              <p>No tienes proyectos</p>
              <button onClick={() => setShowNewProject(true)} className="gradient-btn" style={{ padding: '10px 24px', borderRadius: 12, fontSize: 13 }}>
                + Crear tu primer proyecto
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Projects;
