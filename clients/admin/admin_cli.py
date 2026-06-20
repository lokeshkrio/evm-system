import asyncio
import logging
import questionary
from clients.admin.admin_client import AdminClient

# Setup basic logging config
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def main():
    print("=== EVM System Administration Console ===")
    client = AdminClient()

    try:
        print("Connecting to secure central backend cluster...")
        await client.connect()
        print("Connection authorized.")
    except Exception as e:
        print(f"Deployment Error: Configuration target unreachable. Details: {e}")
        return

    # Style customizations for a modern look
    custom_style = questionary.Style(
        [
            ("qmark", "fg:#ff5555 bold"),  # Question mark indicator
            ("question", "bold fg:#ffffff"),  # The question text
            ("answer", "fg:#50fa7b bold"),  # Selected items or answers
            ("pointer", "fg:#f1fa8c bold"),  # Arrow pointers
            ("highlighted", "fg:#282a36 bg:#f1fa8c bold"),  # Hovered element
            ("selected", "fg:#50fa7b"),  # Selected status
        ]
    )

    while True:
        print("\n" + "=" * 50)
        print("          ROOT SECURITY ADMINISTRATION")
        print("=" * 50)

        # Using questionary's async select option to build an interactive menu
        choice = await questionary.select(
            "Execute Directive:",
            choices=[
                "1. Initialize & Start Election Cycle",
                "2. Halt & Close Active Election",
                "3. Query Cryptographic Tally Results",
                "4. Check Engine Core State",
                "5. Terminate Admin Session",
            ],
            style=custom_style,
        ).ask_async()

        # If a keyboard interrupt or escape happens inside selection, choice becomes None
        if choice is None:
            break

        try:
            if "1." in choice:
                print("\nDispatching signed 'start_election' signal...")
                response = await client.start_election()
                print(f"Execution Receipt:\n{response}")

            elif "2." in choice:
                # Use interactive confirmation questionnaire
                confirm = await questionary.confirm(
                    "CRITICAL: Halt election permanently?",
                    default=False,
                    style=custom_style,
                ).ask_async()

                if not confirm:
                    print("Operation aborted.")
                    continue

                print("\nDispatching signed 'stop_election' signal...")
                response = await client.stop_election()
                print(f"Execution Receipt:\n{response}")

            elif "3." in choice:
                print("\nRequesting system audit results...")
                response = await client.get_results()
                print(f"Tally Verification Data:\n{response}")

            elif "4." in choice:
                print("\nChecking active system state...")
                response = await client.get_status()
                print(f"System State Registry Details:\n{response}")

            elif "5." in choice:
                print("Logging out safely from security session...")
                break

            # Pause momentarily so that live notification loops don't instantly wipe stdout
            await asyncio.sleep(0.5)

        except ConnectionError:
            print("\n[CRITICAL]: Disconnected from backend cluster.")
            break
        except Exception as err:
            print(f"\nPipeline Exception Intercepted: {err}")

    await client.close()
    print("Admin session context closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAdmin interface terminated via SIGINT context shift.")
