# memory/summarizer.py - Resumir conversaciones en recuerdos
import re
from typing import Dict, List, Optional
from .store import MemoryStore

FACT_PATTERNS = [
    (r"me llamo\s+(.+?)(?:\.|,|\s+y\s+|\s+$)", "fact"),
    (r"soy\s+(.+?)(?:\.|,|\s+y\s+|\s+$)", "fact"),
    (r"tengo\s+(\d+)\s+anos", "fact"),
    (r"vivo en\s+(.+?)(?:\.|,|\s+y\s+|\s+$)", "fact"),
    (r"trabajo(?:o| en)?\s+(.+?)(?:\.|,|\s+y\s+|\s+$)", "fact"),
]

PREFERENCE_PATTERNS = [
    (r"me (?:gusta|encanta|prefiero)\s+(.+?)(?:\.|,|\s+y\s+|\s+$)", "preference"),
    (r"no me (?:gusta|encanta|soporto)\s+(.+?)(?:\.|,|\s+y\s+|\s+$)", "preference"),
]

DECISION_PATTERNS = [
    (r"(?:decidi|voy a|planeo|pienso|quiero)\s+(.+?)(?:\.|,|\s+y\s+|\s+$)", "decision"),
]

class MemorySummarizer:
    def __init__(self, store: MemoryStore):
        self._store = store

    def analyze_message(self, text, chat_id=None):
        detected = []
        text_lower = text.lower().strip()
        for pattern, mem_type in FACT_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                content = match.group(1).strip()
                if len(content) > 2:
                    detected.append({"mem_type": mem_type, "content": content, "source": "auto_extract", "confidence": 0.8, "tags": mem_type})
        for pattern, mem_type in PREFERENCE_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                content = match.group(1).strip()
                if len(content) > 2:
                    detected.append({"mem_type": mem_type, "content": content, "source": "auto_extract", "confidence": 0.7, "tags": "preferencia"})
        for pattern, mem_type in DECISION_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                content = match.group(1).strip()
                if len(content) > 2:
                    detected.append({"mem_type": mem_type, "content": content, "source": "auto_extract", "confidence": 0.6, "tags": "decision"})
        return detected

    def process_and_save(self, text, chat_id=None):
        detected = self.analyze_message(text, chat_id)
        saved_ids = []
        for d in detected:
            mid = self._store.save(mem_type=d["mem_type"], content=d["content"], source=d["source"], confidence=d["confidence"], chat_id=chat_id, tags=d["tags"])
            saved_ids.append(mid)
        return saved_ids
