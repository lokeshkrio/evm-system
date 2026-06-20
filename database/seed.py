import json
from pathlib import Path

from pydantic import BaseModel, ValidationError, Field

from database.connection import DBConnection


BASE_DIR = Path(__file__).resolve().parent.parent

PATHS = {
    "candidate": BASE_DIR / "data" / "candidates.json",
    "voter": BASE_DIR / "data" / "voters.json",
}


class Candidate(BaseModel):
    candidate_id: int = Field(validation_alias="id")
    name: str
    party: str


class Voter(BaseModel):
    voter_id: str
    name: str
    age: int


class DataSeeder:

    @staticmethod
    async def seed(
        db: DBConnection,
        candidate_data: Path = PATHS["candidate"],
        voters_data: Path = PATHS["voter"],
    ) -> None:

        assert db.connection is not None

        if not candidate_data.exists():
            raise FileNotFoundError(f"Candidate file not found: {candidate_data}")

        if not voters_data.exists():
            raise FileNotFoundError(f"Voter file not found: {voters_data}")

        # Check whether data already exists
        cursor = await db.connection.execute("SELECT COUNT(*) FROM candidates")
        candidate_count = (await cursor.fetchone())[0]

        cursor = await db.connection.execute("SELECT COUNT(*) FROM voters")
        voter_count = (await cursor.fetchone())[0]

        if candidate_count > 0 or voter_count > 0:
            print("Data already seeded.")
            return

        # ---------- Candidates ----------
        raw_candidates = json.loads(candidate_data.read_text(encoding="utf-8"))

        candidates = []

        for item in raw_candidates:
            try:
                candidates.append(Candidate.model_validate(item))
            except ValidationError as e:
                print(f"Invalid candidate:\n{e}")

        await db.connection.executemany(
            """
            INSERT INTO candidates(
                candidate_id,
                name,
                party
            )
            VALUES (?, ?, ?)
            """,
            [(c.candidate_id, c.name, c.party) for c in candidates],
        )

        # ---------- Voters ----------
        raw_voters = json.loads(voters_data.read_text(encoding="utf-8"))

        voters = []

        for item in raw_voters:
            try:
                voters.append(Voter.model_validate(item))
            except ValidationError as e:
                print(f"Invalid voter:\n{e}")

        await db.connection.executemany(
            """
            INSERT INTO voters(
                voter_id,
                name,
                age
            )
            VALUES (?, ?, ?)
            """,
            [(v.voter_id, v.name, v.age) for v in voters],
        )

        await db.connection.commit()

        print(f"Imported {len(candidates)} candidates and " f"{len(voters)} voters.")

