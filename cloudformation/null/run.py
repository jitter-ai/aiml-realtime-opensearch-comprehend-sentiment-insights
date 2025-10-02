#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path
import time

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
        self.cmd_runner.run_command("podman rmi -f sam-python3.12", check=False)

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

    def start_container(self):
        print("🚀 Starting container...")
        if not self.cmd_runner.run_command("podman compose up --detach --build"):
            return False
        return self.wait_for_container()

    def connect_to_container(self):
        print("🚀 Connecting to container shell...")
        return self.cmd_runner.run_command("podman exec -it aos-sentiment-container /bin/bash")

    def run(self):
        try:
            self.cleanup_resources()
            
            if not self.start_container():
                print("Failed to start container")
                return False

            if not self.connect_to_container():
                print("Failed to connect to container")
                return False

            return True
        except Exception as e:
            print(f"Error during execution: {e}")
            self.cleanup_resources()
            return False

def main():
    manager = ContainerManager()
    success = manager.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

