// frontend/src/pages/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { 
  Activity, Cpu, HardDrive, Zap, Wifi, 
  Circle, Database, CheckCircle, 
  Clock, Calendar, Cloud, ListTodo, StickyNote, Mail,
  LayoutDashboard, Folder, Radio, BarChart3,
  Server, Shield, Gauge, Network
} from 'lucide-react';
import { getStatus } from '../services/api';

const Dashboard: React.FC = () => {
  const [status, setStatus] = useState<{ status: string; modules: Record<string, boolean> } | null>(null);

  useEffect(() => {
    getStatus().then(setStatus).catch(() => setStatus(null));
  }, []);

  const modules = status?.modules || { notion: false, calendar: false, email: false, voice: false, data: false };

  const metrics = [
    { icon: Server, label: 'SISTEMA', value: 'ONLINE', color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20' },
    { icon: Cpu, label: 'CPU', value: '62%', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
    { icon: HardDrive, label: 'MEMORIA', value: '74%', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
    { icon: Gauge, label: 'LATENCIA', value: '12ms', color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20' },
    { icon: Database, label: 'MÓDULOS', value: `${Object.values(modules).filter(Boolean).length}/6`, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
    { icon: Shield, label: 'TLS', value: 'ACTIVO', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' },
  ];

  const moduleList = [
    { name: 'NOTION', key: 'notion', icon: ListTodo, active: modules.notion },
    { name: 'CALENDAR', key: 'calendar', icon: Calendar, active: modules.calendar },
    { name: 'MAIL', key: 'email', icon: Mail, active: modules.email },
    { name: 'VOICE', key: 'voice', icon: Radio, active: modules.voice },
    { name: 'DATA', key: 'data', icon: Database, active: modules.data },
  ];

  const commands = [
    { cmd: 'tareas', desc: 'Tareas pendientes' },
    { cmd: 'crear tarea [nombre]', desc: 'Crear tarea' },
    { cmd: 'completar tarea [nombre]', desc: 'Completar tarea' },
    { cmd: 'eliminar tarea [nombre]', desc: 'Eliminar tarea' },
    { cmd: 'nota [texto]', desc: 'Guardar nota' },
    { cmd: 'ver notas', desc: 'Ver notas' },
    { cmd: 'recordatorio [texto] a las [hora]', desc: 'Crear recordatorio' },
    { cmd: 'eventos', desc: 'Ver eventos' },
    { cmd: 'hora', desc: 'Hora actual' },
    { cmd: 'fecha', desc: 'Fecha actual' },
    { cmd: 'clima', desc: 'Clima' },
    { cmd: 'ayuda', desc: 'Ayuda' },
  ];

  return (
    <div className="w-full h-full bg-[#0a0e1a] text-white flex flex-col overflow-hidden">
      {/* ===== HEADER ===== */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-blue-500/20 bg-[#0a0e1a]/80 backdrop-blur-sm flex-shrink-0">
        <div className="flex items-center gap-3">
          <LayoutDashboard className="w-5 h-5 text-cyan-400" />
          <span className="text-lg font-bold gradient-text tracking-[0.2em]" style={{ fontFamily: 'Orbitron, sans-serif' }}>
            DASHBOARD
          </span>
          <span className="text-[8px] text-blue-400/30">PANEL DE CONTROL</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20">
          <Circle className="w-2 h-2 text-cyan-400 animate-pulse" />
          <span className="text-[8px] text-cyan-400/60 font-mono">SYSTEM READY</span>
        </div>
      </header>

      {/* ===== CONTENIDO ===== */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Métricas */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {metrics.map((item, i) => (
              <div key={i} className={`glass p-4 rounded-xl ${item.bg} border ${item.border} hover:border-cyan-400/30 transition-all`}>
                <div className="flex items-center gap-2">
                  <item.icon className={`w-4 h-4 ${item.color}`} />
                  <span className="text-[8px] text-blue-400/40">{item.label}</span>
                </div>
                <div className={`text-lg font-bold font-mono mt-1 ${item.color}`}>{item.value}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Módulos */}
            <div className="lg:col-span-1 glass rounded-xl p-5">
              <div className="text-[10px] text-cyan-400/40 font-bold tracking-[0.1em] mb-4">MÓDULOS</div>
              <div className="space-y-2">
                {moduleList.map((mod) => {
                  const Icon = mod.icon;
                  return (
                    <div key={mod.key} className="flex items-center justify-between p-3 rounded-lg bg-blue-500/5 border border-blue-500/10 hover:border-cyan-400/20 transition-all">
                      <div className="flex items-center gap-3">
                        <Icon className={`w-4 h-4 ${mod.active ? 'text-cyan-400' : 'text-blue-400/20'}`} />
                        <span className={`text-xs font-mono ${mod.active ? 'text-blue-200/70' : 'text-blue-400/20'}`}>
                          {mod.name}
                        </span>
                      </div>
                      <span className={`text-[8px] font-mono ${mod.active ? 'text-cyan-400' : 'text-blue-400/20'}`}>
                        {mod.active ? 'ACTIVO' : 'INACTIVO'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Comandos */}
            <div className="lg:col-span-2 glass rounded-xl p-5">
              <div className="text-[10px] text-cyan-400/40 font-bold tracking-[0.1em] mb-4">COMANDOS</div>
              <div className="grid grid-cols-2 gap-2">
                {commands.map((item, i) => (
                  <div key={i} className="p-3 rounded-lg bg-blue-500/5 border border-blue-500/10 hover:border-cyan-400/20 transition-all">
                    <div className="text-[10px] font-mono text-cyan-400/60">{item.cmd}</div>
                    <div className="text-[8px] text-blue-400/30">{item.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Estado del sistema */}
          <div className="glass rounded-xl p-4 flex items-center justify-between">
            <div className="flex items-center gap-6 text-[10px] font-mono">
              <span className="text-cyan-400">● ONLINE</span>
              <span className="text-blue-400/20">|</span>
              <span className="text-blue-400/40">TOKENS: 8,214/16,000</span>
              <span className="text-blue-400/20">|</span>
              <span className="text-blue-400/40">LATENCY: 12ms</span>
              <span className="text-blue-400/20">|</span>
              <span className="text-blue-400/40">UPTIME: 23h 41m</span>
            </div>
            <span className="text-[7px] text-blue-400/20">v3.1 · SECURE NODE 09F-ORION</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;