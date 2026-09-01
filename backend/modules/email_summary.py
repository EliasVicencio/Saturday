"""Resumen inteligente de correos electronicos."""
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
            logger.error(f"Error guardando cache de emails: {e}")

    def _summarize_with_llm(self, emails: List[Dict]) -> str:
        try:
            if not self.core.gemini:
                return self._simple_summary(emails)

            email_texts = []
            for i, e in enumerate(emails[:5]):
                sender = e.get('from', 'Desconocido')
                subject = e.get('subject', 'Sin asunto')
                body = e.get('body', e.get('snippet', ''))[:200]
                url = e.get('url', '')
                email_texts.append(f"De: {sender} | Asunto: {subject}\nContenido: {body}\nURL: {url}")

            prompt = """Eres Saturday, el asistente personal de Elias. Analiza estos correos y responde SOLO lo esencial, como si le hablaras a tu jefe.

REGLAS:
- NO listes todos los correos uno por uno
- NO digas "De: fulano" ni "Asunto: tal cosa"
- Habla de forma natural, como un asistente personal
- SOLO menciona correos que sean ACCIONABLES o URGENTES
- Si un correo es promo o basura, NO lo menciones
- Para cada correo importante, di QUE HACER y pregunta si quiere abrirlo
- Si no hay nada importante, di "No hay nada urgente en tus correos"

EJEMPLOS de como responder:
- "Tienes una alerta de seguridad de Google en tu cuenta. ¿Quieres que abra el correo para revisarla?"
- "Tu jefe te pidio un reporte para manana a las 8. ¿Quieres que abra el correo con los detalles?"
- "Tienes 2 invitaciones de LinkedIn. ¿Las revisamos?"
- "No hay nada urgente, solo promociones."

Correos para analizar:
""" + "\n\n".join(email_texts)

            logger.info(f"Calling LLM with {len(email_texts)} emails")
            response = self.core.gemini.chat(prompt)
            logger.info(f"LLM response length: {len(response) if response else 0}")
            if response:
                return response
            else:
                logger.warning("LLM returned empty response, using simple summary")
                return self._simple_summary(emails)
        except Exception as e:
            logger.error(f"Error en LLM summary: {e}")
            import traceback
            traceback.print_exc()
            return self._simple_summary(emails)

    def _simple_summary(self, emails: List[Dict]) -> str:
        if not emails:
            return "No hay correos recientes."
        lines = [f"{len(emails)} correo(s) encontrado(s):"]
        for e in emails[:5]:
            sender = e.get('from', '?')
            subject = e.get('subject', 'Sin asunto')
            lines.append(f"  - {sender}: {subject}")
        return "\n".join(lines)

    def get_summary(self) -> Dict[str, Any]:
        cache = self._load_cache()
        emails = []

        try:
            if hasattr(self.core, 'gmail') and self.core.gmail and self.core.gmail.is_connected():
                emails = self.core.gmail.get_recent_emails(max_results=10)
        except Exception as ex:
            logger.error(f"Error getting Gmail: {ex}")

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

        # Store first actionable URL for "open email" flow
        if self.core and emails:
            self.core.pending_email_url = emails[0].get("url", None)
        elif self.core:
            self.core.pending_email_url = None

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
        return f"Ultima revision: {last} | {count} correos procesados"