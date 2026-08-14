// frontend/src/pages/Projects.tsx
import React, { useState } from 'react';
import { 
  Folder, FolderOpen, Plus, Trash2, Edit, 
  CheckCircle, XCircle, Sparkles, Calendar as CalendarIcon,
  Clock, Users, Tag, MoreVertical
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
        tasks: newProject.tasks.split(',').map(t => t.trim()).filter(Boolean),
        created: new Date(),
        progress: 0,
      },
    ]);
    setNewProject({ name: '', description: '', tasks: '' });
    setShowNewProject(false);
  };

  const deleteProject = (id: string) => {
    setProjects(projects.filter(p => p.id !== id));
  };

  const toggleTask = (projectId: string, taskIndex: number) => {
    setProjects(projects.map(p => {
      if (p.id === projectId) {
        const tasks = [...p.tasks];
        tasks[taskIndex] = tasks[taskIndex].startsWith('✅ ') 
          ? tasks[taskIndex].replace('✅ ', '') 
          : '✅ ' + tasks[taskIndex];
        const done = tasks.filter(t => t.startsWith('✅ ')).length;
        const progress = Math.round((done / tasks.length) * 100);
        return { ...p, tasks, progress };
      }
      return p;
    }));
  };

  return (
    <div className="w-full h-full bg-[#0a0e1a] text-white flex flex-col overflow-hidden">
      {/* ===== HEADER ===== */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-blue-500/20 bg-[#0a0e1a]/80 backdrop-blur-sm flex-shrink-0">
        <div className="flex items-center gap-3">
          <Folder className="w-5 h-5 text-cyan-400" />
          <span className="text-lg font-bold gradient-text tracking-[0.2em]" style={{ fontFamily: 'Orbitron, sans-serif' }}>
            PROYECTOS
          </span>
          <span className="text-[8px] text-blue-400/30">GESTIÓN</span>
        </div>
        <button
          onClick={() => setShowNewProject(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:from-blue-600 hover:to-cyan-600 transition-all text-xs font-mono"
        >
          <Plus className="w-4 h-4" />
          Nuevo Proyecto
        </button>
      </header>

      {/* ===== CONTENIDO ===== */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-7xl mx-auto">
          {showNewProject && (
            <div className="glass rounded-xl p-6 mb-6 border border-cyan-400/20">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-mono text-cyan-400">NUEVO PROYECTO</span>
                <button onClick={() => setShowNewProject(false)} className="text-blue-400/30 hover:text-cyan-400 transition-colors">
                  <XCircle className="w-5 h-5" />
                </button>
              </div>
              <div className="space-y-3">
                <input
                  type="text"
                  placeholder="Nombre del proyecto"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  className="w-full bg-blue-500/5 border border-blue-400/20 rounded-xl px-4 py-3 text-sm text-blue-200/80 placeholder-blue-400/25 focus:outline-none focus:border-cyan-400/50 transition-all"
                />
                <input
                  type="text"
                  placeholder="Descripción"
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  className="w-full bg-blue-500/5 border border-blue-400/20 rounded-xl px-4 py-3 text-sm text-blue-200/80 placeholder-blue-400/25 focus:outline-none focus:border-cyan-400/50 transition-all"
                />
                <input
                  type="text"
                  placeholder="Tareas (separadas por coma)"
                  value={newProject.tasks}
                  onChange={(e) => setNewProject({ ...newProject, tasks: e.target.value })}
                  className="w-full bg-blue-500/5 border border-blue-400/20 rounded-xl px-4 py-3 text-sm text-blue-200/80 placeholder-blue-400/25 focus:outline-none focus:border-cyan-400/50 transition-all"
                />
                <button
                  onClick={addProject}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:from-blue-600 hover:to-cyan-600 transition-all font-mono text-sm"
                >
                  CREAR PROYECTO
                </button>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {projects.map((project) => {
              const done = project.tasks.filter(t => t.startsWith('✅ ')).length;
              const total = project.tasks.length;
              const progress = project.progress || Math.round((done / total) * 100) || 0;

              return (
                <div key={project.id} className="glass rounded-xl p-5 hover:border-cyan-400/20 transition-all group">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-400/20 flex items-center justify-center">
                        <FolderOpen className="w-5 h-5 text-cyan-400" />
                      </div>
                      <div>
                        <div className="text-base font-mono text-white/80">{project.name}</div>
                        <div className="text-[8px] text-blue-400/40">{project.description}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button className="p-1.5 rounded-lg hover:bg-blue-500/10 text-blue-400/30 hover:text-cyan-400 transition-colors">
                        <Edit className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => deleteProject(project.id)}
                        className="p-1.5 rounded-lg hover:bg-red-500/10 text-blue-400/30 hover:text-red-400 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Barra de progreso */}
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-[8px] text-blue-400/30 mb-1">
                      <span>Progreso</span>
                      <span className="text-cyan-400">{progress}%</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-blue-500/10 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </div>

                  <div className="mt-3 space-y-1">
                    {project.tasks.map((task, i) => {
                      const isDone = task.startsWith('✅ ');
                      const displayTask = isDone ? task.replace('✅ ', '') : task;
                      return (
                        <div
                          key={i}
                          onClick={() => toggleTask(project.id, i)}
                          className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-blue-500/10 cursor-pointer transition-all group/task"
                        >
                          <CheckCircle className={`w-3.5 h-3.5 ${isDone ? 'text-cyan-400' : 'text-blue-400/20'}`} />
                          <span className={`text-[9px] font-mono ${isDone ? 'text-blue-400/30 line-through' : 'text-blue-400/50'}`}>
                            {displayTask}
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  <div className="mt-3 pt-3 border-t border-blue-500/10 flex items-center justify-between">
                    <div className="flex items-center gap-3 text-[7px] text-blue-400/20">
                      <span className="flex items-center gap-1">
                        <CheckCircle className="w-3 h-3 text-cyan-400/30" />
                        {done}/{total} tareas
                      </span>
                      <span className="w-px h-3 bg-blue-500/10" />
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {project.created.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' })}
                      </span>
                    </div>
                    <span className="text-[7px] text-blue-400/10 font-mono">ID: {project.id.slice(0, 6)}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {projects.length === 0 && (
            <div className="text-center py-16">
              <Folder className="w-16 h-16 text-blue-400/10 mx-auto mb-4" />
              <div className="text-lg text-blue-400/20 font-mono">No tienes proyectos</div>
              <button
                onClick={() => setShowNewProject(true)}
                className="mt-4 px-6 py-2 rounded-xl bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:from-blue-600 hover:to-cyan-600 transition-all text-sm font-mono"
              >
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