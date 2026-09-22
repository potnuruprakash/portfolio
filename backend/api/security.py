"""
Security utilities: rate limiting, audit logging, and DRF permission classes.
"""
import logging
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
from django.core.cache import cache
from rest_framework.permissions import BasePermission
from api.mongo import mongo_manager

logger = logging.getLogger('api.security')

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = 600  # 10 minutes in seconds


def get_client_ip(request) -> str:
    """Safely extract client IP address."""
    if not request:
        return "127.0.0.1"
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def check_login_rate_limit(request) -> Tuple[bool, int]:
    """
    Check if the client IP is currently rate-limited.
    Returns: (is_allowed: bool, remaining_lockout_seconds: int)
    """
    ip = get_client_ip(request)
    lockout_key = f"login_lockout_{ip}"
    remaining = cache.get(lockout_key)
    if remaining:
        return False, LOCKOUT_DURATION

    attempts_key = f"login_attempts_{ip}"
    attempts = cache.get(attempts_key, 0)
    if attempts >= MAX_FAILED_ATTEMPTS:
        cache.set(lockout_key, True, timeout=LOCKOUT_DURATION)
        return False, LOCKOUT_DURATION

    return True, 0


def record_failed_login(request):
    """Increment failed login attempts for the client IP."""
    ip = get_client_ip(request)
    attempts_key = f"login_attempts_{ip}"
    attempts = cache.get(attempts_key, 0) + 1
    cache.set(attempts_key, attempts, timeout=LOCKOUT_DURATION)

    if attempts >= MAX_FAILED_ATTEMPTS:
        lockout_key = f"login_lockout_{ip}"
        cache.set(lockout_key, True, timeout=LOCKOUT_DURATION)
        logger.warning(f"IP {ip} locked out after {attempts} failed login attempts.")


def reset_login_attempts(request):
    """Clear failed login counters upon successful authentication."""
    ip = get_client_ip(request)
    cache.delete(f"login_attempts_{ip}")
    cache.delete(f"login_lockout_{ip}")


def log_audit_event(
    action: str,
    collection_name: str,
    document_id: str,
    changes: Optional[Dict[str, Any]] = None,
    request=None,
    admin_user: Optional[str] = None
):
    """
    Record an administrative audit log event in MongoDB Atlas.
    Tracks CREATE, UPDATE, DELETE, LOGIN, LOGOUT, UPLOAD, PUBLISH, UNPUBLISH.
    Never records passwords, secrets, or keys.
    """
    try:
        user_str = admin_user
        if not user_str and request and hasattr(request, 'user') and request.user.is_authenticated:
            user_str = request.user.username
        if not user_str:
            user_str = "system"

        ip = get_client_ip(request)
        audit_doc = {
            "admin": user_str,
            "action": action,
            "collection": collection_name,
            "document_id": str(document_id),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ip_address": ip,
            "changes": changes or {},
        }
        mongo_manager.audit_logs.insert_one(audit_doc)
    except Exception as ex:
        logger.error(f"Failed to record audit log: {type(ex).__name__}")


class IsAdminUserSession(BasePermission):
    """
    DRF permission requiring an active, authenticated Django admin/staff session.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_staff or request.user.is_superuser)
        )
