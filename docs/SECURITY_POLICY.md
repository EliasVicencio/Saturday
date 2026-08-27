# Politica de Seguridad de la Informacion
## Proyecto Saturday

**Version:** 1.0
**Fecha:** 2026-08-26
**Responsable:** Elias Vicencio

---

## 1. Alcance

Esta politica aplica a todos los componentes del sistema Saturday:
- Backend API (Flask/Python)
- Frontend (React/TypeScript)
- Infraestructura (Oracle Cloud, Nginx)
- Integraciones externas (Notion, Google, Telegram, WhatsApp, Spotify)

## 2. Principios de Seguridad

### 2.1 Autenticacion y Control de Acceso
- Todos los endpoints de la API requieren autenticacion via API key (`X-API-Key`)
- Las API keys se comparan using `hmac.compare_digest()` para prevenir timing attacks
- Excepciones: `/api/greeting` y `/api/health` (endpoints publicos)
- El webhook de deploy requiere token de autenticacion

### 2.2 Gestion de Secretos
- Todas las API keys y tokens se almacenan en variables de entorno (`.env`)
- Los archivos `.env` NO se suben al repositorio (excluidos en `.gitignore`)
- Las credenciales nunca se exponen en el frontend JavaScript
- Se recomienda rotar las credenciales periodicamente (minimo cada 90 dias)

### 2.3 Transporte Seguro
- Todo el trafico se sirve via HTTPS (TLS 1.2/1.3)
- HTTP se redirige automaticamente a HTTPS
- HSTS habilitado con max-age=31536000
- Certificados SSL via Let's Encrypt con auto-renovacion

### 2.4 Proteccion contra Ataques
- Rate limiting en todos los endpoints: 200 req/min global, 30/min para chat
- Content Security Policy (CSP) habilitada
- Headers de seguridad: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
- CORS restringido al dominio de produccion

### 2.5 Logging y Monitoreo
- Logging estructurado con niveles (INFO, WARNING, ERROR)
- Los errores internos NO se exponen al cliente
- Los intentos de acceso no autorizado se registran
- Health check disponible en `/api/health`

### 2.6 Validacion de Inputs
- Validacion centralizada via `input_validator.py`
- Proteccion contra inyeccion en paths de vault
- Validacion de tipos y longitudes en todos los endpoints
- Sanitizacion de respuestas de error

## 3. Roles y Responsabilidades

| Rol | Responsabilidad |
|-----|----------------|
| Desarrollador | Implementar controles de seguridad, responder a incidentes |
| Usuario | Mantener API keys seguras, reportar vulnerabilidades |

## 4. Gestion de Incidentes

### 4.1 Tipos de Incidentes
- **Critico:** Acceso no autorizado, fuga de datos, compromise de credenciales
- **Alto:** Servicio caido, vulnerable de dependencia Critica
- **Medio:** Rate limit excedido, error de validacion
- **Bajo:** Error de logging, warning de dependencia

### 4.2 Procedimiento de Respuesta
1. **Detectar:** Monitoreo via health checks y logs
2. **Contener:** Rotar credenciales comprometidas, bloquear IPs maliciosas
3. **Erradicar:** Patchear vulnerabilidades, actualizar dependencias
4. **Recuperar:** Restaurar servicio, verificar integridad
5. **Aprender:** Documentar lecciones, actualizar politica

## 5. Copias de Seguridad

- Codigo fuente: GitHub (version control)
- Datos de Notion: API de Notion (almacenamiento persistente)
- Conversaciones: Memoria en servidor (no persistente - Mejora pendiente)
- Configuracion: Git + variables de entorno en servidor

**Objetivo:** Implementar backups automaticos diarios para datos criticos.

## 6. Cumplimiento

### 6.1 RGPD (Reglamento General de Proteccion de Datos)
- Saturday no almacena datos personales del usuario en el servidor
- Las conversaciones se procesan en memoria y no se persisten
- Las integraciones (Notion, Google) operan bajo las politicas de cada proveedor

### 6.2 ISO 27001
Esta politica esta alineada con los controles del Annex A de ISO 27001:
- A.5.1: Politicas de seguridad (este documento)
- A.8.3: Control de acceso (API key en todos los endpoints)
- A.8.5: Autenticacion segura (hmac.compare_digest)
- A.8.24: Uso de criptografia (HTTPS/TLS)
- A.12.4: Registro y monitoreo (logging estructurado)

## 7. Revision y Actualizacion

- **Frecuencia:** Al menos cada 6 meses o tras un incidente de seguridad
- **Responsable:** Desarrollador del proyecto
- **Proximo revision:** 2027-02-26

## 8. Aprobacion

| Nombre | Rol | Fecha |
|--------|-----|-------|
| Elias Vicencio | Desarrollador | 2026-08-26 |
