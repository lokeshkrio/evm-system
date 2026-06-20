from repositories.base_repository import BaseRepository
from models.candidate import Candidate


class CandidateRepository(BaseRepository):
    """Repository handling database operations for the candidates table."""

    async def is_exists(self, candidate_id: int) -> bool:
        """Checks if a candidate exists in the database by their ID.

        Args:
            candidate_id: The ID of the candidate to check.

        Returns:
            True if the candidate exists, False otherwise.
        """
        cursor = await self.conn.execute(
            """
            SELECT 1
            FROM candidates
            WHERE candidate_id = ? AND active = 1
            """,
            (candidate_id,),
        )
        row = await cursor.fetchone()
        return row is not None

    async def get_candidate(self, candidate_id: int) -> Candidate | None:
        """Retrieves a specific candidate by their ID.

        Args:
            candidate_id: The unique candidate ID.

        Returns:
            A Candidate instance if found, or None.
        """
        cursor = await self.conn.execute(
            """
            SELECT candidate_id, name, party, active
            FROM candidates
            WHERE candidate_id = ?
            """,
            (candidate_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return Candidate(
            candidate_id=row["candidate_id"],
            name=row["name"],
            party=row["party"],
            active=bool(row["active"]),
        )

    async def get_all_candidates(self) -> list[Candidate]:
        """Retrieves all candidates registered in the system.

        Returns:
            A list of all Candidate instances.
        """
        cursor = await self.conn.execute(
            """
            SELECT candidate_id, name, party, active
            FROM candidates
            """
        )
        rows = await cursor.fetchall()
        return [
            Candidate(
                candidate_id=row["candidate_id"],
                name=row["name"],
                party=row["party"],
                active=bool(row["active"]),
            )
            for row in rows
        ]

    async def get_all(self) -> list[Candidate]:
        """Alias for get_all_candidates.

        Returns:
            A list of all Candidate instances.
        """
        return await self.get_all_candidates()

    async def add(self, data: Candidate) -> bool:
        """Inserts a new candidate into the database.

        Args:
            data: The Candidate instance to insert.

        Returns:
            True when the insert is queued in the current unit of work.
        """
        await self.conn.execute(
            """
            INSERT INTO candidates (candidate_id, name, party, active)
            VALUES (?, ?, ?, ?)
            """,
            (
                data.candidate_id,
                data.name,
                data.party,
                True if data.active else False,
            ),
        )
        return True
