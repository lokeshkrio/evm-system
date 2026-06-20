from database.connection import DBConnection
import aiosqlite


class BaseRepository:
    """Base repository class providing database connection access to subclass repositories.

    Attributes:
        db: The active DBConnection management object.
    """

    def __init__(self, db: DBConnection) -> None:
        """Initializes the repository with a database connection manager.

        Args:
            db: The DBConnection instance to access the SQLite connection.
        """
        self.db = db

    @property
    def conn(self) -> aiosqlite.Connection:
        """Returns the active SQLite connection.

        Raises:
            RuntimeError: If the database connection is not established.
        """
        if not self.db.connection:
            raise RuntimeError("Database connection not established")
        assert self.db.connection is not None
        return self.db.connection