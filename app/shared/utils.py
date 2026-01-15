"""
Arquivo: app/shared/utils.py

Responsabilidade:
Utilidades genéricas de paginação e normalização de entrada.

Integrações:
- modules.* services
"""

from typing import Sequence, Any


def paginate(items: Sequence[Any], offset: int = 0, limit: int = 50):
    total = len(items)
    end = offset + limit
    return {"total": total, "items": list(items[offset:end])}

