// frontend/src/pages/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import {
  Cpu, HardDrive, Circle, Database,
  Calendar, ListTodo, Mail,
  LayoutDashboard, Radio,
  Server, Shield, Gauge,
} from 'lucide-react';
import { getStatus } from '../services/api';

const colorMap: Record<string, string> = {
  cyan: '#22d3ee',
  blue: '#60a5fa',
  green: '#4ade80',
};
const bgMap: Record<string, string> = {
  cyan: 'rgba(6,182,212,0.08)',
  blue: 'rgba(37,99,235,0.08)',
  green: 'rgba(34,197,94,0.08)',
};
const borderMap: Record<string, string> = {
  cyan: 'rgba(34,211,238,0.2)',
  blue: 'rgba(96,165,250,0.2)',
  green: 'rgba(74,222,128,0.2)',
};

const Dashboard: React.FC = () => {
  const [status, setStatus] = useState<{ status: string; modules: Record<string, boolean> } | null>(null);

  useEffect(() => {
    getStatus().then(setStatus).catch(() => setStatus(null));
  }, []);

  const modules = status?.modules || { notion: false, calendar: false, email: false, voice: false, data: false };

  const metrics = [
    { icon: Server, label: 'SISTEMA', value: 'ONLINE', c: 'cyan' },
    { icon: Cpu, label: 'CPU', value: '62%', c: 'blue' },
    { icon: HardDrive, label: 'MEMORIA', value: '74%', c: 'blue' },
    { icon: Gauge, label: 'LATENCIA', value: '12ms', c: 'cyan' },
    { icon: Database, label: 'MÓDULOS', value: `${Object.values(modules).filter(Boolean).length}/6`, c: 'blue' },
    { icon: Shield, label: 'TLS', value: 'ACTIVO', c: 'green' },
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
    <div className="page">
      <header className="page-header">
        <div className="page-header__title">
          <LayoutDashboard size={18} color="#22d3ee" />
          <h1 className="gradient-text">DASHBOARD</h1>
          <span className="page-header__sub">PANEL DE CONTROL</span>
        </div>
        <div className="badge badge-blue">
          <Circle size={8} color="#22d3ee" fill="#22d3ee" />
          <span>SYSTEM READY</span>
        </div>
      </header>

      <div className="page-body">
        <div className="page-body__inner dash-stack">
          <div className="metrics-grid">
            {metrics.map((item, i) => {
              const Icon = item.icon;
              return (
                <div
                  key={i}
                  className="glass metric-card"
                  style={{ background: bgMap[item.c], borderColor: borderMap[item.c] }}
                >
                  <div className="metric-card__top">
                    <Icon size={15} color={colorMap[item.c]} />
                    <span className="metric-card__label">{item.label}</span>
                  </div>
                  <div className="metric-card__value" style={{ color: colorMap[item.c] }}>
                    {item.value}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="dash-columns">
            <div className="glass panel">
              <div className="panel__title">MÓDULOS</div>
              <div>
                {moduleList.map((mod) => {
                  const Icon = mod.icon;
                  return (
                    <div key={mod.key} className="module-row">
                      <div className="module-row__left">
                        <Icon size={15} color={mod.active ? '#22d3ee' : 'rgba(96,165,250,0.2)'} />
                        <span style={{ color: mod.active ? 'rgba(191,219,254,0.7)' : 'rgba(96,165,250,0.2)' }}>
                          {mod.name}
                        </span>
                      </div>
                      <span className="module-row__status" style={{ color: mod.active ? '#22d3ee' : 'rgba(96,165,250,0.2)' }}>
                        {mod.active ? 'ACTIVO' : 'INACTIVO'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="glass panel">
              <div className="panel__title">COMANDOS</div>
              <div className="commands-grid">
                {commands.map((item, i) => (
                  <div key={i} className="command-card">
                    <div className="command-card__cmd">{item.cmd}</div>
                    <div className="command-card__desc">{item.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="glass status-strip">
            <div className="status-strip__left">
              <span style={{ color: '#22d3ee' }}>● ONLINE</span>
              <span className="sep">|</span>
              <span style={{ color: 'rgba(96,165,250,0.4)' }}>TOKENS: 8,214/16,000</span>
              <span className="sep">|</span>
              <span style={{ color: 'rgba(96,165,250,0.4)' }}>LATENCY: 12ms</span>
              <span className="sep">|</span>
              <span style={{ color: 'rgba(96,165,250,0.4)' }}>UPTIME: 23h 41m</span>
            </div>
            <span className="status-strip__right">v3.1 · SECURE NODE 09F-ORION</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
