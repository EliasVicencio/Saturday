import { useState, useEffect } from "react";
import {
  Newspaper,
  VolumeX,
} from "lucide-react";
import "../styles/Home.css";
import { getNewsPanel, type NewsItem } from "../services/api";

export default function NewsPage() {
  const [articles, setArticles] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const loadNews = async () => {
      setLoading(true);
      try {
        const result = await getNewsPanel();
        if (result && result.headlines && result.headlines.length > 0) {
          setArticles(
            result.headlines.map((article: NewsItem) => ({
              id: article.id || Date.now().toString(),
              title: article.title || "Sin título",
              source: article.source || "Fuente desconocida",
              description: article.description || "",
            }))
          );
        } else {
          setError("No se pudieron cargar las noticias");
        }
      } catch (err) {
        console.error('Error fetching news:', err);
        setError("Error conectando con el backend");
      } finally {
        setLoading(false);
      }
    };

    loadNews();

    // Actualizar cada 30 minutos
    const interval = setInterval(loadNews, 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, [retryCount]);

  // Volver al home (cambia la vista en App.tsx)
  const goBack = () => {
    window.dispatchEvent(new CustomEvent('go-home'));
  };

  if (loading) {
    return (
      <div className="sd" style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div className="sd__bg-grid" />
        <div style={{ textAlign: "center" }}>
          <div className="sd-logo" style={{ fontSize: "2rem", marginBottom: "1rem" }}>(Cargando noticias)</div>
          <span className="pill pill--offline">Conectando...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="sd" style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div className="sd__bg-grid" />
        <div style={{ textAlign: "center", color: "#f87171" }}>
          <div className="sd-logo" style={{ fontSize: "2rem", marginBottom: "1rem" }}>⚠️</div>
          <h2>Error al cargar noticias</h2>
          <p>{error}</p>
          <button className="composer__send" onClick={() => {
            setError(null);
            setRetryCount((count) => count + 1);
          }}>
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="sd">
      <div className="sd__bg-grid" />

      <header className="sd-topbar">
        <div className="sd-topbar__brand">
          <Newspaper size={24} className="accent" />
          <span className="sd-logo">NOTICIAS</span>
        </div>

        <div className="sd-topbar__right">
          <button
            className={`icon-square-btn ${error ? "icon-square-btn--active" : ""}`}
            onClick={goBack}
            title="Volver al inicio"
          >
            <VolumeX size={16} />
          </button>
          <span className="pill pill--online">
            <span className="dot dot--green" /> Online
          </span>
        </div>
      </header>

      <main className="sd-main">
        <div style={{ gridArea: "1 / 1 / -1 / -1" }}>
          {loading && !articles.length && (
            <div style={{ padding: "40px", textAlign: "center" }}>
              <div className="sd-logo" style={{ fontSize: "3rem", marginBottom: "1rem" }}>📰</div>
              <p>Cargando noticias...</p>
            </div>
          )}

          {articles.length === 0 && !loading && (
            <div style={{ padding: "40px", textAlign: "center", color: "#64748b" }}>
              <p>No hay noticias disponibles</p>
              <p>Intenta más tarde o usa "buscar noticias [tema]"</p>
            </div>
          )}

          {articles.length > 0 && (
            <div className="news-grid">
              {articles.map((article) => (
                <article key={article.id} className="news-card">
                  <div className="news-card__header">
                    <Newspaper size={16} className="news-card__icon" />
                    <h3 className="news-card__title">{article.title}</h3>
                  </div>
                  <div className="news-card__meta">
                    <span className="news-card__source">{article.source}</span>
                  </div>
                  <p className="news-card__excerpt">
                    {article.description || "Sin descripción disponible."}
                  </p>
                  <div className="news-card__actions">
                    <button className="news-card__btn" onClick={() => window.alert("Leyendo noticia completa: " + article.title)}>
                      Leer
                    </button>
                    <button className="news-card__btn news-card__btn--secondary" onClick={() => console.log("Compartir:", article.title)}>
                      Compartir
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}

          {articles.length === 0 && loading && (
            <div style={{ padding: "2rem", textAlign: "center" }}>
              <p>El formato de noticias del backend es diferente.</p>
              <p>Intenta el comando "noticias" en el chat principal.</p>
            </div>
          )}
        </div>
      </main>

      <footer className="sd-footer" style={{ padding: "12px 20px", marginTop: "auto" }}>
        <p className="muted" style={{ fontSize: "11px" }}>
          Actualizado {new Date().toLocaleTimeString("es-ES")}
        </p>
      </footer>
    </div>
  );
}