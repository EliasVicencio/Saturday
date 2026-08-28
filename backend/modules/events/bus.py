# events/bus.py - Event bus central para Saturday
import time
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict

@dataclass
class Event:
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"
    timestamp: float = field(default_factory=time.time)
    def to_dict(self):
        d = asdict(self)
        d["timestamp"] = self.timestamp
        return d

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._history: List[Event] = []
        self._max_history = 200

    def subscribe(self, event_name: str, callback: Callable):
        self._subscribers[event_name].append(callback)

    def publish(self, event_name: str, data: Dict[str, Any] = None, source: str = "unknown"):
        event = Event(name=event_name, data=data or {}, source=source)
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        for cb in self._subscribers.get(event_name, []):
            try:
                cb(event)
            except Exception as e:
                print(f"[EventBus] Error: {e}")
        for cb in self._subscribers.get("*", []):
            try:
                cb(event)
            except Exception as e:
                print(f"[EventBus] Error wildcard: {e}")

    def recent(self, event_name: str = "", limit: int = 20) -> List[Event]:
        events = self._history
        if event_name:
            events = [e for e in events if e.name == event_name]
        return events[-limit:]

    def clear_history(self):
        self._history.clear()
