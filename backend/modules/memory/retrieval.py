# memory/retrieval.py - Recuperar contexto relevante antes de responder
from typing import List, Dict, Optional
from .store import MemoryStore, Memory

class MemoryRetriever:
    def __init__(self, store: MemoryStore):
        self._store = store
        self._max_context_memories = 5

    def before_respond(self, text, chat_id=None):
        memories = self._find_relevant(text, chat_id)
        if not memories:
            return ""
        return self._format_context(memories)

    def _find_relevant(self, text, chat_id=None):
        keywords = self._extract_keywords(text)
        results, seen_ids = [], set()
        for kw in keywords:
            for m in self._store.search(query=kw, limit=3):
                if m.id not in seen_ids:
                    results.append(m)
                    seen_ids.add(m.id)
        if chat_id:
            for p in self._store.search(mem_type="preference", chat_id=chat_id, limit=5):
                if p.id not in seen_ids:
                    results.append(p)
                    seen_ids.add(p.id)
        for f in self._store.search(mem_type="fact", limit=5):
            if f.id not in seen_ids:
                results.append(f)
                seen_ids.add(f.id)
        for n in self._store.search(mem_type="note", limit=3):
            if n.id not in seen_ids:
                results.append(n)
                seen_ids.add(n.id)
        results.sort(key=lambda m: (-m.confidence, m.created_at), reverse=True)
        return results[:self._max_context_memories]

    def _extract_keywords(self, text):
        stop = {"el","la","los","las","un","una","de","del","al","en","con","por","para","sin","que","como","cuando","donde","quien","y","o","a","es","son","esta","hay","soy","eres","tiene","tengo","hoy","ayer","maana","ahora","si","no","me","te","le","nos","mi","tu","su"}
        return [w.strip(".,;:!?()[]{}\"\'") for w in text.lower().split() if len(w.strip(".,;:!?()[]{}\"\'")) > 2 and w.strip(".,;:!?()[]{}\"\'") not in stop][:5]

    def _format_context(self, memories):
        if not memories:
            return ""
        lines = ["[MEMORIA DEL USUARIO - contexto relevante]"]
        for m in memories:
            prefix = {"fact":"Hecho","preference":"Preferencia","event":"Evento","decision":"Decision","episode":"Episodio","note":"Nota"}.get(m.mem_type, m.mem_type.capitalize())
            lines.append(f"- [{prefix}] {m.content}")
        lines.append("[FIN MEMORIA]")
        return "\n".join(lines)

    def get_user_facts(self, chat_id, limit=20):
        return self._store.search(mem_type="fact", chat_id=chat_id, limit=limit)

    def get_user_preferences(self, chat_id):
        return self._store.search(mem_type="preference", chat_id=chat_id, limit=20)
