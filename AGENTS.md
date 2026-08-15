# 🧠 Saturday — Sistema de Agentes y Cerebro

Este documento describe la arquitectura interna, las "Skills" y el sistema de monitoreo del asistente personal Saturday.

## 1. El Núcleo (Core System)
El cerebro de Saturday está diseñado como un sistema de **agentes interconectados**. Cada agente es responsable de una función específica y se comunica con el núcleo a través del backend de Flask.

- **Motor Principal:** Flask (Python)
- **Interfaz de Usuario:** React + Vite
- **Motor de Síntesis de Voz:** Google Cloud Text-to-Speech (Chirp 3 HD)
- **Motor de Reconocimiento:** Google Speech-to-Text (STT) + Web Speech API (Browser)

## 2. Skills y Módulos (Los Nodos del Cerebro)

Cada vez que el usuario activa a Saturday, el cerebro decide qué "Skill" debe ejecutar. Las skills actualmente implementadas son:

### 🔹 Notion Skill (Base de Datos)
- **Responsabilidad:** Gestionar la comunicación con la base de datos de Notion.
- **Capacidades:** 
  - Lectura de tareas pendientes (filtrado por columna "Hecho").
  - Inserción de nuevas tareas.
- **Estado:** Activo.

### 🔹 Voz y Audio (Google TTS)
- **Responsabilidad:** Convertir texto a voz natural y transmitirla al frontend.
- **Capacidades:**
  - Generación de audio en base64 para reproducción en navegador.
  - Fallback automático a `window.speechSynthesis` si el audio principal falla.
- **Estado:** Activo.

### 🔹 Proactividad (Sistema de Recordatorios)
- **Responsabilidad:** Ejecutar comprobaciones en segundo plano sin interacción del usuario.
- **Capacidades:** 
  - Monitoreo de hora y fecha para saludos contextúales.
  - (En desarrollo) Lectura automática de calendario y avisos de reuniones.
- **Estado:** Activo.

### 🔹 Wake Word (Siempre Escucha)
- **Responsabilidad:** Mantener el micrófono del navegador en espera.
- **Capacidades:** Detectar la palabra "Saturday" para activar el modo de escucha.
- **Estado:** Activo (Frontend nativo).

### 🔹 Telegram Bot (Notificaciones)
- **Responsabilidad:** Enviar notificaciones y resúmenes de comandos a un chat privado de Telegram.
- **Capacidades:** 
  - Logging de interacciones.
  - Envío de textos y notas de voz.
- **Estado:** Activo.

### 🔹 Mapbox / Stark Maps
- **Responsabilidad:** Visualización de mapas 3D, geolocalización y rutas.
- **Capacidades:** 
  - Modo Globo y modo Calles.
  - Tráfico en vivo (toggle).
  - Edificios 3D.
- **Estado:** Activo.

## 3. El Cerebro Visual (Monitoreo en Tiempo Real)

Saturday cuenta con un panel de control interno (accesible desde la interfaz) que permite ver el estado del sistema en vivo.

- **Función:** Servir como un HUD (Head-Up Display) que refleja lo que el asistente está procesando internamente.
- **Canal de comunicación:** WebSocket (Flask-SocketIO) para transmitir eventos en tiempo real.
- **Eventos que rastrea:**
  - `PROCESSING`: El sistema está analizando un comando.
  - `NOTION_READ`: Consultando la base de datos de tareas.
  - `TTS_GENERATE`: Generando audio con Google.
  - `SKILL_EXECUTED`: Ejecución de skill exitosa.
  - `ERROR`: Se ha producido un error en algún módulo.

## 4. Flujo de Datos (Cómo piensa Saturday)

1. **Entrada:** El usuario habla (Wake Word) o escribe un comando.
2. **Procesamiento:** El Backend analiza el texto.
3. **Enrutamiento (El Cerebro):** 
   - Si es un comando de tareas → Activa **Notion Skill**.
   - Si es una pregunta general → Activa **Groq/LLM Skill** (en desarrollo).
   - Si es un cambio de mapa → Activa **Mapbox Skill**.
4. **Salida:** 
   - Se genera una respuesta de texto.
   - Se genera el audio con **Google TTS**.
   - El evento se registra en el **Log Visual** y se envía a **Telegram**.
5. **Retroalimentación:** El cerebro visual se actualiza mostrando el log y cambiando los colores de los nodos según el estado de la ejecución.

## 5. Plan de Expansión (Futuras Skills)
- **Calendar Skill:** Integración con Google Calendar para lectura de eventos y recordatorios.
- **Domótica Skill:** Control de luces y enchufes inteligentes (vía Home Assistant).
- **LLM Skill (Groq):** Respuestas a preguntas abiertas y redacción de textos usando Llama 3.1.

---

*Documento mantenido para desarrolladores y colaboradores del proyecto Saturday.*