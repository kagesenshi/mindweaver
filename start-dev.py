import subprocess
from pathlib import Path

here = Path(__file__).parent

fe = subprocess.Popen(
    ["uv", "run", "--package", "mindweaver_fe", "reflex", "run"], cwd=here / "frontend"
)
be = subprocess.Popen(
    ["uv", "run", "--package", "mindweaver", "mindweaver", "run"], cwd=here / "backend"
)

for p in [be, fe]:
    p.wait()
