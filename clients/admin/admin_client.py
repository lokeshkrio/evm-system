import urllib.parse
from clients.base.base_client import BaseClient


class AdminClient(BaseClient):
    def __init__(
        self, admin_id: str = "Admin_Console", base_uri: str = "ws://localhost:8765", api_key: str | None = None
    ):
        encoded_id = urllib.parse.quote(admin_id)
        full_uri = f"{base_uri}/?id={encoded_id}"
        super().__init__(uri=full_uri, api_key=api_key)

    async def start_election(self) -> dict:
        """Sends an RPC command to change state to ELECTION_STARTED."""
        return await self.send_request("start_election", {})

    async def stop_election(self) -> dict:
        """Sends an RPC command to finalize and freeze the election state."""
        return await self.send_request("stop_election", {})

    async def enable_vote(self) -> dict:
        """Allows one terminal to submit a vote."""
        return await self.send_request("enable_vote", {})

    async def halt_election(self) -> dict:
        """Halts an election while a voting session is active."""
        return await self.send_request("halt_election", {})

    async def resume_election(self) -> dict:
        """Returns a halted election to its waiting state."""
        return await self.send_request("resume_election", {})

    async def get_results(self) -> dict:
        """Fetches the aggregated vote tallies from the repository layer."""
        return await self.send_request("get_results", {})

    async def get_status(self) -> dict:
        """Checks the current active system state."""
        return await self.send_request("get_status", {})

    async def get_metrics(self) -> dict:
        """Fetches the system metrics including active connections."""
        return await self.send_request("get_metrics", {})

    async def handle_notification(self, notification: dict) -> None:
        """Optional: Listen for live voting events on the admin console."""
        method = notification.get("method")
        if method == "vote_cast":
            print(
                "\n📥 [LIVE AUDIT]: A terminal just successfully processed a ballot.\nChoice > ",
                end="",
                flush=True,
            )
