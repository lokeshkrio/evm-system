# cli.py
import subprocess
import sys
import typer

app = typer.Typer()


@app.command()
def server():
    print("Starting server")
    subprocess.run([sys.executable, "-m", "main"])
    print("Server stopped")


@app.command()
def client():
    print("Starting client")
    subprocess.run([sys.executable, "-m", "clients.terminal.terminal_cli"])
    print("Client stopped")


@app.command()
def admin():
    print("Starting admin")
    subprocess.run([sys.executable, "-m", "clients.admin.admin_cli"])
    print("Admin stopped")


@app.command()
def seed():
    print("Starting seeding")
    subprocess.run([sys.executable, "-m", "data.seed"])
    print("Seeding stopped")


app()
