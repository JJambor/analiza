from enum import Enum

class UserRole(Enum):
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    USER = "user",
    COORDINATOR = "coordinator"