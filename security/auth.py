from models.enums import Role
from config import settings
from database.connection import DBConnection
from repositories.terminal_repository import TerminalRepository


async def authorize(api_key: str | None, required_role: Role, db: DBConnection) -> bool:
    """Verifies that the provided API key has the required role using settings and DB."""
    if not api_key:
        return False
        
    if required_role == Role.ADMIN:
        return api_key == settings.admin_secret_key
        
    if required_role == Role.TERMINAL:
        repo = TerminalRepository(db)
        terminal = await repo.get_by_secret(api_key)
        if terminal and terminal.get("active"):
            return True
            
    return False
