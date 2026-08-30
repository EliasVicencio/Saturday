import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            width: "100vw",
            height: "100vh",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            background: "#050403",
            color: "#ece3cf",
            fontFamily: "'JetBrains Mono', monospace",
            padding: "2rem",
            textAlign: "center",
          }}
        >
          <h1 style={{ color: "#d6b25e", fontSize: "1.5rem", marginBottom: "1rem" }}>
            Error del Sistema
          </h1>
          <p style={{ color: "rgba(230,218,190,0.5)", fontSize: "0.9rem", maxWidth: "500px" }}>
            Ha ocurrido un error inesperado. Recarga la página para continuar.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: "1.5rem",
              padding: "0.5rem 1.5rem",
              background: "#d6b25e",
              color: "#050403",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              fontFamily: "'JetBrains Mono', monospace",
              fontWeight: 600,
              fontSize: "0.8rem",
            }}
          >
            Recargar
          </button>
          {this.state.error && (
            <pre
              style={{
                marginTop: "1.5rem",
                fontSize: "0.7rem",
                color: "rgba(230,218,190,0.3)",
                maxWidth: "600px",
                overflow: "auto",
                maxHeight: "150px",
              }}
            >
              {this.state.error.message}
            </pre>
          )}
        </div>
      );
    }
    return this.props.children;
  }
}