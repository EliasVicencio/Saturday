# agents/cap_memory_op.py - Agente de operaciones de memoria: CRUD de recuerdos
from .base import BaseAgent, AgentResult


class MemoryOpAgent(BaseAgent):
    name = "memory_op"
    description = "Gestionar memorias: recordar, olvidar, listar recuerdos"
    tools = []
    destructive_actions = ["delete_memory"]

    def can_handle(self, text: str) -> float:
        text_lower = text.lower()
        keywords = {
            "recuerda": 0.9, "recuerdo": 0.9, "guarda": 0.85,
            "olvida": 0.95, "olvidar": 0.95, "borrar": 0.8, "eliminar memoria": 0.9,
            "que recuerdas": 0.95, "que sabes de mi": 0.9, "que sabes": 0.8,
            "mis datos": 0.8, "mi nombre": 0.9, "como me llamo": 0.95,
            "mis preferencias": 0.9, "gustos": 0.8,
            "memoria": 0.85, "recuerdos": 0.9,
        }
        score = 0.0
        for kw, s in keywords.items():
            if kw in text_lower:
                score = max(score, s)
        return score

    def process(self, text: str, chat_id: int = None, context: dict = None) -> AgentResult:
        start = __import__("time").time()
        tools_log = []
        text_lower = text.lower()

        # Olvidar
        if any(kw in text_lower for kw in ["olvida", "olvidar", "borrar memoria", "eliminar memoria"]):
            if self.core and self.core.memory_store:
                # "olvida esto" o "olvida que me llamo X"
                subject = text
                for prefix in ["olvida ", "olvidar ", "borra ", "borrar ", "elimina ", "eliminar "]:
                    if prefix in text_lower:
                        subject = text.split(prefix, 1)[-1].strip()
                        break
                memories = self.core.memory_store.search(subject, limit=5)
                if memories:
                    for m in memories:
                        self.core.memory_store.delete(m["id"])
                    tools_log.append({"tool": "memory_delete", "args": {"query": subject, "deleted": len(memories)}})
                    duration = (__import__("time").time() - start) * 1000
                    return AgentResult(
                        response=f"Olvidé {len(memories)} recuerdo(s) relacionado(s) con '{subject}'.",
                        agent=self.name, tools_called=tools_log, duration_ms=duration,
                    )
                duration = (__import__("time").time() - start) * 1000
                return AgentResult(
                    response=f"No encontré recuerdos para '{subject}'.",
                    agent=self.name, duration_ms=duration,
                )

        # Que recuerdas / que sabes
        if any(kw in text_lower for kw in ["que recuerdas", "que sabes", "mis datos", "mi nombre", "como me llamo", "mis preferencias", "gustos", "memoria", "recuerdos"]):
            if self.core and self.core.memory_store:
                facts = self.core.memory_store.get_by_type("fact", limit=10)
                prefs = self.core.memory_store.get_by_type("preference", limit=10)
                parts = []
                if facts:
                    parts.append("Hechos que recuerdo:\n" + "\n".join(f"  - {f['content']}" for f in facts[:5]))
                if prefs:
                    parts.append("Preferencias:\n" + "\n".join(f"  - {p['content']}" for p in prefs[:5]))
                if parts:
                    response = "\n\n".join(parts)
                else:
                    response = "Aún no tengo recuerdos guardados sobre vos."
                duration = (__import__("time").time() - start) * 1000
                return AgentResult(response=response, agent=self.name, duration_ms=duration)

        # Recordar algo nuevo (esto lo maneja el summarizer, pero podemos forzar)
        if any(kw in text_lower for kw in ["recuerda", "guarda", "remember"]):
            if self.core and self.core.memory_summarizer:
                saved = self.core.memory_summarizer.process_and_save(text, chat_id)
                duration = (__import__("time").time() - start) * 1000
                if saved:
                    return AgentResult(
                        response=f"Guardé {len(saved)} detalle(s) de lo que me dijiste.",
                        agent=self.name, duration_ms=duration,
                    )
                return AgentResult(
                    response="No detecté datos específicos para guardar. ¿Podés ser más explícito?",
                    agent=self.name, duration_ms=duration,
                )

        duration = (__import__("time").time() - start) * 1000
        return AgentResult(response="No entendí qué querés hacer con la memoria.", agent=self.name, duration_ms=duration)
