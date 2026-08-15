// frontend/src/components/Navigation.tsx
import React from 'react';
import { LayoutDashboard, Home, Folder, Newspaper } from 'lucide-react';

type View = 'home' | 'dashboard' | 'projects' | 'news';

interface NavigationProps {
  currentView: View;
  onNavigate: (view: View) => void;
}

const Navigation: React.FC<NavigationProps> = ({ currentView, onNavigate }) => {
  const navItems = [
    { view: 'home' as View, icon: Home, label: 'Inicio' },
    { view: 'dashboard' as View, icon: LayoutDashboard, label: 'Dashboard' },
    { view: 'projects' as View, icon: Folder, label: 'Proyectos' },
    { view: 'news' as View, icon: Newspaper, label: 'Noticias' },
  ];

  return (
    <div className="nav-side">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = currentView === item.view;
        return (
          <button
            key={item.view}
            onClick={() => onNavigate(item.view)}
            className={`nav-side-btn ${isActive ? 'active' : ''}`}
            title={item.label}
          >
            <Icon size={20} />
            <span className="nav-side-label">{item.label}</span>
          </button>
        );
      })}
    </div>
  );
};

export default Navigation;