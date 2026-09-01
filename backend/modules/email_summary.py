"""Resumen inteligente de correos electrónicos."""
import json, os, logging
from datetime import datetime
from typing import Optional, Dict, List, Any

logger = logging.getLogger("saturday.email_summary")

class EmailSummary:
    def __init__(self, core):
        self.core = core
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self._cache_file = os.path.join(self.data_dir, 'email_summary_cache.json')

    def _load_cache(self) -> Dict:
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {"last_check": None, "emails": [], "summary": ""}

    def _save_cache(self, cache: Dict):
        try:
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error guardando caché de emails: {e}")

    def _summarize_with_llm(self, emails: List[Dict]) -> str:
        try:
            if not self.core.gemini:
                return self._simple_summary(emails)

            email_texts = []
            for i, e in enumerate(emails[:10]):
                sender = e.get('from', e.get('sender', 'Desconocido'))
                subject = e.get('subject', e.get('asunto', 'Sin asunto'))
                snippet = e.get('snippet', e.get('preview', ''))[:150]
                email_texts.append(f"{i+1}. De: {sender}\n   Asunto: {subject}\n   Vista previa: {snippet}")

            prompt = f"Resume estos correos electrónicos en español, categorizándolos por prioridad (alta/media/baja). Sé conciso.\n\nCorreos:\n" + "\n".join(email_texts)
            response = self.core.gemini.chat(prompt)
            return response if response else self._simple_summary(emails)
        except Exception as e:
            logger.error(f"Error en LLM summary: {e}")
            return self._simple_summary(emails)

    def _simple_summary(self, emails: List[Dict]) -> str:
        if not emails:
            return "No hay correos recientes."
        lines = [f"📧 {len(emails)} correo(s) encontrado(s):"]
        for e in emails[:5]:
            sender = e.get('from', e.get('sender', '?'))
            subject = e.get('subject', e.get('asunto', 'Sin asunto'))
            lines.append(f"  • {sender}: {subject}")
        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        cache = self._load_cache()

        emails = []
        try:
            if self.core.email:
                raw = self.core.email.get_recent()
                if raw:
                    emails = [{"from": "correo", "subject": str(raw)[:100], "snippet": str(raw)[:200]}]
        except Exception:
            pass

        if not emails:
            try:
                if self.core.vault:
                    results = self.core.vault.search("correo")
                    if results:
                        emails = [{"from": "vault", "subject": "Correo guardado", "snippet": str(results)[:200]}]
            except Exception:
                pass

        summary = self._summarize_with_llm(emails) if emails else "No hay correos disponibles para resumir."

        cache.update({
            "last_check": datetime.now().isoformat(),
            "email_count": len(emails),
            "summary": summary
        })
        self._save_cache(cache)

        return {
            "summary": summary,
            "email_count": len(emails),
            "last_check": cache["last_check"],
            "cached": len(emails) == 0
        }

    def get_status(self) -> str:
        cache = self._load_cache()
        last = cache.get("last_check", "nunca")
        count = cache.get("email_count", 0)
        return f"📧 Última revisión: {last} | {count} correos procesados"
