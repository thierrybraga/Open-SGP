"""
Arquivo: app/core/security.py

Responsabilidade:
Fornece utilitários de segurança: hashing de senha, geração e validação de JWT,
e verificação básica de RBAC via roles/permissions.

Integrações:
- core.config
- modules.users
- modules.roles
- modules.permissions
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

from .config import settings


pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(subject: str, claims: Optional[dict] = None) -> str:
    to_encode = {"sub": subject, "iat": datetime.now(timezone.utc)}
    if claims:
        to_encode.update(claims)
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


def rbac_allows(user_roles: list[str], required_permissions: list[str], role_permissions_map: dict[str, set[str]]) -> bool:
    user_perms: set[str] = set()
    for role in user_roles:
        user_perms.update(role_permissions_map.get(role, set()))
    return set(required_permissions).issubset(user_perms)


# ==========================================
# TOKEN BLACKLIST (LOGOUT)
# ==========================================

import redis
from typing import Optional


def get_redis_client():
    """Retorna cliente Redis para blacklist"""
    try:
        return redis.from_url(settings.redis_url, decode_responses=True)
    except Exception:
        return None


def blacklist_token(token: str, exp_seconds: Optional[int] = None):
    """
    Adiciona token à blacklist (usado no logout).

    Args:
        token: Token JWT a ser invalidado
        exp_seconds: Tempo de expiração (padrão: TTL do settings)
    """
    r = get_redis_client()
    if not r:
        return  # Se Redis não disponível, silently fail

    try:
        ttl = exp_seconds or settings.token_blacklist_ttl
        r.setex(f"blacklist:{token}", ttl, "1")
    except Exception:
        pass  # Fail silently


def is_token_blacklisted(token: str) -> bool:
    """
    Verifica se token está na blacklist.

    Returns:
        True se token está blacklisted, False caso contrário
    """
    r = get_redis_client()
    if not r:
        return False  # Se Redis não disponível, assume que não está blacklisted

    try:
        return r.exists(f"blacklist:{token}") > 0
    except Exception:
        return False  # Fail open


def get_token_from_header(authorization: str) -> Optional[str]:
    """
    Extrai token do header Authorization.

    Args:
        authorization: Header "Bearer <token>"

    Returns:
        Token ou None
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization.replace("Bearer ", "")
