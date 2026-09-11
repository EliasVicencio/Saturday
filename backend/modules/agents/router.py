# agents/router.py - Orquestador central de agentes
import time
import uuid
from typing import Dict, Any, List, Optional
from .base import BaseAgent, AgentResult
from .checkpoint import CheckpointStore, Checkpoint
from .confirm import ConfirmationManager

# Importar capabilities
from .cap_general import GeneralAgent
from .cap_system import SystemAgent
from .cap_knowledge import KnowledgeAgent
from .cap_ambient import AmbientAgent
from .cap_memory_op import MemoryOpAgent


class AgentRouter:
    """
    Orquestador que recibe la intención del usuario, evalúa qué agente
    es el más adecuado, delega la ejecución y mantiene trazabilidad.
    """

    def __init__(self, core=None):
        self.core = core
        self.agents: List[BaseAgent] = [
            MemoryOpAgent(core),
            AmbientAgent(core),
            SystemAgent(core),
            KnowledgeAgent(core),
            GeneralAgent(core),  # Siempre último como fallback
        ]
        self.checkpoints = CheckpointStore()
        self.confirm_manager = ConfirmationManager()
        self._active_sessions: Dict[str, Dict] = {}

    def route(self, text: str, chat_id: int = None, session_id: str = "") -> Dict[str, Any]:
        """
        Evalúa el mensaje, elige el agente correcto, ejecuta y retorna.
        """
        start = time.time()
        checkpoint_id = str(uuid.uuid4())[:12]
        session_id = session_id or str(chat_id or "anonymous")

        # Override: Si hay un correo pendiente y el usuario dice afirmativo, ir a system
        text_lower = text.lower().strip()
        affirmative_words = ["si", "sí", "dale", "abre", "abrir", "claro", "por favor", "ok"]
        if self.core and hasattr(self.core, 'pending_email_url') and self.core.pending_email_url:
            if any(w == text_lower or text_lower.startswith(w) for w in affirmative_words):
                for agent in self.agents:
                    if agent.name == "system":
                        result = agent.process(text, chat_id=chat_id, context={
                            "session_id": session_id,
                            "scores": [(1.0, "system")],
                        })
                        rd = result.to_dict()
                        rd["checkpoint_id"] = checkpoint_id
                        rd["session_id"] = session_id
                        rd["duration_ms"] = (time.time() - start) * 1000
                        # Extract URL from tools_called for frontend
                        for tool in result.tools_called:
                            if tool.get("tool") == "open_email" and "url" in tool:
                                rd["navigate_url"] = tool["url"]
                        return rd

        # 1. Evaluar scores de cada agente
        scores = []
        for agent in self.agents:
            score = agent.can_handle(text)
            if score > 0:
                scores.append((score, agent))

        if not scores:
            # No debería pasar, pero fallback
            scores = [(0.0, self.agents[-1])]

        scores.sort(key=lambda x: x[0], reverse=True)
        best_score, best_agent = scores[0]

        # 2. Ejecutar el agente seleccionado
        try:
            result = best_agent.process(text, chat_id=chat_id, context={
                "session_id": session_id,
                "scores": [(s, a.name) for s, a in scores[:3]],
            })
        except Exception as e:
            result = AgentResult(
                response=f"Error procesando con agente {best_agent.name}: {str(e)}",
                agent=best_agent.name,
                duration_ms=(time.time() - start) * 1000,
            )

        # 3. Verificar si requiere confirmación
        if result.requires_confirmation:
            conf = self.confirm_manager.request_confirmation(
                result.confirmation_action, result.agent, result.confirmation_data
            )
            if conf:
                result.checkpoint_id = conf.id
                duration_ms = (time.time() - start) * 1000
                result.duration_ms = duration_ms

                # Guardar checkpoint
                self.checkpoints.save(Checkpoint(
                    id=checkpoint_id, session_id=session_id,
                    user_message=text, agent=result.agent,
                    tools_called=result.tools_called,
                    response=f"[CONFIRMATION REQUIRED] {result.response}",
                    duration_ms=duration_ms, success=True, error=None,
                    timestamp=time.time(),
                ))

                return {
                    "response": f" Requiere confirmación: {result.confirmation_action}\n{result.response}",
                    "agent": result.agent,
                    "requires_confirmation": True,
                    "confirmation_id": conf.id,
                    "confirmation_description": conf.description,
                    "confirmation_risk": conf.risk,
                    "tools_called": result.tools_called,
                    "duration_ms": result.duration_ms,
                    "checkpoint_id": checkpoint_id,
                    "routed_to": best_agent.name,
                    "route_score": best_score,
                    "alternatives": [(a.name, s) for s, a in scores[1:3]],
                }

        # 4. Guardar checkpoint
        duration_ms = (time.time() - start) * 1000
        result.duration_ms = duration_ms
        result.checkpoint_id = checkpoint_id

        self.checkpoints.save(Checkpoint(
            id=checkpoint_id, session_id=session_id,
            user_message=text, agent=result.agent,
            tools_called=result.tools_called,
            response=result.response[:2000],
            duration_ms=duration_ms, success=True, error=None,
            timestamp=time.time(),
        ))

        # 5. Registrar interaccion para aprendizaje de rutinas (no bloqueante)
        if self.core and getattr(self.core, "routines", None):
            try:
                self.core.routines.record_interaction(result.agent)
            except Exception:
                pass  # el aprendizaje de rutinas nunca debe romper una respuesta

        # 6. Publicar evento
        if self.core and self.core.event_bus:
            self.core.event_bus.publish("agent.executed", {
                "agent": result.agent,
                "tools": [t["tool"] for t in result.tools_called],
                "duration_ms": round(duration_ms, 2),
                "score": best_score,
            }, source="router")

        return {
            "response": result.response,
            "agent": result.agent,
            "requires_confirmation": False,
            "tools_called": result.tools_called,
            "duration_ms": result.duration_ms,
            "checkpoint_id": checkpoint_id,
            "routed_to": best_agent.name,
            "route_score": best_score,
            "alternatives": [(a.name, s) for s, a in scores[1:3]],
        }

    def execute_autonomous(self, capability: str, tool: str, args: Dict[str, Any] = None,
                            reason: str = "", risk: str = "low") -> Dict[str, Any]:
        """
        Punto de entrada único para acciones que Saturday inicia POR SÍ MISMO
        (scheduler, rutinas aprendidas, sugerencias proactivas) — sin un mensaje
        de texto del usuario de por medio.

        A diferencia de `route()`, aquí no hay NLP de por medio: el llamador ya
        sabe exactamente qué capability/tool quiere ejecutar. Pero pasa por las
        MISMAS reglas de permisos, confirmación y auditoría que cualquier acción
        pedida por chat, para que nada autónomo se salte el control del usuario.
        """
        args = args or {}
        start = time.time()
        checkpoint_id = str(uuid.uuid4())[:12]

        # 1. Permisos: ¿esta capability puede ejecutar este tipo de permiso?
        perm = self._infer_permission(tool)
        if self.core and self.core.permissions:
            if not self.core.permissions.can(capability, perm):
                self._log_autonomous(checkpoint_id, capability, tool, args,
                                      "denegado por permisos", False, start)
                return {"executed": False, "reason": "permission_denied",
                        "capability": capability, "tool": tool}

            # 2. ¿Requiere confirmación tuya antes de ejecutarse?
            if self.core.permissions.needs_confirmation(capability, perm) or risk == "high":
                conf = self.confirm_manager.request_confirmation(
                    action=tool, agent=capability,
                    data={"args": args, "reason": reason, "autonomous": True},
                )
                self._log_autonomous(checkpoint_id, capability, tool, args,
                                      f"esperando confirmación: {conf.id if conf else '?'}",
                                      True, start)
                return {"executed": False, "reason": "pending_confirmation",
                        "confirmation_id": conf.id if conf else None,
                        "capability": capability, "tool": tool}

        # 3. Ejecutar y dejar rastro (checkpoint + audit), igual que una acción manual
        try:
            result = self.core._execute_tool(tool, args) if self.core else None
            success = True
        except Exception as e:
            result = f"Error ejecutando {tool}: {e}"
            success = False

        duration_ms = (time.time() - start) * 1000
        self.checkpoints.save(Checkpoint(
            id=checkpoint_id, session_id="autonomous",
            user_message=f"[AUTÓNOMO] {reason or tool}", agent=capability,
            tools_called=[{"tool": tool, "args": args}],
            response=str(result)[:2000],
            duration_ms=duration_ms, success=success,
            error=None if success else str(result), timestamp=time.time(),
        ))
        if self.core and self.core.audit:
            self.core.audit.log("autonomous_action", agent=capability, action=reason,
                                 tool=tool, args=args, result=str(result),
                                 duration_ms=duration_ms, success=success)
        if self.core and self.core.event_bus:
            self.core.event_bus.publish("agent.autonomous", {
                "capability": capability, "tool": tool, "success": success,
            }, source="scheduler")

        return {"executed": True, "success": success, "result": result,
                "capability": capability, "tool": tool, "checkpoint_id": checkpoint_id}

    def _infer_permission(self, tool: str) -> str:
        """Mapeo simple tool -> tipo de permiso. Ajustar si se agregan tools nuevas."""
        destructive_hints = ("delete", "borrar", "eliminar", "send", "enviar")
        if any(h in tool.lower() for h in destructive_hints):
            return "memory_delete" if "delete" in tool.lower() or "borrar" in tool.lower() else "system_command"
        return "memory_write"

    def _log_autonomous(self, checkpoint_id, capability, tool, args, msg, success, start):
        duration_ms = (time.time() - start) * 1000
        if self.core and self.core.audit:
            self.core.audit.log("autonomous_action", agent=capability, action=msg,
                                 tool=tool, args=args, result=msg,
                                 duration_ms=duration_ms, success=success)

    def get_checkpoints(self, session_id: str = "", limit: int = 20) -> List[Dict]:
        return self.checkpoints.recent(session_id, limit)

    def get_stats(self) -> Dict[str, Any]:
        return self.checkpoints.stats()

    def get_pending_confirmations(self) -> list:
        return self.confirm_manager.get_pending()

    def confirm_action(self, confirmation_id: str) -> Optional[Dict]:
        conf = self.confirm_manager.confirm(confirmation_id)
        if conf:
            return {"action": conf.action, "agent": conf.agent, "args": conf.args}
        return None

    def cancel_action(self, confirmation_id: str) -> bool:
        return self.confirm_manager.cancel(confirmation_id)

    def list_agents(self) -> List[Dict]:
        return [
            {"name": a.name, "description": a.description, "tools": a.tools}
            for a in self.agents
        ]
