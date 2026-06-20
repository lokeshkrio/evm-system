from models.enums import Role


API_KEYS = {
    "admin-secret": Role.ADMIN,
    "terminal-secret": Role.TERMINAL,
}

def authorize(api_key: str | None, required_role: Role) -> bool:
    """Verifies that the provided API key has the required role."""
    if not api_key:
        return False
    return API_KEYS.get(api_key) == required_role
