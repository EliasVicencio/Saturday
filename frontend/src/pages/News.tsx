// frontend/src/pages/News.tsx
import React, { useState, useEffect } from 'react';
import { Newspaper, Search, ArrowLeft, ExternalLink, Bookmark, Share2, Clock, TrendingUp, Globe, Briefcase, Heart, Beaker, Trophy, Cpu, Sparkles, RefreshCw } from 'lucide-react';
import { sendMessage } from '../services/api';
import '../styles/News.css';

interface NewsArticle { title: string; description: string; source: string; source_name: string; url: string; published_at: string; image?: string; category?: string[]; }
interface NewsProps { onNavigate?: (view: 'home' | 'dashboard' | 'projects' | 'news') => void; }

const News: React.FC<NewsProps> = ({ onNavigate }) => {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('top');
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  const categories = [
    { id: 'top', icon: TrendingUp, label: 'Destacadas' },
    { id: 'world', icon: Globe, label: 'Mundo' },
    { id: 'business', icon: Briefcase, label: 'Negocios' },
    { id: 'technology', icon: Cpu, label: 'Tecnología' },
    { id: 'science', icon: Beaker, label: 'Ciencia' },
    { id: 'health', icon: Heart, label: 'Salud' },
    { id: 'sports', icon: Trophy, label: 'Deportes' },
    { id: 'entertainment', icon: Sparkles, label: 'Entretenimiento' },
  ];

  useEffect(() => { fetchNews(); }, [selectedCategory]);

  const fetchNews = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const message = selectedCategory === 'top' ? 'noticias' : `noticias de ${selectedCategory}`;
      const response = await sendMessage(message);
      const parsed = parseNewsResponse(response.response);
      if (parsed.length > 0) setArticles(parsed);
      else { setError('No se encontraron noticias para esta categoría'); setArticles([]); }
    } catch (error) { console.error('Error fetching news:', error); setError('Error al cargar las noticias'); setArticles([]); }
    finally { setIsLoading(false); }
  };

  const parseNewsResponse = (text: string): NewsArticle[] => {
    const articles: NewsArticle[] = [];
    const lines = text.split('\n');
    let currentArticle: Partial<NewsArticle> = {};
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.match(/^\*\*\d+\.\s/)) {
        if (currentArticle.title) articles.push(currentArticle as NewsArticle);
        currentArticle = { title: line.replace(/^\*\*\d+\.\s/, '').replace(/\*\*$/, '') };
      } else if (line.startsWith('📌 *Fuente:*')) {
        currentArticle.source = line.replace('📌 *Fuente:*', '').trim();
        currentArticle.source_name = currentArticle.source;
      } else if (line.startsWith('🏷️ *Categoría:*')) {
        currentArticle.category = line.replace('🏷️ *Categoría:*', '').split(',').map(c => c.trim());
      } else if (line.startsWith('📝 ')) {
        currentArticle.description = line.replace('📝 ', '');
      }
    }
    if (currentArticle.title) articles.push(currentArticle as NewsArticle);
    return articles;
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await sendMessage(`buscar noticias ${searchQuery}`);
      const parsed = parseNewsResponse(response.response);
      if (parsed.length > 0) setArticles(parsed);
      else { setError(`No se encontraron noticias sobre "${searchQuery}"`); setArticles([]); }
    } catch (error) { console.error('Error searching news:', error); setError('Error al buscar noticias'); setArticles([]); }
    finally { setIsLoading(false); }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => { if (e.key === 'Enter') handleSearch(); };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return 'Hoy';
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diff = now.getTime() - date.getTime();
      if (diff < 3600000) { const mins = Math.floor(diff / 60000); return `hace ${mins} minuto${mins !== 1 ? 's' : ''}`; }
      else if (diff < 86400000) { const hours = Math.floor(diff / 3600000); return `hace ${hours} hora${hours !== 1 ? 's' : ''}`; }
      else return date.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
    } catch { return 'Hoy'; }
  };

  const getCategoryIcon = (category: string) => {
    const found = categories.find(c => c.id === category);
    if (found) { const Icon = found.icon; return <Icon className="w-3 h-3" />; }
    return <TrendingUp className="w-3 h-3" />;
  };

  return (
    <div className="page">
      <header className="page-header">
        <div className="page-header__title">
          <button onClick={() => onNavigate && onNavigate('home')} className="back-btn"><ArrowLeft size={16} /></button>
          <Newspaper size={18} color="#22d3ee" /><h1 className="gradient-text">NOTICIAS</h1><span className="page-header__sub">ACTUALIDAD</span>
        </div>
        <button onClick={fetchNews} className="icon-btn glass" title="Actualizar noticias"><RefreshCw size={16} color="#22d3ee" /></button>
      </header>

      <div className="news-categories">
        {categories.map((cat) => {
          const Icon = cat.icon;
          return (
            <button key={cat.id} onClick={() => setSelectedCategory(cat.id)} className={`category-chip ${selectedCategory === cat.id ? 'active' : ''}`}>
              <Icon size={14} /><span>{cat.label}</span>
            </button>
          );
        })}
      </div>

      <div className="news-search">
        <div className="search-wrapper">
          <Search size={16} className="search-icon" />
          <input type="text" placeholder="Buscar noticias..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyDown={handleKeyPress} className="search-input" />
          <button onClick={handleSearch} className="search-btn">Buscar</button>
        </div>
      </div>

      <div className="page-body">
        <div className="page-body__inner">
          {isLoading ? (
            <div className="news-loading"><div className="loading-spinner"></div><span>Cargando noticias...</span></div>
          ) : error ? (
            <div className="news-error"><Newspaper size={48} /><p>{error}</p><button onClick={fetchNews} className="gradient-btn">Reintentar</button></div>
          ) : articles.length === 0 ? (
            <div className="news-empty"><Newspaper size={48} /><p>No hay noticias disponibles en esta categoría</p><button onClick={() => setSelectedCategory('top')} className="gradient-btn">Ver Destacadas</button></div>
          ) : (
            <div className="news-grid">
              {articles.map((article, index) => (
                <div key={index} className="news-card glass">
                  <div className="news-card__header">
                    <div className="news-card__source"><span className="source-dot" /><span className="source-name">{article.source_name || article.source || 'Fuente'}</span></div>
                    {article.category && article.category.length > 0 && (
                      <div className="news-card__categories">
                        {article.category.slice(0, 2).map((cat, i) => (
                          <span key={i} className="category-tag">{getCategoryIcon(cat)}<span>{cat}</span></span>
                        ))}
                      </div>
                    )}
                  </div>
                  <h3 className="news-card__title">{article.title}</h3>
                  {article.description && <p className="news-card__description">{article.description}</p>}
                  <div className="news-card__footer">
                    <span className="news-card__time"><Clock size={12} />{formatDate(article.published_at)}</span>
                    <div className="news-card__actions">
                      <a href={article.url} target="_blank" rel="noopener noreferrer" className="action-btn"><ExternalLink size={14} /><span>Leer</span></a>
                      <button className="action-btn"><Bookmark size={14} /></button>
                      <button className="action-btn"><Share2 size={14} /></button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default News;