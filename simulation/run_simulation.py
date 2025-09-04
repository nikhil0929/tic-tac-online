#!/usr/bin/env python3
"""
Setup and run the Tic-Tac-Toe simulation

This script helps set up the environment and run the game simulation.
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import websockets
        import redis
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False


def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        # Requirements.txt is in the parent directory
        requirements_path = os.path.join(os.path.dirname(
            os.path.dirname(__file__)), "requirements.txt")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", requirements_path])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False


def check_server_running(base_url="http://localhost:8000"):
    """Check if the FastAPI server is running"""
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def check_redis_running():
    """Check if Redis is running"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        return True
    except Exception:
        return False


def main():
    """Main setup and execution function"""
    print("Tic-Tac-Toe Simulation Setup")
    print("=" * 40)

    # Check if we're in the right directory
    script_dir = os.path.dirname(__file__)
    if not Path(os.path.join(script_dir, "simulation.py")).exists():
        print("Error: simulation.py not found. Please ensure the simulation files are in the correct directory.")
        sys.exit(1)

    # Check dependencies
    if not check_dependencies():
        print("Installing missing dependencies...")
        if not install_dependencies():
            print("Failed to install dependencies. Please install manually:")
            print("pip install -r requirements.txt")
            sys.exit(1)

    print("✓ Dependencies installed")

    # Check Redis
    if not check_redis_running():
        print("✗ Redis is not running. Please start Redis server:")
        print("  - On macOS: brew services start redis")
        print("  - On Ubuntu: sudo systemctl start redis-server")
        print("  - On Windows: Start Redis from the installation directory")
        sys.exit(1)

    print("✓ Redis is running")

    # Check if FastAPI server is running
    if not check_server_running():
        print("✗ FastAPI server is not running. Please start the server:")
        print("  python server.py")
        print("  or")
        print("  uvicorn server:app --reload")
        sys.exit(1)

    print("✓ FastAPI server is running")

    # Optional: Clean database before simulation
    print("\nCleaning database before simulation...")
    try:
        cleanup_script = os.path.join(
            os.path.dirname(__file__), "cleanup_database.py")
        subprocess.run([sys.executable, cleanup_script], check=True)
    except subprocess.CalledProcessError:
        print("Note: Database cleanup failed, but continuing with simulation...")
    except FileNotFoundError:
        print("Note: cleanup_database.py not found, skipping cleanup...")

    # Run the simulation
    print("\nStarting simulation...")
    print("=" * 40)

    try:
        simulation_script = os.path.join(
            os.path.dirname(__file__), "simulation.py")
        subprocess.run([sys.executable, simulation_script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Simulation failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")

    print("\nSimulation completed!")


if __name__ == "__main__":
    main()
