import { useState, useEffect, useCallback } from "react";
import { Newspaper, ArrowLeft, ExternalLink, Share2, Bitcoin, TrendingUp, TrendingDown, Play, Brain, Rss } from "lucide-react";
import "../styles/News.css";
import { getNewsHeadlines, getBitcoinPrice, type Headline, type BitcoinPrice } from "../services/api";

const NEWS_SOURCES = [
  { id: "all", label: "Todos" },
  { id: "tech", label: "Tecnología" },
  { id: "business", label: "Negocios" },
  { id: "world", label: "Mundo" },
  { id: "science", label: "Ciencia" },
  { id: "sports", label: "Deportes" },
];

const SAMPLE_VIDEOS = [
  { id: "dQw4w9WgXcQ", title: "Última hora: Noticias de última generación" },
  { id: "9bZkp7q19f0", title: "Resumen del día en tecnología" },
];

const formatClock = (d: Date) =>
  d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", hour12: false });

export default function NewsPage() {
  const [activeSource, setActiveSource] = useState("all");
  const [articles, setArticles] = useState<Headline[]>([]);
  const [loading, setLoading] = useState(true);
  const [available, setAvailable] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const [btc, setBtc] = useState<BitcoinPrice | null>(null);
  const [btcError, setBtcError] = useState(false);

  const [selectedVideo, setSelectedVideo] = useState(SAMPLE_VIDEOS[0]);
  const [aiAnalysis, setAiAnalysis] = useState<string | null>(null);

  const loadNews = useCallback(async (source: string) => {
    setLoading(true);
    setError(null);
    try {
      const category = source === "all" ? undefined : source;
      const result = await getNewsHeadlines(category, 12);
      setAvailable(result.available);
      setArticles(result.articles);
      setLastUpdate(new Date());
      
      if (result.articles.length > 0) {
        const topHeadlines = result.articles.slice(0, 3).map(a => a.title).join(" | ");
        setAiAnalysis(`Análisis de las principales noticias: ${topHeadlines}. Tendencia general: información en desarrollo.`);
      }
    } catch {
      setError("No pude conectar con el backend.");
      setArticles([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadBtc = useCallback(async () => {
    try {
      setBtc(await getBitcoinPrice());
      setBtcError(false);
    } catch {
      setBtcError(true);
    }
  }, []);

  useEffect(() => {
    loadNews(activeSource);
  }, [activeSource, loadNews]);

  useEffect(() => {
    loadBtc();
    const interval = setInterval(loadBtc, 60000);
    return () => clearInterval(interval);
  }, [loadBtc]);

  const goBack = () => window.dispatchEvent(new CustomEvent("go-home"));

  const shareArticle = async (article: Headline) => {
    if (navigator.share) {
      try {
        await navigator.share({ title: article.title, url: article.url });
        return;
      } catch {}
    }
    if (article.url) {
      await navigator.clipboard.writeText(article.url);
    }
  };

  const btcUp = (btc?.usd_24h_change ?? 0) >= 0;

  return (
    <div className="intel-dashboard">
      <div className="intel-dashboard__grid-bg" />
      <div className="intel-dashboard__scanline" />

      <header className="intel-header">
        <div className="intel-header__brand">
          <span className="intel-header__link" onClick={goBack} title="Volver al inicio">
            <ArrowLeft size={16} />
          </span>
          <span className="intel-header__logo">
            <Newspaper size={18} style={{ marginRight: 8, verticalAlign: "-3px" }} />
            SATURDAY INTEL
          </span>
          <span className="intel-header__subtitle">SALA DE CONTROL</span>
          <span className="intel-header__live">
            <span className="intel-header__live-dot" />
            EN VIVO
          </span>
        </div>
        <div className="intel-header__clock">
          <span className="intel-header__clock-time">{formatClock(new Date())}</span>
          <span className="intel-header__clock-label">
            {lastUpdate ? `ACTUALIZADO ${formatClock(lastUpdate)}` : "CARGANDO"}
          </span>
        </div>
      </header>

      <div className="intel-sources">
        {NEWS_SOURCES.map((source) => (
          <button
            key={source.id}
            className={`intel-source-btn ${activeSource === source.id ? "intel-source-btn--active" : ""}`}
            onClick={() => setActiveSource(source.id)}
          >
            {source.label}
          </button>
        ))}
      </div>

      <div className="intel-main">
        <div className="intel-main__left">
          <div className="intel-video-section">
            <div className="intel-video-section__header">
              <Play size={14} />
              <span>VIDEO EN VIVO</span>
            </div>
            <div className="intel-video-section__player">
              <iframe
                width="100%"
                height="100%"
                src={`https://www.youtube.com/embed/${selectedVideo.id}?autoplay=1&mute=1`}
                title={selectedVideo.title}
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
            <div className="intel-video-section__info">
              <h4>{selectedVideo.title}</h4>
              <div className="intel-video-section__selector">
                {SAMPLE_VIDEOS.map((video) => (
                  <button
                    key={video.id}
                    className={`intel-video-btn ${selectedVideo.id === video.id ? "intel-video-btn--active" : ""}`}
                    onClick={() => setSelectedVideo(video)}
                  >
                    {video.title}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="intel-news-section">
            <div className="intel-news-section__header">
              <Rss size={14} />
              <span>INTELIGENCIA DE CAMPO</span>
            </div>

            {!available && !loading && (
              <div className="intel-empty">
                📰 No configuraste <code>NEWSDATA_API_KEY</code> en el backend, así que no hay noticias disponibles.
              </div>
            )}

            {available && error && (
              <div className="intel-empty">⚠️ {error}</div>
            )}

            {available && !error && !loading && articles.length === 0 && (
              <div className="intel-empty">No hay titulares para esta categoría por ahora.</div>
            )}

            {loading && (
              <div className="intel-empty">Cargando inteligencia de campo...</div>
            )}

            {!loading && articles.length > 0 && (
              <div className="intel-news-grid">
                {articles.map((article, i) => (
                  <article key={`${article.title}-${i}`} className="intel-news-card">
                    {article.image && (
                      <div className="intel-news-card__image" style={{ backgroundImage: `url(${article.image})` }} />
                    )}
                    <div className="intel-news-card__body">
                      <div className="intel-news-card__meta">
                        <span className="intel-news-card__source">{article.source_name || article.source}</span>
                        {article.category?.[0] && (
                          <span className="intel-news-card__tag">{article.category[0]}</span>
                        )}
                      </div>
                      <h3 className="intel-news-card__title">{article.title}</h3>
                      <p className="intel-news-card__excerpt">
                        {article.description || "Sin descripción disponible."}
                      </p>
                      <div className="intel-news-card__actions">
                        <a
                          className="intel-news-card__btn"
                          href={article.url || "#"}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <ExternalLink size={12} /> Leer
                        </a>
                        <button className="intel-news-card__btn intel-news-card__btn--secondary" onClick={() => shareArticle(article)}>
                          <Share2 size={12} /> Compartir
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="intel-main__right">
          <div className="intel-btc-section">
            <div className="intel-btc-section__header">
              <Bitcoin size={14} />
              <span>MERCADOS</span>
            </div>
            <div className="intel-btc-card">
              <div className="intel-btc-card__icon">
                <Bitcoin size={22} />
              </div>
              <div className="intel-btc-card__body">
                <div className="intel-btc-card__label">BITCOIN · BTC/USD</div>
                {btcError ? (
                  <div className="intel-btc-card__error">No se pudo obtener el precio</div>
                ) : btc ? (
                  <>
                    <div className="intel-btc-card__price">
                      ${btc.usd.toLocaleString("en-US")}
                      <span className={`intel-btc-card__change ${btcUp ? "up" : "down"}`}>
                        {btcUp ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                        {Math.abs(btc.usd_24h_change)}% 24h
                      </span>
                    </div>
                    <div className="intel-btc-card__sub">
                      ≈ ${btc.clp.toLocaleString("es-CL")} CLP
                    </div>
                  </>
                ) : (
                  <div className="intel-btc-card__loading">Cargando precio...</div>
                )}
              </div>
            </div>
          </div>

          <div className="intel-ai-section">
            <div className="intel-ai-section__header">
              <Brain size={14} />
              <span>INTELIGENCIA IA</span>
            </div>
            <div className="intel-ai-content">
              {aiAnalysis ? (
                <p className="intel-ai-content__text">{aiAnalysis}</p>
              ) : (
                <p className="intel-ai-content__placeholder">Sin análisis disponible todavía.</p>
              )}
              <div className="intel-ai-content__timestamp">
                {lastUpdate ? `Último análisis: ${formatClock(lastUpdate)}` : "Esperando datos..."}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}