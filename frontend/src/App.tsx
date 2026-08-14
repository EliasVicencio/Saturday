// frontend/src/App.tsx
import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Home, Folder } from 'lucide-react';
import HomePage from './pages/Home';
import DashboardPage from './pages/Dashboard';
import ProjectsPage from './pages/Projects';
import { getStatus } from './services/api';

type View = 'home' | 'dashboard' | 'projects';

function App() {
  const [currentView, setCurrentView] = useState<View>('home');
  const [status, setStatus] = useState<{ status: string } | null>(null);

  useEffect(() => {
    getStatus().then(setStatus).catch(() => setStatus(null));
  }, []);

  const renderView = () => {
    switch (currentView) {
      case 'home':
        return <HomePage />;
      case 'dashboard':
        return <DashboardPage />;
      case 'projects':
        return <ProjectsPage />;
      default:
        return <HomePage />;
    }
  };

  const isOnline = status?.status === 'online';

  const navItems: { view: View; icon: typeof Home; label: string }[] = [
    { view: 'home', icon: Home, label: 'Inicio' },
    { view: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { view: 'projects', icon: Folder, label: 'Proyectos' },
  ];

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', background: '#0a0e1a', overflow: 'hidden' }}>
      {renderView()}

      <nav className="bottom-nav glass-strong">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = currentView === item.view;
          return (
            <button
              key={item.view}
              onClick={() => setCurrentView(item.view)}
              className={`bottom-nav__item ${active ? 'active' : ''}`}
            >
              <Icon size={16} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="status-pill glass-strong">
        <span
          className="status-dot"
          style={{ background: isOnline ? '#22d3ee' : '#facc15' }}
        />
        <span className="label">{isOnline ? 'ONLINE' : 'OFFLINE'}</span>
        <span className="divider" />
        <span className="label" style={{ opacity: 0.5 }}>v3.1</span>
      </div>
    </div>
  );
}

export default App;
