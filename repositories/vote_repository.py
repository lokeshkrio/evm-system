from models.vote import Vote
from repositories.base_repository import BaseRepository


class VoteRepository(BaseRepository):
    """Repository handling database operations for recording and counting votes."""

    @property
    async def total_votes(self) -> int:
        """Retrieves the total number of votes cast.

        Note:
            This is an asynchronous property. To access it, you must use
            `await repository.total_votes`.

        Returns:
            The total vote count as an integer.
        """
        cursor = await self.conn.execute(
            """
            SELECT COUNT(*) as total
            FROM votes
            """
        )
        row = await cursor.fetchone()
        return row["total"]

    async def has_voted(self, voter_hash: str) -> bool:
        """Checks if a voter (identified by their hash) has already voted.

        Args:
            voter_hash: Cryptographic hash of the voter's ID.

        Returns:
            True if they have already voted, False otherwise.
        """
        cursor = await self.conn.execute(
            """
            SELECT 1
            FROM votes
            WHERE voter_hash = ?
            """,
            (voter_hash,),
        )
        row = await cursor.fetchone()
        return row is not None

    async def record_vote(self, vote: Vote, *, commit: bool = True) -> None:
        """Saves a cast vote to the database.

        Args:
            vote: The Vote dataclass containing the voter hash, candidate ID, and timestamp.
        """
        await self.conn.execute(
            """
            INSERT INTO votes(
                voter_hash,
                candidate_id,
                timestamp
            )
            VALUES (?, ?, ?)
            """,
            (vote.voter_hash, vote.candidate_id, vote.timestamp),
        )
        if commit:
            await self.conn.commit()

    async def get_results(self) -> dict[int, int]:
        """Calculates and returns the aggregated vote count per candidate.

        Returns:
            A dictionary mapping candidate IDs to their respective vote counts.
        """
        cursor = await self.conn.execute(
            """
            SELECT candidate_id,
            COUNT(*) as total
            FROM votes
            GROUP BY candidate_id
            """
        )
        rows = await cursor.fetchall()
        return {row["candidate_id"]: row["total"] for row in rows}
