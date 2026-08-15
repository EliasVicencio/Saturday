# Saturday - Proyecto de IA con Integraciones

## 📋 Descripción del Proyecto
Este proyecto es un sistema de IA que integra múltiples servicios y APIs. El objetivo es proporcionar una plataforma unificada para [describe el propósito de tu IA].

## 🛠️ Tecnologías y Stack
- **Lenguaje principal**: [Python / TypeScript / etc.]
- **Framework**: [FastAPI / Next.js / etc.]
- **Bibliotecas de IA**: [TensorFlow / PyTorch / LangChain / etc.]
- **Integraciones**: [APIs externas: OpenAI, Google, etc.]
- **Base de datos**: [PostgreSQL / MongoDB / etc.]
- **Entorno de ejecución**: [Docker / Local / Cloud]

## 📁 Estructura del Repositorio (Actualizar con la real)
- `/src/` - Código fuente principal.
  - `/api/` - Endpoints de la API.
  - `/core/` - Lógica central de la IA.
  - `/integrations/` - Código para cada integración externa.
  - `/utils/` - Funciones auxiliares.
- `/tests/` - Tests unitarios y de integración.
- `/docs/` - Documentación del proyecto.
- `/config/` - Archivos de configuración (no subir secretos).
- `/scripts/` - Scripts de utilidad y despliegue.

## 🔑 Reglas de Integraciones
- **Archivos de entorno**: Las claves API se gestionan con variables de entorno (`.env`). No se suben al repositorio.
- **Nuevas integraciones**: Cada nueva integración debe añadirse como un módulo independiente dentro de `/src/integrations/`, con su propia documentación de uso.
- **Manejo de errores**: Todas las llamadas a APIs externas deben incluir manejo de errores y reintentos con backoff.

## 🚦 Estilo y Calidad de Código
- **Formateo**: Usar [Black / Prettier].
- **Linting**: Seguir las reglas de [PEP 8 / ESLint].
- **Comentarios**: Documentar funciones complejas y lógica de negocio.
- **Tipado**: Usar type hints (Python) o TypeScript estricto.

## 🧪 Pruebas
- Para cada nueva funcionalidad, se deben añadir tests automatizados.
- Los tests deben cubrir casos de éxito y de fallo (especialmente en integraciones).
- Antes de hacer un commit, asegurarse de que los tests pasan localmente.

## ⚙️ Directrices para el Agente (Sisyphus, Hephaestus, Prometheus, Atlas)
1.  **Código nuevo**: Genera código que siga la estructura y estilo definidos.
2.  **Refactorización**: Si se sugiere una refactorización, explica por qué mejora la arquitectura o el rendimiento.
3.  **Integraciones**: Para añadir una nueva API externa, primero investiga si existe un SDK oficial y propón su uso.
4.  **Seguridad**: Revisa el código en busca de vulnerabilidades comunes (inyección, exposición de secretos).
5.  **Documentación**: Si el cambio afecta a la lógica principal, actualiza la documentación correspondiente en `/docs`.
6.  **Mockups**: Cuando uses Atlas con Nano Banana 2 para generar interfaces, asegúrate de que el código se integre con el backend existente.

## 📌 Prioridades
1.  Estabilidad y robustez del sistema.
2.  Claridad y mantenibilidad del código.
3.  Eficiencia en el uso de recursos (especialmente llamadas a API externas).

## Regla de respuesta
- El agente debe dar una sola respuesta por pregunta, sin repeticiones ni análisis extensos. Si la pregunta es específica, la respuesta debe ser específica y directa.