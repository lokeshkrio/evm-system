import urllib.parse
from clients.base.base_client import BaseClient


class AdminClient(BaseClient):
    def __init__(
        self, admin_id: str = "Admin_Console", base_uri: str = "ws://localhost:8765"
    ):
        encoded_id = urllib.parse.quote(admin_id)
        full_uri = f"{base_uri}/?id={encoded_id}"
        super().__init__(uri=full_uri)

    async def start_election(self) -> dict:
        """Sends an RPC command to change state to ELECTION_STARTED."""
        return await self.send_request("start_election", {})

    async def stop_election(self) -> dict:
        """Sends an RPC command to finalize and freeze the election state."""
        return await self.send_request("stop_election", {})

    async def get_results(self) -> dict:
        """Fetches the aggregated vote tallies from the repository layer."""
        return await self.send_request("get_results", {})

    async def get_status(self) -> dict:
        """Checks the current active system state."""
        return await self.send_request("get_status", {})

    async def handle_notification(self, notification: dict) -> None:
        """Optional: Listen for live voting events on the admin console."""
        method = notification.get("method")
        if method == "vote_cast":
            print(
                "\n📥 [LIVE AUDIT]: A terminal just successfully processed a ballot.\nChoice > ",
                end="",
                flush=True,
            )
