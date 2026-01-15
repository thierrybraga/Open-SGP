"""
Arquivo: app/modules/technician_app/__init__.py

Responsabilidade:
Inicializa o módulo App do Técnico.

Integrações:
- core.database
- shared.models
- modules.users
- modules.service_orders
- modules.stock
"""

__version__ = "0.1.0"
__all__ = [
    "models",
    "schemas",
    "service",
    "routes",
]

