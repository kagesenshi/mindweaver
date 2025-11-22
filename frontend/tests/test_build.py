import subprocess
import pytest
import os


@pytest.mark.integration
def test_reflex_compile():
    """
    Test that 'reflex compile' runs without error.
    This ensures the app builds successfully.
    """
    # Ensure we are in the frontend directory where rxconfig.py is located
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Run 'reflex compile' command
    # We use 'uv run' to ensure it uses the correct environment if needed,
    # but since pytest is likely running in the env, direct 'reflex' might work too.
    # Using 'uv run reflex' to be safe and consistent with dev workflow.
    result = subprocess.run(
        ["uv", "run", "reflex", "compile"],
        cwd=frontend_dir,
        capture_output=True,
        text=True,
    )

    # Check for success return code
    assert (
        result.returncode == 0
    ), f"Reflex compile failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
