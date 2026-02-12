import subprocess
import sys
from pathlib import Path
import os

def run_command(cmd, cwd=None, env=None):
    """Run a command and check for errors."""
    print(f"Running: {' '.join(cmd)} in {cwd or os.getcwd()}")
    result = subprocess.run(cmd, cwd=cwd, env=env)
    if result.returncode != 0:
        print(f"Error: Command failed with return code {result.returncode}")
        sys.exit(result.returncode)

def main():
    here = Path(__file__).parent
    backend_dir = here / "backend"
    frontend_dir = here / "frontend"

    print("--- Starting Mindweaver Development Environment Setup ---")

    # 1. Backend: uv sync
    print("\n[1/4] Installing backend dependencies (uv sync)...")
    run_command(["uv", "sync"], cwd=backend_dir)

    # 2. Frontend: npm install
    print("\n[2/4] Installing frontend dependencies (npm install)...")
    if frontend_dir.exists():
        run_command(["npm", "install"], cwd=frontend_dir)
    else:
        print("Warning: frontend directory not found, skipping npm install.")

    # 3. Backend: Database Migrations
    print("\n[3/4] Running database migrations...")
    run_command(["uv", "run", "mindweaver", "db", "migrate"], cwd=backend_dir)

    # 4. Backend: Encryption Key
    print("\n[4/4] Setting up encryption key...")
    env_file = backend_dir / ".env"
    has_key = False
    if env_file.exists():
        with open(env_file, "r") as f:
            if "MINDWEAVER_FERNET_KEY" in f.read():
                has_key = True
    
    if not has_key:
        print("MINDWEAVER_FERNET_KEY not found in .env, generating...")
        try:
            # Get key from CLI
            key_output = subprocess.check_output(
                ["uv", "run", "mindweaver", "crypto", "generate-key"], 
                cwd=backend_dir, 
                text=True
            ).strip()
            
            # Ensure .env exists or append to it
            mode = "a" if env_file.exists() else "w"
            with open(env_file, mode) as f:
                # Add newline if appending to non-empty file
                if mode == "a" and env_file.stat().st_size > 0:
                    f.write("\n")
                f.write(f"{key_output}\n")
            print(f"Successfully generated and added key to {env_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error generating key: {e}")
            sys.exit(1)
    else:
        print("MINDWEAVER_FERNET_KEY already exists in .env")

    print("\n--- Setup Complete! ---")
    print("You can now start the development stack with:")
    print("python start-dev.py")

if __name__ == "__main__":
    main()
