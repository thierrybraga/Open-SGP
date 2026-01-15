"""
Arquivo: app/core/dependencies.py

Responsabilidade:
Define dependências do FastAPI: sessão de banco, autenticação pelo JWT e checagem
de permissões via RBAC com cache Redis.

Integrações:
- core.database
- core.security
- modules.users.models
- modules.roles.models
- modules.permissions.models
- Redis para cache de permissões
"""

import json
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import redis

from .database import SessionLocal
from .security import decode_token, is_token_blacklisted
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Cliente Redis para cache
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

# TTL do cache de permissões (5 minutos)
PERMISSIONS_CACHE_TTL = 300


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_permissions_cached(user_id: int, db: Session) -> set[str]:
    """
    Obtém permissões do usuário com cache Redis.

    Cache key: user:{user_id}:permissions
    TTL: 5 minutos

    Args:
        user_id: ID do usuário
        db: Sessão do banco de dados

    Returns:
        Set com códigos das permissões do usuário
    """
    cache_key = f"user:{user_id}:permissions"

    # Tenta obter do cache
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return set(json.loads(cached))
    except Exception:
        # Se Redis falhar, continua sem cache
        pass

    # Busca do banco de dados
    from ..modules.users.models import User
    from ..modules.roles.models import Role

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return set()

    # Coleta todas as permissões de todas as roles do usuário
    permissions = set()
    for role in user.roles:
        for permission in role.permissions:
            permissions.add(permission.code)

    # Salva no cache
    try:
        redis_client.setex(
            cache_key,
            PERMISSIONS_CACHE_TTL,
            json.dumps(list(permissions))
        )
    except Exception:
        # Se Redis falhar, continua sem cache
        pass

    return permissions


def get_role_permissions_cached(db: Session) -> dict[str, set[str]]:
    """
    Obtém mapeamento role -> permissões com cache Redis.

    Cache key: rbac:role_permissions
    TTL: 5 minutos

    Args:
        db: Sessão do banco de dados

    Returns:
        Dicionário {role_name: {permission_codes}}
    """
    cache_key = "rbac:role_permissions"

    # Tenta obter do cache
    try:
        cached = redis_client.get(cache_key)
        if cached:
            cached_dict = json.loads(cached)
            return {k: set(v) for k, v in cached_dict.items()}
    except Exception:
        pass

    # Busca do banco de dados
    from ..modules.roles.models import Role

    role_permissions_map = {}
    for role in db.query(Role).all():
        role_permissions_map[role.name] = {p.code for p in role.permissions}

    # Salva no cache
    try:
        # Converte sets para listas para JSON
        cacheable = {k: list(v) for k, v in role_permissions_map.items()}
        redis_client.setex(
            cache_key,
            PERMISSIONS_CACHE_TTL,
            json.dumps(cacheable)
        )
    except Exception:
        pass

    return role_permissions_map


def invalidate_user_permissions_cache(user_id: int):
    """
    Invalida cache de permissões de um usuário.

    Deve ser chamado quando:
    - Usuário muda de role
    - Role do usuário tem permissões alteradas
    - Usuário é deletado

    Args:
        user_id: ID do usuário
    """
    cache_key = f"user:{user_id}:permissions"
    try:
        redis_client.delete(cache_key)
    except Exception:
        pass


def invalidate_role_permissions_cache():
    """
    Invalida cache global de role -> permissões.

    Deve ser chamado quando:
    - Nova role é criada
    - Permissões de uma role são alteradas
    - Role é deletada
    """
    cache_key = "rbac:role_permissions"
    try:
        redis_client.delete(cache_key)
    except Exception:
        pass


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
):
    # Verifica se token está na blacklist (logout)
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked (user logged out)"
        )

    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    from ..modules.users.models import User  # local import

    user = db.query(User).filter(User.username == sub).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")
    return user


def require_permissions(*required: str):
    """
    Decorator para checar permissões RBAC com cache Redis.

    Uso:
        @router.get("/admin/users", dependencies=[Depends(require_permissions("users.view"))])

    Args:
        *required: Códigos de permissões necessárias

    Returns:
        FastAPI dependency function
    """
    def dependency(
        user=Depends(get_current_user),
        db: Annotated[Session, Depends(get_db)] = None,
    ):
        # Obtém permissões do usuário com cache
        user_permissions = get_user_permissions_cached(user.id, db)

        # Verifica se usuário tem todas as permissões necessárias
        required_set = set(required)
        if not required_set.issubset(user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {required_set - user_permissions}"
            )

        return True

    return dependency

