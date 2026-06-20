import asyncio
import sys
import questionary
from prompt_toolkit.styles import Style
from clients.terminal.terminal_client import TerminalClient

# Custom color theme matching modern JS frameworks (Vite/NextJS style)
custom_style = Style(
    [
        ("qmark", "fg:#61afef bold"),  # Question mark icon color
        ("question", "bold fg:#ffffff"),  # The question text
        ("answer", "fg:#98c379 bold"),  # Submitted answer text
        ("pointer", "fg:#e5c07b bold"),  # Arrow pointer (>)
        ("highlighted", "fg:#61afef bold"),  # Currently hovered option
        ("selected", "fg:#98c379"),  # Selected item
        ("instruction", "fg:#5c6370 italic"),  # Help text (like "Use arrow keys")
    ]
)


async def main():
    print("\n" + "=" * 45)
    print(" 🗳️  EVM VOTING TERMINAL INTUITIVE INTERFACE ")
    print("=" * 45 + "\n")

    # Interactive prompt for Terminal ID
    terminal_id = await questionary.text(
        "Enter unique Terminal ID (e.g., Terminal_01):", style=custom_style
    ).ask_async()

    if not terminal_id or not terminal_id.strip():
        print("❌ Error: Terminal ID cannot be empty.")
        sys.exit(1)

    client = TerminalClient(terminal_id=terminal_id.strip())

    try:
        print(f"📡 Connecting to EVM Core Server as '{terminal_id}'...")
        await client.connect()
        print("✅ Connection authorized successfully.\n")
    except Exception as e:
        print(f"❌ Connection Failed: Server is unreachable. Details: {e}")
        return

    while True:
        # Beautiful Select menu with arrow-key navigation and Enter execution
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

        try:
            if "Cast a Ballot" in choice:
                voter_id = await questionary.text(
                    "Enter Voter ID:", style=custom_style
                ).ask_async()

                if not voter_id or not voter_id.strip():
                    print("⚠️  Error: Voter ID cannot be blank.")
                    continue

                candidate_raw = await questionary.text(
                    "Enter Candidate ID (integer):",
                    style=custom_style,
                    validate=lambda text: text.isdigit()
                    or "Candidate ID must be a number!",
                ).ask_async()

                candidate_id = int(candidate_raw)

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
