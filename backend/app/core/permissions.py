"""
    Role and permission structures for backend.
    Action-to-permission matrix and workspace authorization.
"""

from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class EnterprisePermission(str, Enum):
    # Residency
    RESIDENCY_READ = "enterprise.residency.read"
    RESIDENCY_MANAGE = "enterprise.residency.manage"

    # Branding
    BRANDING_READ = "enterprise.branding.read"
    BRANDING_MANAGE = "enterprise.branding.manage"
    BRANDING_PUBLISH = "enterprise.branding.publish"

    # Reporting
    REPORT_GENERATE = "enterprise.report.generate"
    REPORT_ACCESS = "authorized.report.access"


ROLE_PERMISSIONS: dict[str, set[EnterprisePermission]] = {
    "admin": {
        EnterprisePermission.RESIDENCY_READ,
        EnterprisePermission.RESIDENCY_MANAGE,
        EnterprisePermission.BRANDING_READ,
        EnterprisePermission.BRANDING_MANAGE,
        EnterprisePermission.BRANDING_PUBLISH,
        EnterprisePermission.REPORT_GENERATE,
        EnterprisePermission.REPORT_ACCESS,
    },
    "owner": {
        EnterprisePermission.RESIDENCY_READ,
        EnterprisePermission.RESIDENCY_MANAGE,
        EnterprisePermission.BRANDING_READ,
        EnterprisePermission.BRANDING_MANAGE,
        EnterprisePermission.BRANDING_PUBLISH,
        EnterprisePermission.REPORT_GENERATE,
        EnterprisePermission.REPORT_ACCESS,
    },
    "member": {
        EnterprisePermission.RESIDENCY_READ,
        EnterprisePermission.BRANDING_READ,
        EnterprisePermission.BRANDING_MANAGE,
        EnterprisePermission.REPORT_GENERATE,
        EnterprisePermission.REPORT_ACCESS,
    },
    "viewer": {
        EnterprisePermission.RESIDENCY_READ,
        EnterprisePermission.BRANDING_READ,
        EnterprisePermission.REPORT_ACCESS,
    },
}


def get_role_payload(role: str) -> dict:
    """Frontend-ready role payload with permission capabilities."""
    try:
        role_enum = Role(role.lower())
    except ValueError:
        role_enum = Role.VIEWER

    perms = [p.value for p in ROLE_PERMISSIONS.get(role_enum, set())]

    return {
        "role": role_enum.value,
        "is_admin": role_enum == Role.ADMIN,
        "can_write": role_enum in (Role.ADMIN, Role.MEMBER),
        "can_delete": role_enum == Role.ADMIN,
        "can_publish": role_enum == Role.ADMIN,
        "permissions": perms,
    }