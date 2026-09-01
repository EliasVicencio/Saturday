import { useState, useEffect, useCallback } from 'react';
import {
  getProactiveContext,
  getDailyProductivity,
  getRoutines,
  getHealthToday,
  logHealth,
  type ProactiveContext,
  type ProductivityReport,
  type RoutineData,
  type HealthToday,
} from '../services/api';
import '../styles/Features.css';

interface FeaturesProps {
  onBack: () => void;
  onChat?: (message: string) => void;
}

export default function FeaturesPage({ onBack, onChat }: FeaturesProps) {
  const [activeCard, setActiveCard] = useState<string | null>(null);
  const [context, setContext] = useState<ProactiveContext | null>(null);
  const [productivity, setProductivity] = useState<ProductivityReport | null>(null);
  const [routines, setRoutines] = useState<RoutineData | null>(null);
  const [health, setHealth] = useState<HealthToday | null>(null);
  const [loading, setLoading] = useState(true);
  const [healthForm, setHealthForm] = useState({ category: 'mood', value: '', note: '' });

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [ctx, prod, rut, hlth] = await Promise.allSettled([
        getProactiveContext(),
        getDailyProductivity(),
        getRoutines(),
        getHealthToday(),
      ]);
      if (ctx.status === 'fulfilled') setContext(ctx.value);
      if (prod.status === 'fulfilled') setProductivity(prod.value);
      if (rut.status === 'fulfilled') setRoutines(rut.value);
      if (hlth.status === 'fulfilled') setHealth(hlth.value);
    } catch (e) {
      console.error('Error loading features:', e);
    }
    setLoading(false);
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleLogHealth = async () => {
    if (!healthForm.value) return;
    try {
      await logHealth(healthForm.category, healthForm.value, healthForm.note);
      setHealthForm({ category: 'mood', value: '', note: '' });
      const updated = await getHealthToday();
      setHealth(updated);
    } catch (e) {
      console.error(e);
    }
  };

  const toggleCard = (card: string) => {
    setActiveCard(activeCard === card ? null : card);
  };

  if (loading) {
    return (
      <div className="features-page">
        <div className="features-loading">
          <div className="features-spinner" />
          <p>Cargando features...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="features-page">
      <header className="features-header">
        <button className="features-back" onClick={onBack}>← Volver</button>
        <h1>🚀 Features Avanzadas</h1>
        <p className="features-subtitle">5 módulos inteligentes para tu asistente</p>
      </header>

      <div className="features-grid">
        {/* 1. Contexto Proactivo */}
        <div className={`feature-card ${activeCard === 'context' ? 'expanded' : ''}`} onClick={() => toggleCard('context')}>
          <div className="card-header">
            <span className="card-icon">🧠</span>
            <h2>Contexto Proactivo</h2>
          </div>
          {activeCard === 'context' && context && (
            <div className="card-body">
              <p className="card-summary">{context.summary}</p>
              {context.suggestions.length > 0 && (
                <div className="suggestions-list">
                  <h3>Sugerencias</h3>
                  {context.suggestions.map((s, i) => (
                    <div key={i} className={`suggestion-item priority-${s.priority}`}>
                      <span className="suggestion-text">{s.text}</span>
                      <span className="suggestion-type">{s.type}</span>
                    </div>
                  ))}
                </div>
              )}
              <div className="card-meta">
                <span>Hora: {context.time.period} ({context.time.hour}:00)</span>
                <span>{context.time.weekday}</span>
                <span>{context.time.is_weekend ? '🏠 Fin de semana' : '💼 Día laboral'}</span>
              </div>
            </div>
          )}
        </div>

        {/* 2. Resumen de Emails */}
        <div className={`feature-card ${activeCard === 'email' ? 'expanded' : ''}`} onClick={() => toggleCard('email')}>
          <div className="card-header">
            <span className="card-icon">📧</span>
            <h2>Resumen de Correos</h2>
          </div>
          {activeCard === 'email' && (
            <div className="card-body">
              <p className="card-summary">Resumen inteligente de correos electrónicos con priorización automática.</p>
              <button className="feature-btn" onClick={(e) => { e.stopPropagation(); onChat?.('resumen de correos'); }}>
                Generar resumen
              </button>
            </div>
          )}
        </div>

        {/* 3. Productividad */}
        <div className={`feature-card ${activeCard === 'productivity' ? 'expanded' : ''}`} onClick={() => toggleCard('productivity')}>
          <div className="card-header">
            <span className="card-icon">📊</span>
            <h2>Análisis de Productividad</h2>
          </div>
          {activeCard === 'productivity' && productivity && (
            <div className="card-body">
              <div className="prod-score">
                <div className="score-circle" style={{ '--score': productivity.score } as any}>
                  <span className="score-number">{productivity.score}</span>
                  <span className="score-label">/ 100</span>
                </div>
              </div>
              <div className="prod-stats">
                <div className="prod-stat">
                  <span className="stat-value">{productivity.interactions}</span>
                  <span className="stat-label">Interacciones</span>
                </div>
                <div className="prod-stat">
                  <span className="stat-value">{productivity.vault_notes}</span>
                  <span className="stat-label">Notas</span>
                </div>
                <div className="prod-stat">
                  <span className="stat-value">{productivity.reminders}</span>
                  <span className="stat-label">Recordatorios</span>
                </div>
                <div className="prod-stat">
                  <span className="stat-value">{productivity.pending_tasks}</span>
                  <span className="stat-label">Tareas</span>
                </div>
              </div>
              {productivity.top_intents.length > 0 && (
                <div className="top-intents">
                  <h3>Acciones más usadas</h3>
                  {productivity.top_intents.map((t, i) => (
                    <div key={i} className="intent-bar">
                      <span className="intent-name">{t.intent}</span>
                      <div className="intent-fill" style={{ width: `${(t.count / (productivity.top_intents[0]?.count || 1)) * 100}%` }} />
                      <span className="intent-count">{t.count}</span>
                    </div>
                  ))}
                </div>
              )}
              <div className="card-meta">
                <span>Total histórico: {productivity.total_all_time} interacciones</span>
              </div>
            </div>
          )}
        </div>

        {/* 4. Rutinas */}
        <div className={`feature-card ${activeCard === 'routines' ? 'expanded' : ''}`} onClick={() => toggleCard('routines')}>
          <div className="card-header">
            <span className="card-icon">🔄</span>
            <h2>Aprendizaje de Rutinas</h2>
          </div>
          {activeCard === 'routines' && routines && (
            <div className="card-body">
              <div className="routines-status">
                <span className={`status-badge status-${routines.status}`}>
                  {routines.status === 'active' ? '🟢 Activo' : routines.status === 'learning' ? '🟡 Aprendiendo' : '⚪ Insuficiente'}
                </span>
                <span>{routines.total_samples} muestras recolectadas</span>
              </div>
              {routines.current_suggestions.length > 0 && (
                <div className="suggestions-list">
                  <h3>Sugerencias actuales</h3>
                  {routines.current_suggestions.map((s, i) => (
                    <div key={i} className="suggestion-item priority-medium">
                      <span className="suggestion-text">{s}</span>
                    </div>
                  ))}
                </div>
              )}
              {routines.status === 'insufficient_data' && (
                <p className="card-summary">Sigue interactuando con Saturday para que aprenda tus rutinas. Se necesitan al menos 5 interacciones.</p>
              )}
            </div>
          )}
        </div>

        {/* 5. Salud */}
        <div className={`feature-card ${activeCard === 'health' ? 'expanded' : ''}`} onClick={() => toggleCard('health')}>
          <div className="card-header">
            <span className="card-icon">❤️</span>
            <h2>Seguimiento de Salud</h2>
          </div>
          {activeCard === 'health' && health && (
            <div className="card-body">
              {health.mood_average !== null && (
                <div className="health-mood">
                  <span className="mood-label">Ánimo promedio hoy:</span>
                  <span className="mood-value">{health.mood_average}/10</span>
                </div>
              )}

              <div className="health-compliance">
                {Object.entries(health.compliance).map(([key, val]) => (
                  <div key={key} className={`compliance-item ${val.met ? 'met' : 'not-met'}`}>
                    <span className="compliance-name">
                      {key === 'water' ? '💧 Agua' : key === 'exercise' ? '🏃 Ejercicio' : key === 'sleep' ? '😴 Sueño' : key}
                    </span>
                    <div className="compliance-bar">
                      <div className="compliance-fill" style={{ width: `${Math.min(100, (val.current / val.goal) * 100)}%` }} />
                    </div>
                    <span className="compliance-text">{val.current}/{val.goal}</span>
                  </div>
                ))}
              </div>

              <div className="health-form" onClick={(e) => e.stopPropagation()}>
                <h3>Registrar</h3>
                <div className="form-row">
                  <select value={healthForm.category} onChange={e => setHealthForm({...healthForm, category: e.target.value})}>
                    <option value="mood">😊 Ánimo (1-10)</option>
                    <option value="water">💧 Agua (vasos)</option>
                    <option value="exercise">🏃 Ejercicio (min)</option>
                    <option value="sleep">😴 Sueño (horas)</option>
                    <option value="weight">⚖️ Peso (kg)</option>
                    <option value="note">📝 Nota</option>
                  </select>
                  <input
                    type={healthForm.category === 'note' ? 'text' : 'number'}
                    placeholder={healthForm.category === 'note' ? 'Nota...' : 'Valor'}
                    value={healthForm.value}
                    onChange={e => setHealthForm({...healthForm, value: e.target.value})}
                  />
                  <button onClick={handleLogHealth}>✅</button>
                </div>
              </div>

              {health.total_entries > 0 && (
                <div className="card-meta">
                  <span>{health.total_entries} registros hoy</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
