# Saturday - Resumen Día 28 Ago 2026

## Estado actual del proyecto
- **URL:** https://saturday.viewdns.net
- **Último commit:** 82cefb4 (fix: rebuild frontend with correct VITE_API_URL)
- **Git repo:** https://github.com/EliasVicencio/Saturday.git

## Lo que se hizo hoy
1. **Auditoría completa de seguridad y código** - 2 subagentes analizaron todo
2. **Fixes de seguridad:** API key hardcoded eliminada, auth en endpoints abiertos, frontend .env eliminada
3. **Fixes de bugs:** imports rotos, tools sin implementar (bitcoin, youtube)
4. **Dead code eliminado:** GEMINI_TOOLS, telephone.py, audio/, brain/, imports muertos, 5 métodos muertos
5. **config.py integrado** a core.py (reemplaza os.getenv dispersos)
6. **Intent/knowledge_graph mismatches** arreglados (get_camera, system_info)
7. **VaultGraph reacciona a la voz** de Saturday (speaking state)
8. **frontend/dist/ tracked en git** para deploys automáticos
9. **Post-pull hook** en VPS para arreglar permisos de dist/

## Pendiente para mañana
- Tests unitarios (no hay ninguno)
- config.py podría conectarse a más módulos (voice.py, gemini_chat.py aún usan os.getenv)
- Wake word (openWakeWord) - Level 1 pendiente
- Push-to-talk state machine
- Provider interface para swappable STT/TTS
- Latency measurement
