import asyncio
import logging
import questionary
import sys
from clients.admin.admin_client import AdminClient

# Setup basic logging config
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def main():
    # Style customizations for a modern look
    custom_style = questionary.Style(
        [
            ("qmark", "fg:#ff5555 bold"),
            ("question", "bold fg:#ffffff"),
            ("answer", "fg:#50fa7b bold"),
            ("pointer", "fg:#f1fa8c bold"),
            ("highlighted", "fg:#282a36 bg:#f1fa8c bold"),
            ("selected", "fg:#50fa7b"),
        ]
    )

    print("\n" + "=" * 50)
    print("          ROOT SECURITY ADMINISTRATION")
    print("=" * 50 + "\n")

    api_key = await questionary.password(
        "Enter Admin Authentication Token:", style=custom_style
    ).ask_async()

    if not api_key:
        print("Operation aborted.")
        sys.exit(1)

    client = AdminClient(api_key=api_key)

    try:
        print("Connecting to secure central backend cluster...")
        await client.connect()
        print("Connection authorized.")
    except Exception as e:
        print(f"Deployment Error: Configuration target unreachable. Details: {e}")
        return

    while True:
        print("\n" + "-" * 50)
        
        choice = await questionary.select(
            "Execute Directive:",
            choices=[
                "1. Initialize & Start Election Cycle",
                "2. Allow Single Terminal to Cast Vote",
                "3. Halt Active Election (Pause)",
                "4. Resume Halted Election",
                "5. Stop & Close Active Election",
                "6. Check System Metrics & Terminals",
                "7. Query Cryptographic Tally Results",
                "8. Check Engine Core State",
                "9. Terminate Admin Session",
            ],
            style=custom_style,
        ).ask_async()

        if choice is None:
            break

        try:
            if "1." in choice:
                print("\nDispatching signed 'start_election' signal...")
                response = await client.start_election()
                print(f"Execution Receipt:\n{response}")

            elif "2." in choice:
                print("\nDispatching 'enable_vote' signal for next terminal...")
                response = await client.enable_vote()
                print(f"Execution Receipt:\n{response}")

            elif "3." in choice:
                print("\nDispatching 'halt_election' signal...")
                response = await client.halt_election()
                print(f"Execution Receipt:\n{response}")

            elif "4." in choice:
                print("\nDispatching 'resume_election' signal...")
                response = await client.resume_election()
                print(f"Execution Receipt:\n{response}")

            elif "5." in choice:
                confirm = await questionary.confirm(
                    "CRITICAL: Stop election permanently?",
                    default=False,
                    style=custom_style,
                ).ask_async()

                if not confirm:
                    print("Operation aborted.")
                    continue

                print("\nDispatching signed 'stop_election' signal...")
                response = await client.stop_election()
                print(f"Execution Receipt:\n{response}")

            elif "6." in choice:
                print("\nFetching system metrics...")
                response = await client.get_metrics()
                print(f"System Metrics:\n{response}")

            elif "7." in choice:
                print("\nRequesting system audit results...")
                response = await client.get_results()
                print(f"Tally Verification Data:\n{response}")

            elif "8." in choice:
                print("\nChecking active system state...")
                response = await client.get_status()
                print(f"System State Registry Details:\n{response}")

            elif "9." in choice:
                print("Logging out safely from security session...")
                break

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
