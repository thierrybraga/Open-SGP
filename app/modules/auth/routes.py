"""
Arquivo: app/modules/auth/routes.py

Responsabilidade:
Rotas REST para autenticação, emissão de JWT e registro básico de usuários.

Integrações:
- core.security
- core.dependencies
- modules.users.service
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...core.dependencies import get_db, get_current_user
from ...core.security import verify_password, create_access_token, blacklist_token, get_token_from_header
from ..users.models import User
from ..users.schemas import UserCreate, UserOut
from ..users.service import create_user
from .schemas import Token


router = APIRouter()

# Rate limiter for authentication endpoints
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserOut)
@limiter.limit("5/minute")  # Máximo 5 registros por minuto
def register(request: Request, data: UserCreate, db: Session = Depends(get_db)):
    """
    Registra novo usuário.

    Rate limit: 5 tentativas por minuto por IP.
    """
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    user = create_user(db, data)
    return UserOut(id=user.id, username=user.username, email=user.email, is_active=user.is_active, roles=[r.name for r in user.roles])


@router.post("/token", response_model=Token)
@limiter.limit("5/minute")  # Máximo 5 tentativas de login por minuto
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Autentica usuário e retorna JWT token.

    Rate limit: 5 tentativas por minuto por IP.
    Protege contra ataques de força bruta.
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = create_access_token(subject=user.username, claims={"roles": [r.name for r in user.roles]})
    return Token(access_token=token)


@router.post("/logout")
def logout(request: Request, current_user: User = Depends(get_current_user)):
    """
    Faz logout do usuário invalidando o token JWT.

    O token é adicionado à blacklist no Redis e não poderá
    mais ser usado para autenticação.

    Requer autenticação.
    """
    # Extrai token do header Authorization
    auth_header = request.headers.get("authorization", "")
    token = get_token_from_header(auth_header)

    if token:
        # Adiciona token à blacklist
        blacklist_token(token)

    return {"message": "Logout successful", "username": current_user.username}

