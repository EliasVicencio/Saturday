# agents/cap_knowledge.py - Agente de conocimiento: weather, news, crypto, vault, youtube
from .base import BaseAgent, AgentResult


class KnowledgeAgent(BaseAgent):
    name = "knowledge"
    description = "Clima, noticias, criptomonedas, busquedas en la boveda, YouTube"
    tools = ["get_weather", "get_news", "get_events", "search_vault"]

    def can_handle(self, text: str) -> float:
        text_lower = text.lower()
        keywords = {
            "clima": 0.95, "temperatura": 0.9, "lluvia": 0.85, "tiempo": 0.7,
            "noticias": 0.95, "noticia": 0.9, "periodico": 0.85, "titular": 0.8,
            "bitcoin": 0.95, "crypto": 0.9, "btc": 0.95, "ethereum": 0.9,
            "buscar": 0.6, "busca": 0.6, "encuentra": 0.5,
            "bodega": 0.9, "boveda": 0.9, "nota": 0.7, "notas": 0.7,
            "youtube": 0.95, "video": 0.7, "tutorial": 0.6,
            "tareas": 0.85, "tarea": 0.85, "calendario": 0.8, "evento": 0.7,
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

        # Clima
        if any(kw in text_lower for kw in ["clima", "temperatura", "lluvia", "tiempo", "hace calor", "hace frio"]):
            result = self.call_tool("get_weather")
            tools_log.append({"tool": "get_weather", "args": {}})
            duration = (__import__("time").time() - start) * 1000
            return AgentResult(response=str(result), agent=self.name, tools_called=tools_log, duration_ms=duration)

        # Noticias
        if any(kw in text_lower for kw in ["noticias", "noticia", "periodico", "titular"]):
            result = self.call_tool("get_news")
            tools_log.append({"tool": "get_news", "args": {}})
            duration = (__import__("time").time() - start) * 1000
            return AgentResult(response=str(result), agent=self.name, tools_called=tools_log, duration_ms=duration)

        # Bitcoin / Crypto
        if any(kw in text_lower for kw in ["bitcoin", "crypto", "btc", "ethereum", "cripto"]):
            if self.core and hasattr(self.core, '_execute_tool'):
                result = self.core._execute_tool("get_bitcoin", {})
                tools_log.append({"tool": "get_bitcoin", "args": {}})
            else:
                result = "Crypto no disponible"
            duration = (__import__("time").time() - start) * 1000
            return AgentResult(response=str(result), agent=self.name, tools_called=tools_log, duration_ms=duration)

        # Buscar en boveda
        if any(kw in text_lower for kw in ["buscar", "busca", "encuentra", "bodega", "boveda", "nota", "notas"]):
            query = text
            for prefix in ["buscar ", "busca ", "encuentra ", "leo ", "leer ", "nota ", "notas "]:
                if prefix in text_lower:
                    query = text.split(prefix)[-1].strip()
                    break
            result = self.call_tool("search_vault", {"query": query})
            tools_log.append({"tool": "search_vault", "args": {"query": query}})
            duration = (__import__("time").time() - start) * 1000
            return AgentResult(response=str(result), agent=self.name, tools_called=tools_log, duration_ms=duration)

        # YouTube
        if any(kw in text_lower for kw in ["youtube", "video", "tutorial"]):
            query = text
            for prefix in ["buscar ", "busca ", "youtube ", "video ", "tutorial "]:
                if prefix in text_lower:
                    query = text.split(prefix)[-1].strip()
                    break
            if self.core and hasattr(self.core, '_execute_tool'):
                result = self.core._execute_tool("search_youtube", {"query": query})
                tools_log.append({"tool": "search_youtube", "args": {"query": query}})
            else:
                result = "YouTube no disponible"
            duration = (__import__("time").time() - start) * 1000
            return AgentResult(response=str(result), agent=self.name, tools_called=tools_log, duration_ms=duration)

        # Tareas / Calendario
        if any(kw in text_lower for kw in ["tareas", "tarea", "calendario", "evento", "eventos"]):
            result = self.call_tool("get_events")
            tools_log.append({"tool": "get_events", "args": {}})
            duration = (__import__("time").time() - start) * 1000
            return AgentResult(response=str(result), agent=self.name, tools_called=tools_log, duration_ms=duration)

        duration = (__import__("time").time() - start) * 1000
        return AgentResult(response="No encontré información sobre eso.", agent=self.name, duration_ms=duration)
