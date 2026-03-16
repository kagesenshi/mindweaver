# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import argparse
from dataclasses import dataclass
from alembic.config import Config as AlembicConfig
from alembic.command import revision, upgrade, downgrade, history
from typing import Callable
from mindweaver.config import settings
from mindweaver.app import app
from sqlmodel import SQLModel, Session, select
import mindweaver.fw.model
from mindweaver.datasource_service import (
    DatabaseSource,
    WebSource,
    APISource,
    StreamingSource,
)
from mindweaver.crypto import generate_fernet_key, rotate_key, EncryptionError
import asyncio
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sqlalchemy as sa
import uvicorn
import subprocess
import sys
from pathlib import Path
from .config import logger


def _get_default_config_path() -> str:
    """
    Locate the default alembic.ini file.
    """
    # 1. Check current directory
    local_path = Path("alembic.ini")
    if local_path.exists():
        return str(local_path)

    # 2. Check relative to project installation
    # backend/src/mindweaver/cli.py -> backend/alembic.ini
    project_path = Path(__file__).parent.parent.parent / "alembic.ini"
    if project_path.exists():
        return str(project_path.resolve())

    return "alembic.ini"


class RunArgs(argparse.Namespace):
    port: int
    host: str


def handle_run(args: RunArgs):
    uvicorn.run(
        "mindweaver.app:app",
        reload=True,
        reload_delay=5,
        host=args.host,
        port=args.port,
    )


class MigrateArgs(argparse.Namespace):
    config: str


def handle_migrate(args: MigrateArgs):
    config = AlembicConfig(args.config)
    config.set_main_option("sqlalchemy.url", settings.db_uri)
    upgrade(config, revision="heads")
    logger.info("Update completed successfully.")


class DowngradeArgs(argparse.Namespace):
    config: str
    revision: str


def handle_downgrade(args: DowngradeArgs):
    config = AlembicConfig(args.config)
    config.set_main_option("sqlalchemy.url", settings.db_uri)
    downgrade(config, revision=args.revision)
    logger.info(f"Downgrade to {args.revision} completed successfully.")


class HistoryArgs(argparse.Namespace):
    config: str
    verbose: bool
    indicate_current: bool


def handle_history(args: HistoryArgs):
    config = AlembicConfig(args.config)
    config.set_main_option("sqlalchemy.url", settings.db_uri)
    history(config, verbose=args.verbose, indicate_current=args.indicate_current)


def handle_reset(args: argparse.Namespace):
    confirm = input("This will drop all tables in the database. Are you sure? (N/y) > ")
    if confirm.lower().strip() != "y":
        logger.info("Aborted")
    engine = sa.create_engine(settings.db_uri)
    with engine.connect() as conn:
        conn.execute(sa.text("drop schema public cascade"))
        conn.execute(sa.text("create schema public"))
        conn.commit()
    logger.info("Database have been emptied")


class RevisionArgs(argparse.Namespace):
    autogenerate: bool
    message: str
    config: str


def handle_revision(args: RevisionArgs):
    """
    Trigger Alembic to generate a new migration.
    """
    # Call Alembic to create a new migration
    config = AlembicConfig(args.config)
    config.set_main_option("sqlalchemy.url", settings.db_uri)
    revision(config, autogenerate=args.autogenerate, message=args.message)
    logger.info("Migration generated successfully.")


class CryptoGenerateKeyArgs(argparse.Namespace):
    pass


def handle_crypto_generate_key(args: CryptoGenerateKeyArgs):
    """
    Generate a new Fernet encryption key.
    """
    key = generate_fernet_key()
    print(f"MINDWEAVER_FERNET_KEY={key}")


class CryptoRotateKeyArgs(argparse.Namespace):
    old_key: str
    new_key: str


def handle_crypto_rotate_key(args: CryptoRotateKeyArgs):
    """
    Rotate encryption keys for all data sources.
    """
    if not args.old_key or not args.new_key:
        logger.error("Both --old-key and --new-key are required")
        return

    logger.info("Starting key rotation for all data sources...")

    # Create database engine and session
    engine = sa.create_engine(settings.db_uri)

    try:
        with Session(engine) as session:
            source_models = [DatabaseSource, WebSource, APISource, StreamingSource]
            rotated_count = 0
            total_count = 0

            for model_cls in source_models:
                statement = select(model_cls)
                sources = session.exec(statement).all()
                total_count += len(sources)

                for ds in sources:
                    try:
                        # 1. Rotate the main password field if it exists
                        if ds.password:
                            ds.password = rotate_key(
                                args.old_key, args.new_key, ds.password
                            )
                            session.add(ds)
                            rotated_count += 1
                            logger.info(
                                f"Rotated password for {model_cls.__name__}: {ds.name} (ID: {ds.id})"
                            )

                        # 2. Rotate passwords in parameters if they exist (legacy support)
                        if ds.parameters and "password" in ds.parameters:
                            encrypted_password = ds.parameters["password"]
                            if encrypted_password:
                                ds.parameters["password"] = rotate_key(
                                    args.old_key, args.new_key, encrypted_password
                                )
                                session.add(ds)
                                rotated_count += 1
                                logger.info(
                                    f"Rotated parameter password for {model_cls.__name__}: {ds.name} (ID: {ds.id})"
                                )
                    except EncryptionError as e:
                        logger.error(
                            f"Failed to rotate key for {model_cls.__name__} {ds.name} (ID: {ds.id}): {str(e)}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Unexpected error rotating key for {model_cls.__name__} {ds.name} (ID: {ds.id}): {str(e)}"
                        )

            # Commit all changes
            session.commit()
            logger.info(f"\nKey rotation completed successfully!")
            logger.info(
                f"Rotated {rotated_count} operations out of {total_count} source(s)."
            )
            logger.info(f"\nIMPORTANT: Update MINDWEAVER_FERNET_KEY to the new key.")

    except Exception as e:
        logger.error(f"Failed to rotate keys: {str(e)}")
    finally:
        engine.dispose()


def run_with_reloader(cmd, watch_dir: str = None):
    """
    Run a command and restart it when files in watch_dir change.
    """
    if watch_dir is None:
        watch_dir = str(Path(__file__).parent)

    class RestartHandler(FileSystemEventHandler):
        def __init__(self, callback):
            self.callback = callback
            self.last_restart = 0

        def on_modified(self, event):
            self._handle_event(event)

        def on_created(self, event):
            self._handle_event(event)

        def on_deleted(self, event):
            self._handle_event(event)

        def on_moved(self, event):
            self._handle_event(event)

        def _handle_event(self, event):
            if event.is_directory or not event.src_path.endswith(".py"):
                return
            current_time = time.time()
            if current_time - self.last_restart > 5:
                logger.info(f"File changed: {event.src_path}. Restarting...")
                self.callback()
                self.last_restart = current_time

    process = None

    def start_process():
        nonlocal process
        if process:
            process.terminate()
            process.wait()
        process = subprocess.Popen(cmd)

    start_process()

    event_handler = RestartHandler(start_process)
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
            if process.poll() is not None:
                # Process exited unexpectedly, restart it?
                # For now just wait
                pass
    except KeyboardInterrupt:
        observer.stop()
        if process:
            process.terminate()
    observer.join()


def handle_scheduler(args: argparse.Namespace):
    """
    Start the Celery scheduler (beat).
    If embedded_worker is True, also start a worker.
    """
    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "mindweaver.celery_app",
        "beat",
        "--loglevel=info",
    ]

    if settings.embedded_worker:
        logger.info("Starting embedded Celery worker...")
        # Start worker in background
        worker_cmd = [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "mindweaver.celery_app",
            "worker",
            "--loglevel=info",
            "--pool=solo",
        ]
        if args.reload:
            # If reloading, we might want to start the worker with its own reloader too?
            # Or just let the scheduler reloader handle both if they are in the same dir.
            # However, subprocess.Popen doesn't block.
            # For simplicity, if reload is on, we run the worker in a separate reloader process if EMBEDDED.
            # But the scheduler itself will be the main blocking process.
            subprocess.Popen([sys.executable, sys.argv[0], "worker", "--reload"])
        else:
            subprocess.Popen(worker_cmd)

    logger.info("Starting Celery scheduler...")
    if args.reload:
        run_with_reloader(cmd)
    else:
        subprocess.run(cmd)


def handle_worker(args: argparse.Namespace):
    """
    Start the Celery worker.
    """
    logger.info("Starting Celery worker...")
    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "mindweaver.celery_app",
        "worker",
        "--loglevel=info",
        "--pool=solo",
    ]
    if args.reload:
        run_with_reloader(cmd)
    else:
        subprocess.run(cmd)


def get_parser() -> argparse.ArgumentParser:
    """
    Construct argument parser
    """
    parser = argparse.ArgumentParser(
        description="Mindweaver CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    # run
    run_cmd = subparsers.add_parser("run", help="Run the application")
    run_cmd.add_argument("-p", "--port", dest="port", type=int, default=8000)
    run_cmd.add_argument("-b", "--bind", dest="host", type=str, default="127.0.0.1")
    run_cmd.set_defaults(handler=handle_run)

    # db
    db_cmd = subparsers.add_parser("db", help="Database operations")
    db_cmd.add_argument(
        "-f",
        "--config",
        dest="config",
        type=str,
        default=_get_default_config_path(),
        help="Path to alembic.ini configuration file",
    )
    db_cmd_subparser = db_cmd.add_subparsers(dest="db_command")

    # db migrate
    db_migrate_cmd = db_cmd_subparser.add_parser("migrate", help="Run DB migrations")
    db_migrate_cmd.set_defaults(handler=handle_migrate)

    # db downgrade
    db_downgrade_cmd = db_cmd_subparser.add_parser("downgrade", help="Run DB downgrades")
    db_downgrade_cmd.add_argument(
        "-r", "--revision", dest="revision", type=str, required=True, help="Revision to downgrade to (e.g. -1, base, or a revision ID)"
    )
    db_downgrade_cmd.set_defaults(handler=handle_downgrade)

    # db history
    db_history_cmd = db_cmd_subparser.add_parser("history", help="List database migrations")
    db_history_cmd.add_argument(
        "-v", "--verbose", action="store_true", help="Use more verbose output"
    )
    db_history_cmd.add_argument(
        "-c", "--current", dest="indicate_current", action="store_true", help="Indicate current revision"
    )
    db_history_cmd.set_defaults(handler=handle_history)

    # db create migration
    db_revision_cmd = db_cmd_subparser.add_parser(
        "revision", help="Generate DB migration"
    )
    db_revision_cmd.add_argument(
        "-m", "--message", dest="message", required=True, type=str
    )
    db_revision_cmd.add_argument(
        "-a", "--autogenerate", dest="autogenerate", action="store_true", default=False
    )
    db_revision_cmd.set_defaults(handler=handle_revision)

    # db reset
    if settings.enable_db_reset:
        db_reset_cmd = db_cmd_subparser.add_parser(
            "reset", help="Drop and reset database"
        )
        db_reset_cmd.set_defaults(handler=handle_reset)

    # crypto
    crypto_cmd = subparsers.add_parser("crypto", help="Cryptographic operations")
    crypto_cmd_subparser = crypto_cmd.add_subparsers(dest="crypto_command")

    # crypto generate-key
    crypto_generate_key_cmd = crypto_cmd_subparser.add_parser(
        "generate-key", help="Generate a new Fernet encryption key"
    )
    crypto_generate_key_cmd.set_defaults(handler=handle_crypto_generate_key)

    # crypto rotate-key
    crypto_rotate_key_cmd = crypto_cmd_subparser.add_parser(
        "rotate-key", help="Rotate encryption keys for all data sources"
    )
    crypto_rotate_key_cmd.add_argument(
        "--old-key",
        dest="old_key",
        required=True,
        type=str,
        help="Current encryption key",
    )
    crypto_rotate_key_cmd.add_argument(
        "--new-key", dest="new_key", required=True, type=str, help="New encryption key"
    )
    crypto_rotate_key_cmd.set_defaults(handler=handle_crypto_rotate_key)

    # scheduler
    scheduler_cmd = subparsers.add_parser("scheduler", help="Start Celery scheduler")
    scheduler_cmd.add_argument(
        "--reload", action="store_true", help="Auto-reload on code changes"
    )
    scheduler_cmd.set_defaults(handler=handle_scheduler)

    # worker
    worker_cmd = subparsers.add_parser("worker", help="Start Celery worker")
    worker_cmd.add_argument(
        "--reload", action="store_true", help="Auto-reload on code changes"
    )
    worker_cmd.set_defaults(handler=handle_worker)

    return parser


class MainArgs(argparse.Namespace):
    handler: Callable[[argparse.Namespace], None]


def main():
    parser = get_parser()
    args: MainArgs = parser.parse_args()
    if hasattr(args, "handler"):
        args.handler(args)
    else:
        parser.print_help()
