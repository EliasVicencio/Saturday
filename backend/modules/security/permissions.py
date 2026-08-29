# security/permissions.py - Permisos por agente y capability
from typing import Dict, Set

# Definicion de permisos por capability
CAPABILITY_PERMISSIONS = {
    "general": {"chat", "memory_read"},
    "system": {"chat", "system_info", "memory_read", "memory_write"},
    "knowledge": {"chat", "memory_read", "memory_write", "web_read"},
    "ambient": {"chat", "camera", "privacy_control", "memory_read", "memory_write"},
    "memory_op": {"chat", "memory_read", "memory_write", "memory_delete"},
}

# Permisos que requieren confirmacion
REQUIRES_CONFIRM = {"memory_delete", "privacy_control", "system_command"}

class PermissionManager:
    def __init__(self):
        self._overrides: Dict[str, Set[str]] = {}

    def can(self, capability: str, permission: str) -> bool:
        perms = self._overrides.get(capability, CAPABILITY_PERMISSIONS.get(capability, set()))
        return permission in perms

    def grant(self, capability: str, permission: str):
        if capability not in self._overrides:
            self._overrides[capability] = set(CAPABILITY_PERMISSIONS.get(capability, set()))
        self._overrides[capability].add(permission)

    def revoke(self, capability: str, permission: str):
        if capability in self._overrides:
            self._overrides[capability].discard(permission)

    def needs_confirmation(self, capability: str, permission: str) -> bool:
        return permission in REQUIRES_CONFIRM

    def get_permissions(self, capability: str) -> Set[str]:
        return self._overrides.get(capability, CAPABILITY_PERMISSIONS.get(capability, set()))

    def list_all(self) -> Dict[str, list]:
        result = {}
        for cap in set(list(CAPABILITY_PERMISSIONS.keys()) + list(self._overrides.keys())):
            result[cap] = sorted(self.get_permissions(cap))
        return result
