from __future__ import annotations
from typing import Dict, Any, List


class InMemorySessionStore:
    def __init__(self):
        self._messages: Dict[str, List[Dict[str, Any]]] = {}

    def append(self, session_id: str, role: str, content: str):
        self._messages.setdefault(session_id, []).append({"role": role, "content": content})

    def get(self, session_id: str) -> List[Dict[str, Any]]:
        return self._messages.get(session_id, [])
