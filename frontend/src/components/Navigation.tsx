// frontend/src/components/Navigation.tsx
import React from 'react';
import { LayoutDashboard, Home, Folder, Newspaper, Settings, Zap, Users, Globe } from 'lucide-react';

type View = 'home' | 'dashboard' | 'projects' | 'news';

interface NavigationProps {
  currentView: View;
  onNavigate: (view: View) => void;
}

const colorMap: Record<string, string> = {
  home: '#22d3ee', dashboard: '#60a5fa', projects: '#f97316', news: '#a78bfa'
};

const bgMap: Record<string, string> = {
  home: 'rgba(6,182,212,0.1)', 
  dashboard: 'rgba(37,99,235,0.1)', 
  projects: 'rgba(249,115,22,0.1)', 
  news: 'rgba(167,139,250,0.1)'
};

const borderMap: Record<string, string> = {
  home: 'rgba(34,211,238,0.2)', 
  dashboard: 'rgba(96,165,250,0.2)', 
  projects: 'rgba(249,115,22,0.2)', 
  news: 'rgba(167,139,250,0.2)'
};

const Navigation: React.FC<NavigationProps> = ({ currentView, onNavigate }) => {
  const navItems = [
    { view: 'home' as View, icon: Home, label: 'Inicio' },
    { view: 'dashboard' as View, icon: LayoutDashboard, label: 'Dashboard' },
    { view: 'projects' as View, icon: Folder, label: 'Proyectos' },
    { view: 'news' as View, icon: Newspaper, label: 'Noticias' },
  ];

  return (
    <nav className="nav-side" style={{ 
      borderRight: `1px solid ${borderMap[currentView]}`,
      background: 'rgba(17,24,39,0.8)',
    }}>
      <ul className="nav-list">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.view;
          const bgColor = isActive ? colorMap[item.view] : 'rgba(96,165,250,0.1)';
          const borderColor = isActive ? borderMap[item.view] : 'rgba(96,165,250,0.1)';
          
          return (
            <li
              key={item.view}
              className="nav-item"
              style={{
                background: isActive ? bgColor : 'transparent',
                borderRadius: '12px',
                margin: '8px 0',
              }}
              onClick={() => onNavigate(item.view)}
            >
              <button 
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  borderRadius: '10px',
                  color: isActive ? '#e2e8f0' : 'rgba(147,197,253,0.5)',
                  fontWeight: isActive ? 600 : 500,
                  transition: 'all 0.2s ease',
                  fontSize: 13,
                }}
                onMouseEnter={() => {
                  if (!isActive) {
                    // Efecto hover sutil
                    const btn = event.currentTarget;
                    btn.style.color = 'rgba(96,165,250,0.7)';
                  }
                }}
                onMouseLeave={() => {
                  if (!isActive) {
                    const btn = event.currentTarget;
                    btn.style.color = 'rgba(147,197,253,0.5)';
                  }
                }}
              >
                <Icon size={20} style={{ color: isActive ? '#22d3ee' : 'rgba(96,165,250,0.3)' }} />
                <span className="nav-side-label" style={{ color: isActive ? '#22d3ee' : 'rgba(147,197,253,0.5)' }}>
                  {item.label}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
};

// Estilos CSS-in-JS inline o se podrían mover a un archivo separado
// Pero manteniendo el estilo existente con enhancement

export default Navigation;