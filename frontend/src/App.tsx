// frontend/src/App.tsx
import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Home, Folder, Sparkles } from 'lucide-react';
import HomePage from './pages/Home';
import DashboardPage from './pages/Dashboard';
import ProjectsPage from './pages/Projects';
import { getStatus } from './services/api';

type View = 'home' | 'dashboard' | 'projects';

function App() {
  const [currentView, setCurrentView] = useState<View>('home');
  const [status, setStatus] = useState<{ status: string } | null>(null);
  const [previousView, setPreviousView] = useState<View>('home');

  useEffect(() => {
    getStatus().then(setStatus).catch(() => setStatus(null));
  }, []);

  // Función para cambiar de vista (expuesta globalmente para Saturday)
  const navigateTo = (view: View) => {
    if (view !== currentView) {
      setPreviousView(currentView);
      setCurrentView(view);
    }
  };

  // Exponer navegación globalmente para que Saturday pueda usarla
  useEffect(() => {
    (window as any).__saturdayNavigate = navigateTo;
    return () => {
      delete (window as any).__saturdayNavigate;
    };
  }, [currentView]);

  // Escuchar comandos de navegación desde el chat
  useEffect(() => {
    const handleNavigation = (event: CustomEvent) => {
      const { command } = event.detail;
      if (command === 'dashboard') navigateTo('dashboard');
      else if (command === 'proyectos' || command === 'projects') navigateTo('projects');
      else if (command === 'inicio' || command === 'home' || command === 'atrás' || command === 'volver') navigateTo('home');
    };

    window.addEventListener('saturday-navigate' as any, handleNavigation);
    return () => {
      window.removeEventListener('saturday-navigate' as any, handleNavigation);
    };
  }, []);

  const renderView = () => {
    switch (currentView) {
      case 'home':
        return <HomePage onNavigate={navigateTo} />;
      case 'dashboard':
        return <DashboardPage onNavigate={navigateTo} />;
      case 'projects':
        return <ProjectsPage onNavigate={navigateTo} />;
      default:
        return <HomePage onNavigate={navigateTo} />;
    }
  };

  return (
    <div className="app-container">
      {renderView()}

      {/* ===== INDICADOR DE VISTA ===== */}
      <div className="view-indicator">
        <span className="view-indicator__label">
          {currentView === 'home' && '💬 CHAT'}
          {currentView === 'dashboard' && '📊 DASHBOARD'}
          {currentView === 'projects' && '📁 PROYECTOS'}
        </span>
      </div>

      {/* ===== INDICADOR DE ESTADO ===== */}
      <div className="status-indicator">
        <span className={`status-dot ${status?.status === 'online' ? 'online' : 'offline'}`} />
        <span className="status-text">{status?.status === 'online' ? 'ONLINE' : 'OFFLINE'}</span>
      </div>
    </div>
  );
}

export default App;