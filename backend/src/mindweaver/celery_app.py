# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from celery import Celery
from mindweaver.config import settings

app = Celery(
    "mindweaver",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["mindweaver.tasks.platform_status"],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.timezone,
    enable_utc=True,
    beat_schedule={
        "poll-all-platforms-15s": {
            "task": "mindweaver.tasks.platform_status.poll_all_platforms",
            "schedule": 15.0,
        },
    },
)

if __name__ == "__main__":
    app.start()
