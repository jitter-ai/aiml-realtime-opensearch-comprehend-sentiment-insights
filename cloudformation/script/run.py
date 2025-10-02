#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path
import time
import questionary

class CommandRunner:
    @staticmethod
    def run_command(cmd, check=True):
        try:
            result = subprocess.run(cmd, check=check, text=True, shell=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
            return False

class ContainerManager:
    def __init__(self):
        os.chdir(Path(__file__).parent.absolute())
        self.cmd_runner = CommandRunner()

    def cleanup_resources(self):
        print("🧹 Cleaning up existing resources...")
        self.cmd_runner.run_command("podman compose down", check=False)
        self.cmd_runner.run_command("podman rmi -f aos-sentiment-cli:latest", check=False)

    def wait_for_container(self):
        print("⏳ Waiting for container to be ready...")
        max_attempts = 10
        for i in range(max_attempts):
            result = subprocess.run(
                "podman ps --format '{{.Names}} {{.Status}}' | grep aos-sentiment-container",
                shell=True,
                text=True,
                capture_output=True
            )
            if "Up" in result.stdout:
                print("✅ Container is ready")
                return True
            time.sleep(2)
        return False

    def start_container(self, rebuild=False, no_cache=False):
        print("🚀 Starting container...")
        if no_cache:
            cmd = "podman compose build --no-cache && podman compose up --detach"
        elif rebuild:
            cmd = "podman compose up --detach --build"
        else:
            cmd = "podman compose up --detach"
        if not self.cmd_runner.run_command(cmd):
            return False
        return self.wait_for_container()

    def connect_to_container(self):
        print("🔌 Connecting to container shell...")
        return self.cmd_runner.run_command("podman exec -it aos-sentiment-container /bin/bash")

    def show_menu(self):
        choices = [
            "Start container with rebuild",
            "Start container with rebuild (no cache)",
            "Start container without rebuild",
            "Exit"
        ]

        answer = questionary.select(
            "🔧 Container Management Menu",
            choices=choices,
            use_indicator=True,
            use_shortcuts=True
        ).ask()

        if answer == choices[0]:  # Start with rebuild
            self.cleanup_resources()
            if self.start_container(rebuild=True):
                return self.connect_to_container()
            return False

        elif answer == choices[1]:  # Start with rebuild (no cache)
            self.cleanup_resources()
            print("🔄 Building with no cache (this may take longer)...")
            if self.start_container(rebuild=False, no_cache=True):
                return self.connect_to_container()
            return False

        elif answer == choices[2]:  # Start without rebuild
            if self.start_container(rebuild=False):
                return self.connect_to_container()
            return False

        elif answer == choices[3]:  # Exit
            print("👋 Goodbye!")
            return True

        return False

    def run(self):
        try:
            return self.show_menu()
        except Exception as e:
            print(f"❌ Error during execution: {e}")
            self.cleanup_resources()
            return False

def main():
    manager = ContainerManager()
    success = manager.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()