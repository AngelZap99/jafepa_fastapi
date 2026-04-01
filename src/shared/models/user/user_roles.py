from enum import Enum


class UserRole(str, Enum):
    ADMINISTRADOR = "Administrador"
    VENDEDOR = "Vendedor"
    ALMACENISTA = "Almacenista"
    MIXTO = "Mixto"


DEFAULT_USER_ROLE = UserRole.VENDEDOR
DEFAULT_ADMIN_ROLE = UserRole.ADMINISTRADOR
