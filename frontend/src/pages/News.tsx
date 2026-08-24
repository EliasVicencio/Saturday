import { useState, useEffect, useCallback } from "react";
import { Newspaper, ArrowLeft, ExternalLink, Share2, Bitcoin, TrendingUp, TrendingDown } from "lucide-react";
import "../styles/Home.css";
import "../styles/News.css";
import { getNewsHeadlines, getBitcoinPrice, type Headline, type BitcoinPrice } from "../services/api";

const CATEGORIES: { id: string | undefined; label: string }[] = [
  { id: undefined, label: "Portada" },
  { id: "technology", label: "Tecnología" },
  { id: "business", label: "Negocios" },
  { id: "world", label: "Mundo" },
  { id: "science", label: "Ciencia" },
  { id: "sports", label: "Deportes" },
];

const formatClock = (d: Date) =>
  d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", hour12: false });

export default function NewsPage() {
  const [category, setCategory] = useState<string | undefined>(undefined);
  const [articles, setArticles] = useState<Headline[]>([]);
  const [loading, setLoading] = useState(true);
  const [available, setAvailable] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const [btc, setBtc] = useState<BitcoinPrice | null>(null);
  const [btcError, setBtcError] = useState(false);

  const loadNews = useCallback(async (cat: string | undefined) => {
    setLoading(true);
    setError(null);
    try {
      const result = await getNewsHeadlines(cat, 9);
      setAvailable(result.available);
      setArticles(result.articles);
      setLastUpdate(new Date());
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
    loadNews(category);
  }, [category, loadNews]);

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
      } catch {
        // el usuario canceló, no hacemos nada
      }
    }
    if (article.url) {
      await navigator.clipboard.writeText(article.url);
    }
  };

  const btcUp = (btc?.usd_24h_change ?? 0) >= 0;

  return (
    <div className="vault">
      <div className="vault__bg-grid" />
      <div className="vault__scanline" />

      <header className="vault-topbar">
        <div className="vault-topbar__brand">
          <span className="vault-topbar__link" onClick={goBack} title="Volver al inicio">
            <ArrowLeft size={16} />
          </span>
          <span className="vault-logo">
            <Newspaper size={18} style={{ marginRight: 8, verticalAlign: "-3px" }} />
            NOTICIAS
          </span>
          <span className="vault-subtitle">PANEL DE INFORMACIÓN</span>
        </div>
        <div className="vault-topbar__clock">
          <span className="vault-topbar__clock-time">{formatClock(new Date())}</span>
          <span className="vault-topbar__clock-label">
            {lastUpdate ? `ACTUALIZADO ${formatClock(lastUpdate)}` : "CARGANDO"}
          </span>
        </div>
      </header>

      <div className="news-layout">
        {/* ===== PANEL BITCOIN ===== */}
        <div className="news-btc-card">
          <div className="news-btc-card__icon">
            <Bitcoin size={22} />
          </div>
          <div className="news-btc-card__body">
            <div className="news-btc-card__label">BITCOIN · BTC/USD</div>
            {btcError ? (
              <div className="news-btc-card__error">No se pudo obtener el precio</div>
            ) : btc ? (
              <>
                <div className="news-btc-card__price">
                  ${btc.usd.toLocaleString("en-US")}
                  <span className={`news-btc-card__change ${btcUp ? "up" : "down"}`}>
                    {btcUp ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                    {Math.abs(btc.usd_24h_change)}% 24h
                  </span>
                </div>
                <div className="news-btc-card__sub">
                  ≈ ${btc.clp.toLocaleString("es-CL")} CLP
                </div>
              </>
            ) : (
              <div className="news-btc-card__loading">Cargando precio...</div>
            )}
          </div>
        </div>

        {/* ===== TABS DE CATEGORÍA ===== */}
        <div className="news-tabs">
          {CATEGORIES.map((c) => (
            <button
              key={c.label}
              className={`news-tab ${category === c.id ? "news-tab--active" : ""}`}
              onClick={() => setCategory(c.id)}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* ===== ESTADOS ===== */}
        {!available && !loading && (
          <div className="news-empty">
            📰 No configuraste <code>NEWSDATA_API_KEY</code> en el backend, así que no hay noticias disponibles.
          </div>
        )}

        {available && error && (
          <div className="news-empty">⚠️ {error}</div>
        )}

        {available && !error && !loading && articles.length === 0 && (
          <div className="news-empty">No hay titulares para esta categoría por ahora.</div>
        )}

        {loading && (
          <div className="news-empty">Cargando titulares...</div>
        )}

        {/* ===== GRID DE NOTICIAS ===== */}
        {!loading && articles.length > 0 && (
          <div className="news-grid">
            {articles.map((article, i) => (
              <article key={`${article.title}-${i}`} className="news-card">
                {article.image && (
                  <div className="news-card__image" style={{ backgroundImage: `url(${article.image})` }} />
                )}
                <div className="news-card__body">
                  <div className="news-card__meta">
                    <span className="news-card__source">{article.source_name || article.source}</span>
                    {article.category?.[0] && (
                      <span className="news-card__tag">{article.category[0]}</span>
                    )}
                  </div>
                  <h3 className="news-card__title">{article.title}</h3>
                  <p className="news-card__excerpt">
                    {article.description || "Sin descripción disponible."}
                  </p>
                  <div className="news-card__actions">
                    <a
                      className="news-card__btn"
                      href={article.url || "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <ExternalLink size={12} /> Leer
                    </a>
                    <button className="news-card__btn news-card__btn--secondary" onClick={() => shareArticle(article)}>
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
  );
}