// frontend/src/App.tsx
import { useState, useEffect } from 'react';
import HomePage from './pages/Home';
import NewsPage from './pages/News';
import SettingsPage from './pages/Settings';
import './styles/App.css';

type View = 'home' | 'news' | 'settings';

function App() {
  const [currentView, setCurrentView] = useState<View>('home');

  useEffect(() => {
    const goHome = () => setCurrentView('home');
    window.addEventListener('go-home', goHome);
    return () => window.removeEventListener('go-home', goHome);
  }, []);

  return (
    <div className="app-container">
      {currentView === 'news' ? (
        <NewsPage />
      ) : currentView === 'settings' ? (
        <SettingsPage onBack={() => setCurrentView('home')} />
      ) : (
        <HomePage
          onNavigateNews={() => setCurrentView('news')}
          onNavigateSettings={() => setCurrentView('settings')}
        />
      )}
    </div>
  );
}

export default App;