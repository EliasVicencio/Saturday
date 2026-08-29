# modules/intent_engine.py
"""
IntentEngine - Interpretación de intenciones de texto/voz para Saturday.

Por qué existe este archivo:
Antes, `core.py` tenía una lista plana de tuplas (frase, intención) y hacía
`if frase in texto`. Eso obliga a escribir el comando casi exacto y cada
intención nueva se mezclaba con las demás en una sola lista gigante.

Este motor:
1. Agrupa cada intención con TODAS sus frases sinónimas ("noticias",
   "muéstrame las noticias", "quiero ver las noticias", etc.) en un solo lugar.
2. Si el texto no calza exacto, hace *fuzzy matching* (tolera errores de tipeo,
   acentos, orden de palabras parecido) en vez de fallar directo a "no entendí".
3. Extrae parámetros de forma declarativa (param_mode) en vez de código repetido.
4. Deja un "gancho" (`interpret_with_llm`) para más adelante reemplazar o
   complementar el matching con un modelo real (Claude, GPT, etc.) sin tener
   que tocar el resto de `core.py` -- la interfaz de salida (IntentMatch) no cambia.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Callable, Dict, List, Optional


def _normalize(text: str) -> str:
    """minúsculas + sin tildes, para comparar sin ruido de acentos."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


@dataclass
class IntentDefinition:
    name: str
    phrases: List[str]  # frases sinónimas que disparan esta intención
    # cómo extraer parámetros del texto una vez matcheada la intención:
    #   None      -> sin parámetros
    #   "text"    -> params['text'] = texto restante tras sacar la frase
    #   "name"    -> params['name'] = texto restante tras sacar la frase
    param_mode: Optional[str] = None
    priority: bool = False  # intenciones de alta prioridad (ej: whatsapp) se evalúan primero
    meta: Dict = field(default_factory=dict)  # datos extra libres (ej: {'navigate': 'news'})


@dataclass
class IntentMatch:
    intent: str
    matched_phrase: str
    confidence: float  # 0..1
    params: Dict
    meta: Dict


class IntentEngine:
    """
    Clasifica un texto contra un registro de intenciones.

    Uso:
        engine = IntentEngine()
        engine.register(IntentDefinition(name="clima", phrases=["clima", "temperatura", "cómo está el tiempo"], param_mode=None))
        match = engine.classify("oye, cómo está el tiempo hoy")
        # match.intent == "clima"
    """

    FUZZY_THRESHOLD = 0.72  # por debajo de esto, se considera "no reconocido"

    def __init__(self):
        self._intents: List[IntentDefinition] = []

    def register(self, definition: IntentDefinition):
        self._intents.append(definition)

    def register_many(self, definitions: List[IntentDefinition]):
        self._intents.extend(definitions)

    # ------------------------------------------------------------------

    def classify(self, text: str) -> Optional[IntentMatch]:
        norm_text = _normalize(text)
        if not norm_text:
            return None

        # 1) intenciones de alta prioridad primero (ej: comandos de WhatsApp)
        for group in (True, False):
            candidates = [i for i in self._intents if i.priority == group]
            best = self._best_match(norm_text, text, candidates)
            if best:
                return best
        return None

    def _best_match(self, norm_text: str, original_text: str,
                     candidates: List[IntentDefinition]) -> Optional[IntentMatch]:
        best_score = 0.0
        best_intent: Optional[IntentDefinition] = None
        best_phrase = ""

        for definition in candidates:
            for phrase in definition.phrases:
                norm_phrase = _normalize(phrase)

                # coincidencia exacta (substring) -> score alto, con bonus a frases más largas
                # (para que "buscar tarea" le gane a "tarea" si ambas matchean)
                if norm_phrase in norm_text:
                    score = 0.9 + min(len(norm_phrase) / 100, 0.1)
                else:
                    # fuzzy: tolera errores de tipeo / variaciones de orden
                    score = SequenceMatcher(None, norm_phrase, norm_text).ratio()

                if score > best_score:
                    best_score = score
                    best_intent = definition
                    best_phrase = phrase

        if best_intent is None or best_score < self.FUZZY_THRESHOLD:
            return None

        params = self._extract_params(best_intent, best_phrase, original_text)
        return IntentMatch(
            intent=best_intent.name,
            matched_phrase=best_phrase,
            confidence=round(best_score, 3),
            params=params,
            meta=best_intent.meta,
        )

    @staticmethod
    def _extract_params(definition: IntentDefinition, matched_phrase: str, original_text: str) -> Dict:
        if definition.param_mode is None:
            return {}
        # sacamos la frase matcheada del texto original (case-insensitive) y
        # devolvemos lo que queda como parámetro libre
        pattern = re.compile(re.escape(matched_phrase), re.IGNORECASE)
        remainder = pattern.sub("", original_text, count=1).strip(" ,:.-")
        key = "name" if definition.param_mode == "name" else "text"
        return {key: remainder}

    # ------------------------------------------------------------------
    # GANCHO PARA UN MODELO DE IA (opcional, futuro)
    # ------------------------------------------------------------------

    def interpret_with_llm(self, text: str, llm_call: Callable[[str], str]) -> Optional[IntentMatch]:
        """
        Punto de extensión: si en el futuro querés que un LLM interprete
        comandos ambiguos que el matching por sinónimos no cachea, este método
        muestra el contrato esperado. `llm_call` sería una función que recibe
        el texto del usuario + la lista de intenciones disponibles y devuelve
        el nombre de la intención elegida (como string). No se usa por defecto:
        hay que conectarlo a mano en core.py una vez que tengas una API key
        de un proveedor de IA configurada.
        """
        intent_names = [i.name for i in self._intents]
        prompt = (
            "Elegí la intención más probable para este mensaje de usuario, "
            f"respondé solo con el nombre exacto de la lista: {intent_names}.\n"
            f"Mensaje: {text}"
        )
        raw = llm_call(prompt).strip()
        if raw in intent_names:
            definition = next(i for i in self._intents if i.name == raw)
            params = self._extract_params(definition, "", text) if definition.param_mode else {}
            return IntentMatch(intent=raw, matched_phrase="(llm)", confidence=1.0, params=params, meta=definition.meta)
        return None


# ------------------------------------------------------------------
# REGISTRO POR DEFECTO DE INTENCIONES DE SATURDAY
# ------------------------------------------------------------------

def build_default_engine() -> IntentEngine:
    engine = IntentEngine()

    engine.register_many([
        # ---- Alta prioridad: comandos de WhatsApp ----
        IntentDefinition(
            name="enviar_whatsapp",
            phrases=["envía whatsapp", "enviar whatsapp", "envía wsp", "manda un whatsapp", "manda whatsapp"],
            param_mode="text",
            priority=True,
        ),
        IntentDefinition(
            name="enviar_voz_whatsapp",
            phrases=["envía voz whatsapp", "enviar voz whatsapp", "voz whatsapp", "manda audio por whatsapp"],
            param_mode="text",
            priority=True,
        ),

        # ---- Spotify / música ----
        IntentDefinition(name="abrir_spotify", phrases=["abrir spotify", "abre spotify"]),
        IntentDefinition(name="reproducir_musica", phrases=[
            "reproduce", "reproducir", "pon música", "pon musica", "toca", "toca música", "play", "dale play",
        ]),
        IntentDefinition(name="pausar_musica", phrases=["pausa", "pausar", "detén la música", "para la música"]),
        IntentDefinition(name="siguiente_cancion", phrases=["siguiente", "siguiente canción", "siguiente tema", "next"]),
        IntentDefinition(name="anterior_cancion", phrases=["anterior", "canción anterior", "tema anterior"]),
        IntentDefinition(name="cancion_actual", phrases=["canción actual", "qué suena", "qué música suena", "que suena"]),

        # ---- Tareas ----
        IntentDefinition(name="buscar_tarea", phrases=["buscar tarea", "busca la tarea"], param_mode="name"),
        IntentDefinition(name="crear_tarea", phrases=["crear tarea", "nueva tarea", "agrega una tarea", "agregar tarea"], param_mode="name"),
        IntentDefinition(name="completar_tarea", phrases=["completar tarea", "marcar tarea como hecha", "termina la tarea"], param_mode="name"),
        IntentDefinition(name="eliminar_tarea", phrases=["eliminar tarea", "borrar tarea", "quita la tarea"], param_mode="name"),
        IntentDefinition(name="tareas_hoy", phrases=["tareas hoy", "tareas de hoy", "qué tareas tengo hoy"]),
        IntentDefinition(name="tareas_completadas", phrases=["tareas completadas", "tareas terminadas"]),
        IntentDefinition(name="tareas", phrases=["tareas", "mis tareas", "ver tareas", "lista de tareas"]),

        # ---- Notas ----
        IntentDefinition(name="crear_nota", phrases=["nota", "crear nota", "toma nota", "anota esto"], param_mode="text"),
        IntentDefinition(name="ver_notas", phrases=["ver notas", "mis notas", "lista de notas"]),
        IntentDefinition(name="buscar_nota", phrases=["buscar nota", "busca la nota"], param_mode="text"),

        # ---- Recordatorios ----
        IntentDefinition(name="crear_recordatorio", phrases=[
            "recordatorio", "recuérdame", "crear recordatorio", "agrega un recordatorio",
        ], param_mode="text"),
        IntentDefinition(name="ver_recordatorios", phrases=["ver recordatorios", "mis recordatorios"]),
        IntentDefinition(name="recordatorios_hoy", phrases=["recordatorios hoy", "recordatorios de hoy"]),

        # ---- Calendario ----
        IntentDefinition(name="eventos", phrases=["eventos", "mis eventos", "ver eventos", "agenda"]),
        IntentDefinition(name="eventos_hoy", phrases=["eventos hoy", "eventos de hoy", "qué tengo hoy", "agenda de hoy"]),
        IntentDefinition(name="crear_evento", phrases=["crear evento", "agenda un evento", "agrega un evento"], param_mode="text"),

        # ---- Correo ----
        IntentDefinition(name="correos", phrases=["correos", "mis correos", "ver correos", "revisa mi correo"]),
        IntentDefinition(name="no_leidos", phrases=["no leídos", "correos no leídos", "correos sin leer"]),
        IntentDefinition(name="enviar_correo", phrases=["enviar correo", "manda un correo", "envía un email"], param_mode="text"),

        # ---- Utilidades ----
        IntentDefinition(name="hora", phrases=["hora", "qué hora es", "dime la hora"]),
        IntentDefinition(name="fecha", phrases=["fecha", "qué día es hoy", "dime la fecha"]),
        IntentDefinition(name="clima", phrases=["clima", "temperatura", "cómo está el tiempo", "va a llover"]),
        IntentDefinition(name="get_camera", phrases=["ver cámara", "cámara", "muéstrame la cámara"]),
        IntentDefinition(name="estadisticas", phrases=["estadísticas", "estadisticas", "mis estadísticas"]),
        IntentDefinition(name="system_info", phrases=["estado del sistema", "cómo está el sistema", "rendimiento del sistema"]),

        # ---- Noticias ----
        IntentDefinition(name="noticias", phrases=["noticias", "noticias de", "noticias del día", "qué está pasando"]),
        IntentDefinition(name="buscar_noticias", phrases=["buscar noticias", "buscar noticia", "busca noticias sobre"], param_mode="text"),
        IntentDefinition(name="noticias_resumen", phrases=["noticias resumen", "resumen noticias", "envíame las noticias"]),
        # Comando de NAVEGACIÓN al panel de Noticias del frontend (no busca info,
        # solo le indica al frontend que cambie de vista; ver meta={'navigate': 'news'})
        IntentDefinition(
            name="abrir_noticias",
            phrases=[
                "abrir noticias", "abre las noticias", "ver panel de noticias", "abre el panel de noticias",
                "muéstrame las noticias", "quiero ver las noticias", "ir a noticias", "sección de noticias",
                "panel de noticias", "ve a noticias", "llévame a noticias", "llévame a las noticias",
                "vamos a noticias", "abre noticias",
            ],
            meta={"navigate": "news"},
        ),

        # ---- Bóveda ----
        IntentDefinition(name="guardar_boveda", phrases=[
            "guardar en la bóveda", "guardar en boveda", "anota en la bóveda", "guarda esto en la bóveda",
        ], param_mode="text"),
        IntentDefinition(name="buscar_boveda", phrases=[
            "buscar en la bóveda", "buscar en boveda", "busca en la bóveda",
        ], param_mode="text"),
        IntentDefinition(name="estado_boveda", phrases=[
            "estado de la bóveda", "estado de la boveda", "cómo está la bóveda", "resumen de la bóveda",
        ]),

        # ---- Social ----
        IntentDefinition(name="saludo", phrases=["hola", "buenas", "qué tal", "hey saturday"]),
        IntentDefinition(name="ayuda", phrases=["ayuda", "qué puedes hacer", "qué sabes hacer", "comandos disponibles"]),
        
        # ---- Resumen diario ----
        IntentDefinition(name="resumen_dia", phrases=[
            "resumen del día", "resumen diario", "qué hice hoy", "resumen de hoy",
        ]),
        
        # ---- Status ----
        IntentDefinition(name="status", phrases=[
            "status", "estatus", "cómo estás", "cómo andas", "todo bien",
            "estado general", "chequeo general", "health check",
        ]),
    ])

    return engine