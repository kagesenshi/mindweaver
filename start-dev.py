import subprocess
import time
from pathlib import Path

here = Path(__file__).parent

fe = subprocess.Popen(
    ["uv", "run", "--package", "mindweaver_fe", "reflex", "run"], cwd=here / "frontend"
)
be = subprocess.Popen(
    ["uv", "run", "--package", "mindweaver", "mindweaver", "run"], cwd=here / "backend"
)

processes = {"frontend": fe, "backend": be}

try:
    # Monitor processes and terminate all if any one exits
    while True:
        for name, proc in processes.items():
            retcode = proc.poll()
            if retcode is not None:
                print(f"\n{name} process terminated with code {retcode}")
                print("Terminating all processes...")

                # Terminate all other processes
                for other_name, other_proc in processes.items():
                    if other_proc.poll() is None:  # Still running
                        print(f"Terminating {other_name}...")
                        other_proc.terminate()
                        try:
                            other_proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            print(f"Force killing {other_name}...")
                            other_proc.kill()

                exit(retcode)

        time.sleep(0.5)  # Check every 500ms

except KeyboardInterrupt:
    print("\nReceived interrupt, terminating all processes...")
    for name, proc in processes.items():
        if proc.poll() is None:
            print(f"Terminating {name}...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"Force killing {name}...")
                proc.kill()
    exit(0)
