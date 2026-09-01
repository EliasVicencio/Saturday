// frontend/src/App.tsx
import { useState, useEffect } from 'react';
import HomePage from './pages/Home';
import NewsPage from './pages/News';
import SettingsPage from './pages/Settings';
import FeaturesPage from './pages/Features';
import './styles/App.css';

type View = 'home' | 'news' | 'settings' | 'features';

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
      ) : currentView === 'features' ? (
        <FeaturesPage onBack={() => setCurrentView('home')} />
      ) : (
        <HomePage
          onNavigateNews={() => setCurrentView('news')}
          onNavigateSettings={() => setCurrentView('settings')}
          onNavigateFeatures={() => setCurrentView('features')}
        />
      )}
    </div>
  );
}

export default App;