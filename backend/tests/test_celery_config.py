# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.celery_app import app
from mindweaver.config import settings


def test_celery_beat_schedule_expires():
    """Verify that status polling tasks have expires configuration set correctly."""
    schedule = app.conf.beat_schedule

    # Verify poll-all-platforms-15s
    platform_task = schedule.get("poll-all-platforms-15s")
    assert platform_task is not None
    assert platform_task.get("options") is not None
    assert platform_task["options"].get("expires") == settings.status_polling_expiry

    # Verify poll-all-k8s-clusters-15s
    k8s_task = schedule.get("poll-all-k8s-clusters-15s")
    assert k8s_task is not None
    assert k8s_task.get("options") is not None
    assert k8s_task["options"].get("expires") == settings.status_polling_expiry
