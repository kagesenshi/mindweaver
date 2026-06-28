# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import logging
from datetime import timedelta
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from mindweaver.celery_app import app
from mindweaver.config import logger
from mindweaver.fw.model import get_engine, ts_now
from mindweaver.service.name_tracker.model import NameTracker
from mindweaver.platform_service.base import PlatformBase
from .base import run_async

# Ensure all platform models are loaded for subclasses scanning
import mindweaver.platform_service.pgsql.model
import mindweaver.platform_service.hive_metastore.model
import mindweaver.platform_service.trino.model
import mindweaver.platform_service.superset.model
import mindweaver.platform_service.airflow.model
import mindweaver.platform_service.kafka.model


async def scan_and_clean_names():
    """
    Scans all platform service models, populates NameTracker with currently active names,
    and removes any tracker entries that haven't been seen for more than 7 days.
    """
    logger.info("Scanning platform models to populate NameTracker...")
    engine = get_engine()
    
    async with AsyncSession(engine) as session:
        # Find all subclasses of PlatformBase that are actual database tables
        platform_models = [
            cls for cls in PlatformBase.__subclasses__()
            if getattr(cls, "__table__", None) is not None
        ]

        current_time = ts_now()

        for model_cls in platform_models:
            logger.info(f"Scanning table: {model_cls.__tablename__}")
            stmt = select(model_cls.name)
            result = await session.exec(stmt)
            names = result.all()

            for name in names:
                stmt_tracker = select(NameTracker).where(NameTracker.name == name)
                tracker_result = await session.exec(stmt_tracker)
                tracker = tracker_result.first()

                if not tracker:
                    tracker = NameTracker(
                        name=name,
                        module=model_cls.__tablename__,
                        last_seen=current_time,
                    )
                    session.add(tracker)
                else:
                    tracker.last_seen = current_time
                    tracker.module = model_cls.__tablename__
                    session.add(tracker)

        # Commit name updates/insertions
        await session.commit()

        # Clean up entries last seen more than 7 days ago
        cutoff_time = current_time - timedelta(days=7)
        logger.info(f"Cleaning NameTracker entries older than 7 days (before {cutoff_time})...")
        
        stmt_cleanup = select(NameTracker).where(NameTracker.last_seen < cutoff_time)
        cleanup_result = await session.exec(stmt_cleanup)
        to_delete = cleanup_result.all()

        for item in to_delete:
            logger.info(f"Pruning expired NameTracker entry: {item.name}")
            await session.delete(item)

        await session.commit()
        logger.info("NameTracker scan and clean completed successfully.")


@app.task
def scan_and_clean_names_task():
    """
    Celery periodic task to run the name scanning and cleanup.
    """
    run_async(scan_and_clean_names())
