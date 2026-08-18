// frontend/src/App.tsx
import React, { useState, useEffect } from 'react';
import HomePage from './pages/Home';
import Navigation from './components/Navigation';
import './components/Navigation.css';
import './styles/App.css';
import { getStatus } from './services/api';

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
        return <HomePage />;;
      default:
        return <HomePage />;
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