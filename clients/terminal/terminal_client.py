import urllib.parse
from clients.base.base_client import BaseClient


from utils.hashing import hash_voter_id


class TerminalClient(BaseClient):
    def __init__(self, terminal_id: str, base_uri: str = "ws://localhost:8765", api_key: str | None = None):
        # Safely escape spacing inside IDs
        encoded_id = urllib.parse.quote(terminal_id)
        full_uri = f"{base_uri}/?id={encoded_id}"

        super().__init__(uri=full_uri, api_key=api_key)
        self.terminal_id = terminal_id

    async def cast_vote(self, voter_id: str, candidate_id: int) -> dict:
        """Sends an RPC request to cast a ballot."""
        voter_hash = hash_voter_id(voter_id)
        return await self.send_request(
            "cast_vote", {"voter_hash": voter_hash, "candidate_id": candidate_id}
        )

    async def get_status(self) -> dict:
        """Asks for the current server state."""
        return await self.send_request("get_status", {})

    async def handle_notification(self, notification: dict) -> None:
        """Overrides base behavior to print live engine alerts instantly on screen."""
        method = notification.get("method")
        if method == "election_started":
            print(
                "\n📢 [ALERT]: The election has officially STARTED! Voting terminals active."
            )
        elif method == "election_stopped":
            print("\n📢 [ALERT]: The election has STOPPED. Voting options disabled.")
