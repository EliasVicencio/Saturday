import { useState, useEffect, useCallback } from "react";
import { ArrowLeft, ExternalLink, Share2, TrendingUp, TrendingDown } from "lucide-react";
import "../styles/News.css";
import { getNewsHeadlines, getBitcoinPrice, type Headline, type BitcoinPrice } from "../services/api";

const NEWS_SOURCES = [
  { id: "all", label: "CNN", badge: "NEWS", badgeColor: "red" },
  { id: "tech", label: "BBC News", badge: "NEWS", badgeColor: "red" },
  { id: "world", label: "DW News", badge: "NEWS", badgeColor: "red" },
  { id: "business", label: "AL Jazeerea", badge: "NEWS", badgeColor: "red" },
  { id: "science", label: "France 24", badge: "NEWS", badgeColor: "red" },
  { id: "sports", label: "NBC News", badge: "NEWS", badgeColor: "red" },
  { id: "fireship", label: "Fireship", badge: "DEV", badgeColor: "green" },
  { id: "ai", label: "AI Explained", badge: "IA", badgeColor: "purple" },
  { id: "deepmind", label: "Google DeepMind", badge: "IA", badgeColor: "purple" },
  { id: "mkbhd", label: "MKBHD", badge: "TECH", badgeColor: "blue" },
  { id: "networkchuck", label: "NetworkChuck", badge: "SEC", badgeColor: "orange" },
  { id: "linus", label: "Linus Tech Tips", badge: "TECH", badgeColor: "blue" },
];

const NEWS_FILTERS = [
  { id: "all", label: "TEC" },
  { id: "ia", label: "IA" },
  { id: "cid", label: "CID" },
  { id: "pro", label: "PRO" },
];

const formatClock = (d: Date) =>
  d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", hour12: false });

export default function NewsPage() {
  const [activeSource, setActiveSource] = useState("all");
  const [activeFilter, setActiveFilter] = useState("all");
  const [articles, setArticles] = useState<Headline[]>([]);
  const [loading, setLoading] = useState(true);
  const [available, setAvailable] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const [btc, setBtc] = useState<BitcoinPrice | null>(null);
  const [btcError, setBtcError] = useState(false);

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
    <div className="vault intel-dashboard">
      <div className="vault__bg-grid" />
      <div className="vault__scanline" />

      <header className="vault-topbar intel-topbar">
        <div className="vault-topbar__brand">
          <span className="vault-topbar__link" onClick={goBack} title="Volver al inicio">
            <ArrowLeft size={14} /> VOLVER
          </span>
          <div className="intel-title">
            <span className="intel-title__main">STARK INTEL</span>
            <span className="intel-title__sub">SALA DE CONTROL</span>
          </div>
        </div>
        <div className="vault-topbar__clock">
          <span className="vault-topbar__clock-time">{formatClock(new Date())}</span>
          <span className="intel-live-badge">
            <span className="intel-live-badge__dot" />
            EN VIVO
          </span>
        </div>
      </header>

      <div className="intel-sources-bar">
        {NEWS_SOURCES.map((source) => (
          <button
            key={source.id}
            className={`intel-source-tab ${activeSource === source.id ? "intel-source-tab--active" : ""}`}
            onClick={() => setActiveSource(source.id)}
          >
            <span className={`intel-source-tab__badge intel-source-tab__badge--${source.badgeColor}`}>
              {source.badge}
            </span>
            <span className="intel-source-tab__label">{source.label}</span>
          </button>
        ))}
      </div>

      <div className="intel-layout">
        <div className="intel-main-left">
          <div className="intel-video-area">
            <div className="intel-video-area__player">
              <iframe
                width="100%"
                height="100%"
                src="https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1&mute=1"
                title="Última hora"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
            <div className="intel-video-area__title">
              Hormuz, Oman deal, new defense pact &amp; more | Military expert analysis
            </div>
          </div>

          <div className="intel-field-section">
            <div className="intel-field-section__header">
              <span className="intel-field-section__dot" />
              <span>INTELIGENCIA DE CAMPO</span>
              <div className="intel-field-section__filters">
                {NEWS_FILTERS.map((f) => (
                  <button
                    key={f.id}
                    className={`intel-filter-btn ${activeFilter === f.id ? "intel-filter-btn--active" : ""}`}
                    onClick={() => setActiveFilter(f.id)}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="intel-field-content">
              {!available && !loading && (
                <div className="intel-empty">
                  No configuraste <code>NEWSDATA_API_KEY</code> en el backend.
                </div>
              )}
              {available && error && <div className="intel-empty">⚠️ {error}</div>}
              {available && !error && !loading && articles.length === 0 && (
                <div className="intel-empty">No hay titulares para esta categoría.</div>
              )}
              {loading && <div className="intel-empty">Cargando inteligencia de campo...</div>}

              {!loading && articles.length > 0 && (
                <div className="intel-field-grid">
                  {articles.map((article, i) => (
                    <article key={`${article.title}-${i}`} className="intel-field-card">
                      {article.image && (
                        <div className="intel-field-card__img" style={{ backgroundImage: `url(${article.image})` }} />
                      )}
                      <div className="intel-field-card__body">
                        <div className="intel-field-card__meta">
                          <span className="intel-field-card__source">{article.source_name || article.source}</span>
                          {article.category?.[0] && (
                            <span className="intel-field-card__tag">{article.category[0]}</span>
                          )}
                        </div>
                        <h3 className="intel-field-card__title">{article.title}</h3>
                        <p className="intel-field-card__excerpt">
                          {article.description || "Sin descripción."}
                        </p>
                        <div className="intel-field-card__actions">
                          <a className="intel-field-card__btn" href={article.url || "#"} target="_blank" rel="noopener noreferrer">
                            <ExternalLink size={11} /> Leer
                          </a>
                          <button className="intel-field-card__btn intel-field-card__btn--ghost" onClick={() => shareArticle(article)}>
                            <Share2 size={11} /> Compartir
                          </button>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="intel-main-right">
          <div className="intel-market-panel">
            <div className="intel-panel-header">
              <span className="intel-panel-header__dot" />
              <span>MARKET OVERVIEW</span>
            </div>
            <div className="intel-market-panel__body">
              {btcError ? (
                <div className="intel-empty">No se pudo obtener el precio</div>
              ) : btc ? (
                <>
                  <div className="intel-market-panel__price">
                    ${btc.usd.toLocaleString("en-US")}
                  </div>
                  <div className={`intel-market-panel__change ${btcUp ? "up" : "down"}`}>
                    {btcUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                    {btcUp ? "+" : ""}{btc.usd_24h_change.toFixed(2)}%
                  </div>
                  <div className="intel-market-panel__chart">
                    <svg viewBox="0 0 300 80" className="intel-chart-line">
                      <polyline
                        fill="none"
                        stroke={btcUp ? "var(--green)" : "var(--red)"}
                        strokeWidth="1.5"
                        points="0,60 20,55 40,58 60,50 80,52 100,45 120,48 140,40 160,42 180,38 200,35 220,30 240,32 260,28 280,25 300,20"
                      />
                    </svg>
                  </div>
                  <div className="intel-market-panel__sub">
                    ≈ ${btc.clp.toLocaleString("es-CL")} CLP
                  </div>
                </>
              ) : (
                <div className="intel-empty">Cargando mercado...</div>
              )}
            </div>
          </div>

          <div className="intel-ai-panel">
            <div className="intel-panel-header">
              <span className="intel-panel-header__dot" />
              <span>INTELIGENCIA IA</span>
            </div>
            <div className="intel-ai-panel__body">
              {aiAnalysis ? (
                <p className="intel-ai-panel__text">{aiAnalysis}</p>
              ) : (
                <p className="intel-ai-panel__placeholder">Sin análisis disponible todavía.</p>
              )}
              <div className="intel-ai-panel__timestamp">
                {lastUpdate ? `Último análisis: ${formatClock(lastUpdate)}` : "Esperando datos..."}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}