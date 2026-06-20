import asyncio
import sys
import json
from pathlib import Path
import questionary
from prompt_toolkit.styles import Style
from clients.terminal.terminal_client import TerminalClient

custom_style = Style(
    [
        ("qmark", "fg:#61afef bold"),
        ("question", "bold fg:#ffffff"),
        ("answer", "fg:#98c379 bold"),
        ("pointer", "fg:#e5c07b bold"),
        ("highlighted", "fg:#61afef bold"),
        ("selected", "fg:#98c379"),
        ("instruction", "fg:#5c6370 italic"),
    ]
)


async def main():
    print("\n" + "=" * 45)
    print(" 🗳️  EVM VOTING TERMINAL INTUITIVE INTERFACE ")
    print("=" * 45 + "\n")

    api_key = await questionary.password(
        "Enter Terminal Authentication Token:", style=custom_style
    ).ask_async()

    if not api_key:
        print("❌ Error: Authentication Token cannot be empty.")
        sys.exit(1)

    terminal_id = await questionary.text(
        "Enter unique Terminal ID (e.g., Terminal_01):", style=custom_style
    ).ask_async()

    if not terminal_id or not terminal_id.strip():
        print("❌ Error: Terminal ID cannot be empty.")
        sys.exit(1)

    client = TerminalClient(terminal_id=terminal_id.strip(), api_key=api_key)

    try:
        print(f"📡 Connecting to EVM Core Server as '{terminal_id}'...")
        await client.connect()
        print("✅ Connection authorized successfully.\n")
    except Exception as e:
        print(f"❌ Connection Failed: Server is unreachable. Details: {e}")
        return
        
    # Load candidates locally from JSON
    candidates_path = Path("data/candidates.json")
    if not candidates_path.exists():
        print(f"❌ Error: Could not find candidates file at {candidates_path}")
        return
        
    try:
        with open(candidates_path, "r", encoding="utf-8") as f:
            candidates = json.load(f)
    except Exception as e:
        print(f"❌ Error reading candidates: {e}")
        return

    candidate_choices = [f"{c['id']} - {c['name']} ({c['party']})" for c in candidates]

    while True:
        choice = await questionary.select(
            f"Active Session [{terminal_id}] — Choose a terminal action:",
            choices=[
                "1. Cast a Ballot",
                "2. Check Election Status",
                "3. Exit Terminal Application",
            ],
            style=custom_style,
            pointer="➔",
        ).ask_async()

        if choice is None:
            break

        try:
            if "Cast a Ballot" in choice:
                voter_id = await questionary.text(
                    "Enter Voter ID:", style=custom_style
                ).ask_async()

                if not voter_id or not voter_id.strip():
                    print("⚠️  Error: Voter ID cannot be blank.")
                    continue

                candidate_selection = await questionary.select(
                    "Select a Candidate:",
                    choices=candidate_choices,
                    style=custom_style
                ).ask_async()
                
                if candidate_selection is None:
                    continue
                    
                candidate_id = int(candidate_selection.split(" - ")[0])

                print("\n🔐 Submitting secure ballot transaction...")
                response = await client.cast_vote(voter_id.strip(), candidate_id)
                print(f"📥 Server Response: {response}\n")

            elif "Check Election Status" in choice:
                print("\n🔍 Fetching remote election engine system status...")
                response = await client.get_status()
                print(f"📊 Server Status Payload: {response}\n")

            elif "Exit" in choice:
                print("👋 Gracefully closing terminal interface context...")
                break

        except ConnectionError:
            print("\n🚨 [CRITICAL ERROR]: Connection to the server was lost.")
            break
        except Exception as err:
            print(f"\n💥 An error occurred while handling the request: {err}")

    await client.close()
    print("🔒 Terminal connection closed safely.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Terminal application forced to terminate by user request.")
