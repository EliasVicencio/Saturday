// frontend/src/App.tsx
import React, { useState, useEffect } from 'react';
import HomePage from './pages/Home';
import DashboardPage from './pages/Dashboard';
import ProjectsPage from './pages/Projects';
import NewsPage from './pages/News';
import Navigation from './components/Navigation';
import { getStatus } from './services/api';
import './styles/App.css';

type View = 'home' | 'dashboard' | 'projects' | 'news';

function App() {
  const [currentView, setCurrentView] = useState<View>('home');
  const [status, setStatus] = useState<{ status: string } | null>(null);

  useEffect(() => {
    getStatus().then(setStatus).catch(() => setStatus(null));
  }, []);

  const renderView = () => {
    switch (currentView) {
      case 'home':
        return <HomePage onNavigate={setCurrentView} />;
      case 'dashboard':
        return <DashboardPage onNavigate={setCurrentView} />;
      case 'projects':
        return <ProjectsPage onNavigate={setCurrentView} />;
      case 'news':
        return <NewsPage onNavigate={setCurrentView} />;
      default:
        return <HomePage onNavigate={setCurrentView} />;
    }
  };

  return (
    <div className="app-container">
      {renderView()}
      <Navigation currentView={currentView} onNavigate={setCurrentView} />
    </div>
  );
}

export default App;