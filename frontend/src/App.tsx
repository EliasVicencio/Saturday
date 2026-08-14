// frontend/src/App.tsx
import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Home, Folder, Sparkles, Circle } from 'lucide-react';
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

  return (
    <div className="w-full h-screen bg-[#0a0e1a] relative overflow-hidden">
      {renderView()}

      {/* ===== NAVEGACIÓN INFERIOR CON BRILLO ===== */}
      <nav className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-1 px-2 py-2 rounded-2xl glass-strong border border-blue-500/20 shadow-2xl shadow-blue-500/5">
        {[
          { view: 'home', icon: Home, label: 'Inicio' },
          { view: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
          { view: 'projects', icon: Folder, label: 'Proyectos' },
        ].map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.view;
          return (
            <button
              key={item.view}
              onClick={() => setCurrentView(item.view as View)}
              className={`flex flex-col items-center gap-0.5 px-4 py-2 rounded-xl transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 text-cyan-400 border border-cyan-400/20'
                  : 'text-blue-400/30 hover:text-blue-400/60 hover:bg-blue-500/5'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : ''}`} />
              <span className={`text-[7px] font-mono ${isActive ? 'text-cyan-400/60' : ''}`}>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* ===== INDICADOR DE ESTADO ===== */}
      <div className="fixed top-4 right-6 z-50 flex items-center gap-2 px-3 py-1.5 rounded-full glass-strong border border-blue-500/20">
        <span className={`w-1.5 h-1.5 rounded-full ${status?.status === 'online' ? 'bg-cyan-400 animate-pulse' : 'bg-yellow-400'}`} />
        <span className="text-[7px] text-blue-400/40 font-mono">
          {status?.status === 'online' ? 'ONLINE' : 'OFFLINE'}
        </span>
        <span className="w-px h-3 bg-blue-500/20" />
        <span className="text-[7px] text-blue-400/20 font-mono">v3.1</span>
      </div>
    </div>
  );
}

export default App;