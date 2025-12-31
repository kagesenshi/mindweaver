---
trigger: always_on
glob:
description:
---

This project uses following stack:
- flutter (for frontend)
- fastapi (for backend)
- python environment is managed using uv
- this project interacts with kubernetes for service deployment

command to start backend: `uv run mindweaver run --port 8000` in `backend` folder

command to start frontend: `flutter run -d chrome` in `frontend` folder

remember to run `uv run pytest tests` in `backend` after modifying `backend`. You do not have to run this test if you only modifying `frontend`

