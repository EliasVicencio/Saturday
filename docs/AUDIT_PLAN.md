# Plan de Auditoría — ISO 27001 / ISO 9001 / ISO 25010
## Proyecto Saturday

**Fecha:** 2026-08-26
**Alcance:** Sistema completo Saturday (backend Flask + frontend React + infraestructura Oracle Cloud)
**Estado:** En progreso

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [ISO 27001 — Seguridad de la Información](#2-iso-27001)
3. [ISO 9001 — Gestión de Calidad](#3-iso-9001)
4. [ISO 25010 — Calidad de Software](#4-iso-25010)
5. [Matriz de Riesgos](#5-matriz-de-riesgos)
6. [Roadmap de Remediación](#6-roadmap-de-remediación)

---

## 1. Resumen Ejecutivo

| Estándar | Puntuación Actual | Meta Mínima | Brecha |
|----------|-------------------|-------------|--------|
| ISO 27001 (Seguridad) | 5/10 | 7/10 | **2 puntos** |
| ISO 9001 (Calidad) | 3/10 | 6/10 | **3 puntos** |
| ISO 25010 (Software) | 4/10 | 7/10 | **3 puntos** |

**Hallazgos Críticos:** 2 | **Altos:** 4 | **Medios:** 8 | **Bajos:** 5

---

## 2. ISO 27001 — Seguridad de la Información

### 2.1 Dominio A.5 — Controles Organizacionales

| Control | Requisito | Estado Actual | Brecha | Prioridad |
|---------|-----------|---------------|--------|-----------|
| A.5.1 | Políticas de seguridad | No existe política formal | **CRÍTICO** | Alta |
| A.5.2 | Roles y responsabilidades | Solo 1 desarrollador | **CRÍTICO** | Media |
| A.5.3 | Segregación de funciones | Deploy + código en misma persona | **ALTO** | Media |
| A.5.7 | Amenazas de catering | Sin análisis de amenazas | **ALTO** | Media |
| A.5.15 | Control de acceso | `require_api_key` se desactiva sin variable | **ALTO** | Alta |
| A.5.23 | Seguridad en la nube | Oracle Cloud sin hardening documentado | **MEDIO** | Baja |

### 2.2 Dominio A.6 — Seguridad de Recursos Humanos

| Control | Requisito | Estado Actual | Brecha |
|---------|-----------|---------------|--------|
| A.6.1 | Screening de empleados | N/A (proyecto personal) | N/A |
| A.6.2 | Términos de empleo | N/A | N/A |

### 2.3 Dominio A.7 — Seguridad Física

| Control | Requisito | Estado Actual | Brecha |
|---------|-----------|---------------|--------|
| A.7.1 | Perímetros de seguridad | Oracle Cloud (responsabilidad compartida) | **MEDIO** |
| A.7.4 | protección contra amenazas ambientales | Oracle Cloud gestiona esto | OK |

### 2.4 Dominio A.8 — Seguridad Tecnológica

| Control | Requisito | Estado Actual | Brecha | Prioridad |
|---------|-----------|---------------|--------|-----------|
| A.8.1 | Dispositivos de usuario | Hardening del servidor | **MEDIO** | Baja |
| A.8.2 | Privilegios de acceso | sudo sin restricciones en deploy.sh | **ALTO** | Alta |
| A.8.3 | Restricción de acceso | La mayoría de endpoints son públicos | **CRÍTICO** | **Crítica** |
| A.8.4 | Acceso a código fuente | GitHub público/privado sin branch protection | **MEDIO** | Media |
| A.8.5 | Autenticación segura | API key con comparación directa (timing attack) | **ALTO** | Alta |
| A.8.9 | Gestión de configuración | Sin infrastructure as code | **MEDIO** | Media |
| A.8.10 | Reducción de vulnerabilidades | Sin escaneo de dependencias (safety, dependabot) | **ALTO** | Alta |
| A.8.11 | Reducción de datos | Sin minimización de datos en logs | **MEDIO** | Baja |
| A.8.12 | Prevención de malware | Sin antivirus en servidor | **BAJO** | Baja |
| A.8.13 | Copias de seguridad | Sin estrategia de backup documentada | **ALTO** | Alta |
| A.8.24 | Uso de criptografía | HTTPS habilitado, sin encriptación en reposo | **MEDIO** | Media |

### 2.5 Dominio A.9 — Control de Acceso

| Control | Requisito | Estado Actual | Brecha | Prioridad |
|---------|-----------|---------------|--------|-----------|
| A.9.1 | Requisitos de control de acceso | Sin política de control de acceso | **CRÍTICO** | **Crítica** |
| A.9.2 | Gestión de usuarios | Sin sistema de usuarios/roles | **ALTO** | Alta |
| A.9.3 | Gestión de privilegios | API key binaria (todo o nada) | **ALTO** | Alta |
| A.9.4 | Protección de contraseñas | Sin hashing de API keys | **MEDIO** | Media |

### 2.6 Dominio A.10 — Criptografía

| Control | Requisito | Estado Actual | Brecha |
|---------|-----------|---------------|--------|
| A.10.1 | Control de claves | API keys en texto plano en `.env` | **ALTO** |
| A.10.2 | Certificados SSL | Let's Encrypt, auto-renovado | **OK** |

### 2.7 Dominio A.12 — Seguridad Operacional

| Control | Requisito | Estado Actual | Brecha | Prioridad |
|---------|-----------|---------------|--------|-----------|
| A.12.1 | Procedimientos operacionales | Sin documentación de operaciones | **ALTO** | Alta |
| A.12.2 | Protección contra malware | Sin EDR/antivirus | **MEDIO** | Baja |
| A.12.3 | Copias de seguridad | Sin backup strategy | **ALTO** | Alta |
| A.12.4 | Registro y monitoreo | `print()` sin logging estructurado | **CRÍTICO** | **Crítica** |
| A.12.5 | Monitorización de software | Sin health checks programáticos | **MEDIO** | Media |
| A.12.6 | Gestión de vulnerabilidades | Sin escaneo de vulnerabilidades | **ALTO** | Alta |

### 2.8 Dominio A.13 — Seguridad de Comunicaciones

| Control | Requisito | Estado Actual | Brecha |
|---------|-----------|---------------|--------|
| A.13.1 | Gestión deredes | HTTPS + HTTP redirect | **OK** |
| A.13.2 | Transferencia de información | API keys en query strings (WhatsApp) | **MEDIO** |

### 2.9 Dominio A.14 — Seguridad del Desarrollo

| Control | Requisito | Estado Actual | Brecha | Prioridad |
|---------|-----------|---------------|--------|-----------|
| A.14.1 | Proceso de desarrollo | Sin CI/CD, deploy manual | **ALTO** | Alta |
| A.14.2 | Requisitos de seguridad | Sin threat modeling | **ALTO** | Alta |
| A.14.3 | Arquitectura de seguridad | Sin security architecture review | **MEDIO** | Media |
| A.14.4 | Seguridad en codificación | Sin linting, bare except clauses | **ALTO** | Alta |
| A.14.5 | Seguridad en pruebas | Sin tests de seguridad | **ALTO** | Alta |
| A.14.6 | Validación de datos | `input_validator.py` existe pero no se usa | **MEDIO** | Media |
| A.14.7 | Cambios en software | Deploy directo a producción sin staging | **ALTO** | Alta |

### 2.10 Dominio A.15 — Gestión de Incidentes

| Control | Requisito | Estado Actual | Brecha |
|---------|-----------|---------------|--------|
| A.15.1 | Preparación y gestión de incidentes | Sin plan de respuesta a incidentes | **CRÍTICO** |
| A.15.2 | Aprendizaje de incidentes | Sin proceso de lecciones aprendidas | **ALTO** |

### 2.11 Dominio A.16 — Continuidad del Negocio

| Control | Requisito | Estado Actual | Brecha |
|---------|-----------|---------------|--------|
| A.16.1 | Planificación de continuidad | Sin BCP/DRP | **ALTO** |
| A.16.2 | Implementación de continuidad | Sin failover ni redundancia | **ALTO** |

### 2.12 Dominio A.17 — Cumplimiento

| Control | Requisito | Estado Actual | Brecha |
|---------|-----------|---------------|--------|
| A.17.1 | Cumplimiento legal | Sin revisión de RGPD/LFPD | **MEDIO** |
| A.17.2 | Revisión de políticas | Sin auditorías periódicas | **MEDIO** |

---

## 3. ISO 9001 — Gestión de Calidad

### 3.1 Contexto de la Organización (Cláusula 4)

| Requisito | Estado Actual | Brecha | Prioridad |
|-----------|---------------|--------|-----------|
| 4.1 | Comprensión del contexto | Sin análisis FODA del proyecto | **MEDIO** |
| 4.2 | Partes interesadas | Sin mapeo de stakeholders | **BAJO** |
| 4.3 | Alcance del SGQ | Sin definición formal | **ALTO** |
| 4.4 | Sistema de gestión | Sin documentación de procesos | **ALTO** |

### 3.2 Liderazgo (Cláusula 5)

| Requisito | Estado Actual | Brecha |
|-----------|---------------|--------|
| 5.1 | Compromiso del liderazgo | Proyecto personal, N/A | N/A |
| 5.2 | Política de calidad | No existe | **ALTO** |
| 5.3 | Roles y responsabilidades | Solo 1 desarrollador | **MEDIO** |

### 3.3 Planificación (Cláusula 6)

| Requisito | Estado Actual | Brecha | Prioridad |
|-----------|---------------|--------|-----------|
| 6.1 | Acciones para riesgos | Sin análisis formal de riesgos | **ALTO** |
| 6.2 | Objetivos de calidad | Sin KPIs definidos | **ALTO** |
| 6.3 | Planificación de cambios | Deploy sin plan formal | **MEDIO** |

### 3.4 Soporte (Cláusula 7)

| Requisito | Estado Actual | Brecha |
|-----------|---------------|--------|
| 7.1 | Recursos | Infraestructura Oracle Cloud | **OK** |
| 7.2 | Competencia | 1 desarrollador full-stack | **MEDIO** |
| 7.3 | Toma de conciencia | N/A (proyecto personal) | N/A |
| 7.4 | Comunicación | Sin canales formales | **BAJO** |
| 7.5 | Información documentada | README básico, sin procedimientos | **ALTO** |

### 3.5 Operación (Cláusula 8)

| Requisito | Estado Actual | Brecha | Prioridad |
|-----------|---------------|--------|-----------|
| 8.1 | Planificación operacional | Sin runbooks ni SOPs | **ALTO** |
| 8.2 | Requisitos | Sin especificaciones formales | **MEDIO** |
| 8.3 | Diseño y desarrollo | Desarrollo ad-hoc sin revisión | **ALTO** |
| 8.4 | Control de proveedores | Dependencias de Notion, Google, etc. sin SLAs | **MEDIO** |
| 8.5 | Producción | Deploy manual sin verificación | **ALTO** |
| 8.6 | Liberación de producto | Sin criteria de release | **ALTO** |
| 8.7 | Control de no conformidades | Sin proceso de bug tracking | **ALTO** |

### 3.6 Evaluación del Desempeño (Cláusula 9)

| Requisito | Estado Actual | Brecha |
|-----------|---------------|--------|
| 9.1 | Monitoreo y medición | Sin métricas de calidad | **CRÍTICO** |
| 9.2 | Auditoría interna | Sin proceso de auditoría | **ALTO** |
| 9.3 | Revisión por la dirección | N/A (proyecto personal) | N/A |

### 3.7 Mejora (Cláusula 10)

| Requisito | Estado Actual | Brecha |
|-----------|---------------|--------|
| 10.1 | No conformidades y acciones | Sin proceso CAPA | **ALTO** |
| 10.2 | Mejora continua | Sin retroalimentación ni métricas | **ALTO** |

---

## 4. ISO 25010 — Calidad de Software

### 4.1 Funcionalidad Adecuada (FURPS+)

| Característica | Subcaracterísticas | Estado | Puntuación |
|----------------|-------------------|--------|------------|
| **Funcionalidad** | Completitud funcional | Múltiples integraciones (Notion, Google, Telegram, WhatsApp, Spotify, YouTube) | 7/10 |
| | Corrección funcional | Bugs conocidos: mojibake, devLog recursivo | 5/10 |
| | Pertinencia funcional | Bien alineado al propósito de asistente personal | 8/10 |

### 4.2 Fiabilidad

| Subcaracterística | Estado | Puntuación | Brecha |
|-------------------|--------|------------|--------|
| Madurez | `bare except:` oculta errores, sin logging | 3/10 | **ALTO** |
| Disponibilidad | Sin redundancia, single point of failure | 4/10 | **ALTO** |
| Tolerancia a fallos | Degradación graceful en `core.py` pero sin alertas | 5/10 | **MEDIO** |
| Capacidad de recuperación | Sin backups ni restore procedure | 2/10 | **ALTO** |

### 4.3 Usabilidad

| Subcaracterística | Estado | Puntuación | Brecha |
|-------------------|--------|------------|--------|
| Reconocimiento de adecuación | UI clara, temas consistentes | 7/10 | **BAJO** |
| Aprendibilidad | Sin onboarding ni ayuda | 4/10 | **MEDIO** |
| Operabilidad | Voz + texto, interfaz limpia | 8/10 | **BAJO** |
| Protección contra errores de usuario | Validación de inputs en desarrollo | 5/10 | **MEDIO** |
| Estética de interfaz | Diseño vault-gold consistente | 8/10 | **BAJO** |
| Accesibilidad | Sin auditoría WCAG | 3/10 | **ALTO** |

### 4.4 Rendimiento

| Subcaracterística | Estado | Puntuación | Brecha |
|-------------------|--------|------------|--------|
| Comportamiento temporal | Sin profiling ni métricas | 5/10 | **MEDIO** |
| Capacidad | Sin testing de carga | 4/10 | **MEDIO** |
| Eficiencia de recursos | gunicorn 2 workers, memory 45MB | 6/10 | **BAJO** |

### 4.5 Seguridad

| Subcaracterística | Estado | Puntuación | Brecha |
|-------------------|--------|------------|--------|
| Confidencialidad | API keys en texto plano, endpoints abiertos | 2/10 | **CRÍTICO** |
| Integridad | Sin validación cruzada, sin CSRF tokens | 4/10 | **ALTO** |
| No repudio | Sin logging de auditoría | 3/10 | **ALTO** |
| Responsabilidad | Sin trazabilidad de acciones | 3/10 | **ALTO** |
| Autenticidad | API key binaria (todo o nada) | 3/10 | **ALTO** |

### 4.6 Mantenibilidad

| Subcaracterística | Estado | Puntuación | Brecha |
|-------------------|--------|------------|--------|
| Modularidad | Buenos módulos separados en `/modules/` | 7/10 | **BAJO** |
| Reusabilidad | Código reutilizable entre Flask + Telegram | 6/10 | **BAJO** |
| Analizabilidad | Sin tests, sin linting, print-based logging | 2/10 | **CRÍTICO** |
| Modificabilidad | Sin refactoring guide, bare excepts | 4/10 | **ALTO** |
| Testabilidad | 0% cobertura, sin mocks | 1/10 | **CRÍTICO** |
| Estabilidad | Sin regression testing | 3/10 | **ALTO** |

### 4.7 Portabilidad

| Subcaracterística | Estado | Puntuación | Brecha |
|-------------------|--------|------------|--------|
| Adaptabilidad | Hardcodeado a Ubuntu/Oracle Cloud | 3/10 | **MEDIO** |
| Instalabilidad | deploy.sh manual, sin Docker | 4/10 | **MEDIO** |
| Coexistencia | Único servicio en el servidor | 6/10 | **BAJO** |
| Reemplazabilidad | Acoplado a APIs específicas (Notion, Google) | 5/10 | **MEDIO** |

---

## 5. Matriz de Riesgos

| # | Riesgo | Probabilidad | Impacto | Calificación ISO | Control Actual | Control Requerido |
|---|--------|-------------|---------|------------------|----------------|-------------------|
| R1 | Acceso no autorizado a endpoints | Alta (100%) | Alto (datos personales) | **20** | API key parcial | Auth completa + roles |
| R2 | Exfiltración de API keys | Media | Crítico (todos los servicios) | **16** | .gitignore | Vault + rotación |
| R3 | Denegación de servicio | Media | Alto (servicio caído) | **12** | Rate limiting básico | WAF + DDoS protection |
| R4 | Pérdida de datos | Media | Alto (conversaciones, tareas) | **12** | Sin backups | Backup diario + restore |
| R5 |注入 de código | Baja | Crítico (RCE) | **9** | Input validator parcial | Validación completa |
| R6 | Incumplimiento RGPD | Media | Alto (multas) | **12** | Sin política | Política de privacidad |
| R7 | Fallo en cascada (dependencias) | Media | Alto (servicio total) | **12** | Sin monitoring | Health checks + alerts |
| R8 | Código con vulnerabilidades | Alta | Alto (ataques) | **16** | Sin linting | SAST + DAST |

**Escala de calificación:** Probabilidad (1-5) × Impacto (1-5) = Calificación (1-25)
- **Crítico (20-25):** Acción inmediata
- **Alto (12-19):** Acción en 30 días
- **Medio (6-11):** Acción en 90 días
- **Bajo (1-5):** Monitoreo

---

## 6. Roadmap de Remediación

### Fase 1 — Inmediata (Semana 1-2) — Controles Críticos

| # | Acción | ISO 27001 | ISO 9001 | ISO 25010 | Esfuerzo |
|---|--------|-----------|----------|-----------|----------|
| 1.1 | **Rotar todas las API keys** expuestas en `.env` | A.8.10 | 8.7 | Seguridad | 1h |
| 1.2 | **Aplicar `@require_api_key` a TODOS los endpoints** | A.8.3, A.9.2 | 8.5 | Seguridad | 4h |
| 1.3 | **Usar `hmac.compare_digest()`** en comparación de keys | A.8.5 | 8.5 | Seguridad | 1h |
| 1.4 | **Eliminar token hardcodeado** del webhook_server.py | A.8.5 | 8.5 | Seguridad | 0.5h |
| 1.5 | **Configurar logging estructurado** (reemplazar `print()`) | A.12.4 | 9.1 | Fiabilidad | 4h |
| 1.6 | **Sanitizar errores** — no exponer `str(e)` al cliente | A.14.4 | 8.7 | Fiabilidad | 2h |
| 1.7 | **Implementar health check** `/api/health` con métricas | A.16.1 | 9.1 | Fiabilidad | 2h |
| 1.8 | **Crear política de seguridad** básica (documento) | A.5.1 | 5.2 | N/A | 2h |

### Fase 2 — Corto Plazo (Semana 3-6) — Controles Altos

| # | Acción | ISO 27001 | ISO 9001 | ISO 25010 | Esfuerzo |
|---|--------|-----------|----------|-----------|----------|
| 2.1 | **Configurar ruff** (Python linter) + **ESLint** (TS) | A.14.4 | 8.3 | Mantenibilidad | 2h |
| 2.2 | **Crear suite de tests** con pytest + vitest (mín. 30% cobertura) | A.14.5 | 8.3, 9.1 | Testabilidad | 16h |
| 2.3 | **Implementar autenticación por JWT** o sesión con tokens | A.9.2, A.9.4 | 8.5 | Seguridad | 8h |
| 2.4 | **Agregar input validation** a TODOS los endpoints | A.14.6 | 8.5 | Integridad | 4h |
| 2.5 | **Eliminar `bare except:`** — tipificar excepciones | A.14.4 | 8.3 | Fiabilidad | 4h |
| 2.6 | **Implementar retry + backoff** en llamadas a APIs externas | A.14.4 | 8.5 | Fiabilidad | 4h |
| 2.7 | **Crear estrategia de backups** (Notion data + conversaciones) | A.12.3, A.16.1 | 8.5 | Capacidad recuperación | 4h |
| 2.8 | **Configurar Dependabot/Safety** para escaneo de dependencias | A.8.10 | 8.4 | Mantenibilidad | 2h |
| 2.9 | **Eliminar API keys del frontend** — crear endpoints proxy | A.8.3 | 8.5 | Seguridad | 4h |
| 2.10 | **Documentar API** con OpenAPI/Swagger | A.14.1 | 7.5 | Analizabilidad | 4h |

### Fase 3 — Mediano Plazo (Mes 2-3) — Maduración

| # | Acción | ISO 27001 | ISO 9001 | ISO 25010 | Esfuerzo |
|---|--------|-----------|----------|-----------|----------|
| 3.1 | **Implementar CI/CD** con GitHub Actions (lint + test + deploy) | A.14.1 | 8.5, 8.6 | Mantenibilidad | 8h |
| 3.2 | **Crear environment de staging** | A.14.7 | 8.5 | Fiabilidad | 4h |
| 3.3 | **Encriptar datos en reposo** (vault, conversaciones) | A.8.24 | 8.5 | Seguridad | 8h |
| 3.4 | **Implementar WAF** o reglas de firewall avanzadas | A.8.20 | 8.5 | Seguridad | 4h |
| 3.5 | **Crear runbook de operaciones** | A.12.1 | 8.1 | N/A | 8h |
| 3.6 | **Plan de respuesta a incidentes** | A.15.1 | 8.7 | N/A | 4h |
| 3.7 | **Auditoría de accesibilidad WCAG 2.1** | N/A | N/A | Usabilidad | 8h |
| 3.8 | **Dockerizar** la aplicación | A.8.9 | 8.5 | Portabilidad | 8h |
| 3.9 | **Implementar métricas de calidad** (coverage, uptime, latency) | A.12.5 | 9.1 | Rendimiento | 4h |
| 3.10 | **Eliminar `'unsafe-eval'` de CSP** en producción | A.8.24 | 8.5 | Seguridad | 2h |

### Fase 4 — Largo Plazo (Mes 4-6) — Certificación

| # | Acción | ISO 27001 | ISO 9001 | ISO 25010 | Esfuerzo |
|---|--------|-----------|----------|-----------|----------|
| 4.1 | Realizar auditoría interna formal | A.17.2 | 9.2 | N/A | 16h |
| 4.2 | Revisión de cumplimiento RGPD/LFPD | A.17.1 | 9.1 | N/A | 8h |
| 4.3 | Implementar BCP/DRP documentado | A.16.1 | 8.5 | Fiabilidad | 16h |
| 4.4 | Obtener feedback de usuarios (encuesta) | N/A | 9.1 | Usabilidad | 4h |
| 4.5 | Revisión de lecciones aprendidas | A.15.2 | 10.1 | N/A | 4h |
| 4.6 | Evaluación de madurez completa | Todo | Todo | Todo | 16h |

---

## Anexo A — Controles Existentes (Cumplidos)

| Control | ISO 27001 | Estado |
|---------|-----------|--------|
| HTTPS con TLS 1.2/1.3 | A.8.24 | ✅ |
| HTTP → HTTPS redirect | A.13.1 | ✅ |
| CSP en nginx | A.8.24 | ✅ |
| HSTS habilitado | A.8.24 | ✅ |
| CORS restringido | A.8.3 | ✅ |
| Rate limiting | A.8.3 | ✅ (parcial) |
| .gitignore exhaustivo | A.8.4 | ✅ |
| Input validator definido | A.14.6 | ⚠️ (no usado) |
| Conventional commits | A.14.1 | ✅ |
| Degradación graceful | A.16.2 | ✅ (parcial) |
| Service worker correcto | A.8.24 | ✅ |

---

## Anexo B — Mapeo ISO 27001 Annex A → Controles Saturday

| Capítulo | Total Controles | Cumplidos | Parcial | No cumplidos |
|----------|-----------------|-----------|---------|--------------|
| A.5 Organizacionales | 37 | 2 | 3 | 32 |
| A.6 Recursos Humanos | 2 | N/A | N/A | N/A |
| A.7 Física | 15 | 4 | 1 | 10 |
| A.8 Tecnológica | 34 | 8 | 12 | 14 |
| A.9 Acceso | 14 | 1 | 4 | 9 |
| A.10 Criptografía | 2 | 1 | 0 | 1 |
| A.12 Operacional | 12 | 2 | 5 | 5 |
| A.13 Comunicaciones | 2 | 1 | 1 | 0 |
| A.14 Desarrollo | 11 | 2 | 4 | 5 |
| A.15 Incidentes | 2 | 0 | 0 | 2 |
| A.16 Continuidad | 2 | 0 | 0 | 2 |
| A.17 Cumplimiento | 2 | 0 | 1 | 1 |
| **TOTAL** | **135** | **20** | **31** | **84** |

**Porcentaje de cumplimiento:** 20/135 = **14.8%** (mínimo recomendado: 60%)
