import argparse
from dataclasses import dataclass
from alembic.config import Config as AlembicConfig
from alembic.command import revision, upgrade
from typing import Callable
from mindweaver.config import settings
from mindweaver.app import app
from sqlmodel import SQLModel
import mindweaver.fw.model
import mindweaver.service.data_source
import asyncio
import sqlalchemy as sa
import uvicorn
from .config import logger


class RunArgs(argparse.Namespace):
    pass


def handle_run(args: RunArgs):
    uvicorn.run("mindweaver.app:app", reload=True, reload_delay=5, port=5000)


class MigrateArgs(argparse.Namespace):
    config: str


def handle_migrate(args: MigrateArgs):
    config = AlembicConfig(args.config)
    config.set_main_option("sqlalchemy.url", settings.db_uri)
    upgrade(config, revision="heads")
    logger.info("Update completed successfully.")


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


def get_parser() -> argparse.ArgumentParser:
    """
    Construct argument parser
    """
    parser = argparse.ArgumentParser(description="Mindweaver CLI")
    subparsers = parser.add_subparsers(dest="command")

    # run
    run_cmd = subparsers.add_parser("run", help="Run the application")
    run_cmd.set_defaults(handler=handle_run)

    # db
    db_cmd = subparsers.add_parser("db", help="Database operations")
    db_cmd.add_argument(
        "-f", "--config", dest="config", type=str, default="alembic.ini"
    )
    db_cmd_subparser = db_cmd.add_subparsers(dest="db_command")

    # db migrate
    db_migrate_cmd = db_cmd_subparser.add_parser("migrate", help="Run DB migrations")
    db_migrate_cmd.set_defaults(handler=handle_migrate)

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
