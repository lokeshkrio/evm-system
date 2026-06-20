import json
import aiosqlite
from pydantic import BaseModel, ValidationError
from pathlib import Path


paths = {
    "candidate": "./data/candidates.json",
    "voter": "./data/voters.json",
    "db": "./evm.db",
}


class Candidate(BaseModel):
    candidate_id: int
    name: str
    party: str


class Voter(BaseModel):
    voter_id: str
    name: str
    age: int


class CandidateSeeder:

    @staticmethod
    async def seed(
        db_path: str = paths["db"],
        candidate_data: str = paths["candidate"],
        voters_data: str = paths["voter"],
    ) -> None:
        async with aiosqlite.connect(db_path) as db:
            # Check whether candidates already exist
            cursor = await db.execute("SELECT COUNT(*) FROM candidates")
            count = (await cursor.fetchone())[0]

            if count > 0:
                print("candidates already loaded")

            candidate_path = Path(candidate_data)
            voters_path = Path(voters_data)

            if (not candidate_path.exists) | (not voters_path.exists):
                raise FileNotFoundError("Targets Files not Located")

            with open(candidate_path, "r", encoding="utf-8") as f:
                global raw_candidate_data
                raw_candidate_data = json.load(f)

            candidates = []

            for item in raw_candidate_data:
                try:
                    candidate = Candidate.model_validate(item)
                    candidates.append(candidate)

                except ValidationError as e:
                    print(f"Invalid candidate data:\n{e}")

            await db.executemany(
                """
                INSERT INTO candidates (
                    candidate_id,
                    name,
                    party
                )
                VALUES (?, ?, ?)
                """,
                [(c.candidate_id, c.name, c.party) for c in candidates],
            )

            with open(voters_path, "r", encoding="utf-8") as f:
                global raw_voters_data
                raw_voters_data = json.load(f)

            voters = []

            for item in raw_voters_data:
                try:
                    voter = Voter.validate(item)
                    voters.append(voter)
                except ValidationError as e:
                    print(f"Invalid candidate data:\n{e}")

            await db.executemany(
                """
                INSERT INTO voters(
                    voter_id,
                    name,
                    age
                )
                VALUES (?,?,?)
                """,
                [(v.voter_id, v.name, v.age) for v in voters],
            )

            await db.commit()

        print("DATA IMPORTED SUCCESSFULLY")
