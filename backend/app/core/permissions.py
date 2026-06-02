"""
Role and permission structures for  backend.
TODO: Wire to DB role column once workspace roles migration runs (Week 2).
"""

from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"



# Frontend-ready role payload
def get_role_payload(role: str) -> dict:
    return {
        "role": role,
        "is_admin": role == Role.ADMIN,
        "can_write": role in (Role.ADMIN, Role.MEMBER),
        "can_delete": role == Role.ADMIN
    }