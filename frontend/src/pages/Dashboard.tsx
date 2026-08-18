// frontend/src/pages/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { 
  Cpu, HardDrive, Circle, Database, Calendar, ListTodo, Mail, 
  LayoutDashboard, Radio, Server, Shield, Gauge, 
  Mic, MicOff, Globe, 
  Zap, Wifi, Box, Folder, Users, Settings 
} from 'lucide-react';
import { getStatus } from '../services/api';
import '../styles/Dashboard.css';

interface DashboardProps {
  onNavigate?: (view: 'home' | 'dashboard' | 'projects' | 'news') => void;
}

const colorMap: Record<string, string> = { 
  cyan: '#22d3ee', blue: '#60a5fa', green: '#4ade80', 
  orange: '#f97316', purple: '#a78bfa', pink: '#ec4899' 
};
const bgMap: Record<string, string> = { 
  cyan: 'rgba(6,182,212,0.08)', blue: 'rgba(37,99,235,0.08)', green: 'rgba(34,197,94,0.08)', 
  orange: 'rgba(249,115,22,0.08)', purple: 'rgba(167,139,250,0.08)', pink: 'rgba(236,72,153,0.08)' 
};
const borderMap: Record<string, string> = { 
  cyan: 'rgba(34,211,238,0.2)', blue: 'rgba(96,165,250,0.2)', green: 'rgba(74,222,128,0.2)', 
  orange: 'rgba(249,115,22,0.2)', purple: 'rgba(167,139,250,0.2)', pink: 'rgba(236,72,153,0.2)' 
};

const Dashboard: React.FC<DashboardProps> = () => {
  const [status, setStatus] = useState<{ status: string; modules: Record<string, boolean> } | null>(null);
  useEffect(() => {
    getStatus().then(setStatus).catch(() => setStatus(null));
  }, []);
  const modules = status?.modules || { notion: false, calendar: false, email: false, voice: false, data: false };

  // Tarjetas de métricas mejoradas
  const metrics = [
    { icon: Server, label: 'SISTEMA', value: 'ONLINE', c: 'cyan', bg: bgMap.cyan, border: borderMap.cyan },
    { icon: Cpu, label: 'CPU', value: '62%', c: 'blue', bg: bgMap.blue, border: borderMap.blue },
    { icon: HardDrive, label: 'MEMORIA', value: '74%', c: 'blue', bg: bgMap.blue, border: borderMap.blue },
    { icon: Gauge, label: 'LATENCIA', value: '12ms', c: 'cyan', bg: bgMap.cyan, border: borderMap.cyan },
    { icon: Database, label: 'MÓDULOS', value: `${Object.values(modules).filter(Boolean).length}/6`, c: 'blue', bg: bgMap.blue, border: borderMap.blue },
    { icon: Shield, label: 'SEGURIDAD', value: 'ACTIVO', c: 'green', bg: bgMap.green, border: borderMap.green },
    { icon: Zap, label: 'ENERGÍA', value: '95%', c: 'orange', bg: bgMap.orange, border: borderMap.orange },
    { icon: Globe, label: 'CONEXIÓN', value: 'ESTABLE', c: 'purple', bg: bgMap.purple, border: borderMap.purple },
  ];

  const moduleList = [
    { name: 'NOTION', key: 'notion', icon: ListTodo, active: modules.notion, color: colorMap.cyan },
    { name: 'CALENDAR', key: 'calendar', icon: Calendar, active: modules.calendar, color: colorMap.blue },
    { name: 'MAIL', key: 'email', icon: Mail, active: modules.email, color: colorMap.blue },
    { name: 'VOICE', key: 'voice', icon: Mic, active: modules.voice, color: colorMap.orange },
    { name: 'DATA', key: 'data', icon: Database, active: modules.data, color: colorMap.blue },
    { name: 'TELEGRAM', key: 'telegram', icon: Users, active: modules.telegram || false, color: colorMap.purple },
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
        <div className="badge-container">
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
                <div key={i} className="glass metric-card" style={{ 
                  background: item.bg, 
                  border: `1px solid ${item.border}`,
                  transition: 'all 0.3s ease'
                }}>
                  <div className="metric-card__top"><Icon size={16} color={item.c} /><span className="metric-card__label">{item.label}</span></div>
                  <div className="metric-card__value" style={{ color: item.c }}>{item.value}</div>
                </div>
              );
            })}
          </div>
          
          <div className="dash-columns">
            <div className="glass panel" style={{ marginBottom: '1.5rem' }}>
              <div className="panel__title" style={{ 
                borderBottom: `1px solid ${borderMap.cyan}`,
                paddingBottom: '12px',
                marginBottom: '12px'
              }}>MÓDULOS</div>
              {moduleList.map((mod) => {
                const Icon = mod.icon;
                return (
                  <div key={mod.key} className="module-row" style={{ 
                    borderBottom: '1px solid rgba(96,165,250,0.1)',
                    marginBottom: '8px',
                    paddingBottom: '8px'
                  }}>
                    <div className="module-row__left" style={{ 
                      color: mod.active ? mod.color : 'rgba(96,165,250,0.2)'
                    }}><Icon size={14} /><span style={{ color: mod.active ? mod.color : 'rgba(96,165,250,0.2)' }}>{mod.name}</span></div>
                    <span className="module-row__status" style={{ 
                      color: mod.active ? mod.color : 'rgba(96,165,250,0.2)'
                    }}>{mod.active ? 'ACTIVO' : 'INACTIVO'}</span>
                  </div>
                );
              })}
            </div>
            
            <div className="glass panel">
              <div className="panel__title" style={{ 
                borderBottom: `1px solid ${borderMap.blue}`,
                paddingBottom: '12px',
                marginBottom: '12px'
              }}>COMANDOS RÁPIDOS</div>
              <div className="commands-grid">
                {commands.map((item, i) => (
                  <div key={i} className="command-card" style={{ 
                    background: 'rgba(17,24,39,0.5)',
                    border: `1px solid ${borderMap.blue}`,
                    transition: 'all 0.2s ease'
                  }}>
                    <div className="command-card__cmd" style={{ color: colorMap.cyan }}>{item.cmd}</div>
                    <div className="command-card__desc" style={{ color: 'rgba(147,197,253,0.6)' }}>{item.desc}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          <div className="glass status-strip" style={{ 
            marginTop: '1.5rem',
            padding: '1.5rem',
            borderRadius: '12px'
          }}>
            <div className="status-strip__left" style={{ 
              flexDirection: 'column',
              gap: '12px'
            }}>
              <span style={{ color: '#22d3ee', fontWeight: 600 }}>● ONLINE</span>
              <span style={{ color: 'rgba(96,165,250,0.4)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em' }}>SISTEMA ACTIVO</span>
              <span style={{ color: 'rgba(96,165,250,0.4)' }}>TOKENS: 8,214/16,000</span>
              <span style={{ color: 'rgba(96,165,250,0.4)' }}>LATENCIA: 12ms</span>
              <span style={{ color: 'rgba(96,165,250,0.4)' }}>UPTIME: 23h 41m</span>
            </div>
            <span className="status-strip__right" style={{ 
              marginLeft: 'auto',
              background: 'rgba(17,24,39,0.5)',
              padding: '8px 16px',
              borderRadius: '20px',
              fontSize: 10
            }}>v3.1 · NODE 09F-ORION</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;