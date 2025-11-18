import argparse
from dataclasses import dataclass
from alembic.config import Config as AlembicConfig
from alembic.command import revision, upgrade
from typing import Callable
from mindweaver.config import settings
import mindweaver.db.base
import mindweaver.db.data_source
import asyncio
from .config import logger

class RunArgs(argparse.Namespace):
    pass

def handle_run(args: RunArgs):
    pass

class MigrateArgs(argparse.Namespace):
    config: str

def handle_migrate(args: MigrateArgs):
    config = AlembicConfig(args.config)
    config.set_main_option('sqlalchemy.url', settings.db_uri)
    upgrade(config, revision='heads') 
    logger.info('Update completed successfully.')

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
    config.set_main_option('sqlalchemy.url', settings.db_uri)
    revision(config, autogenerate=args.autogenerate, message=args.message)
    logger.info("Migration generated successfully.")

def get_parser() -> argparse.ArgumentParser:
    """
    Construct argument parser
    """
    parser = argparse.ArgumentParser(description="Mindweaver CLI")
    subparsers = parser.add_subparsers(dest='command')

    # run 
    run_cmd = subparsers.add_parser('run', help='Run the application')
    run_cmd.set_defaults(handler=handle_run)

    # db
    db_cmd = subparsers.add_parser('db', help='Database operations')
    db_cmd.add_argument('-f', '--config', dest='config', type=str, default='alembic.ini')
    db_cmd_subparser = db_cmd.add_subparsers(dest='db_command')

    # db migrate
    db_migrate_cmd = db_cmd_subparser.add_parser('migrate', help='Run DB migrations')
    db_migrate_cmd.set_defaults(handler=handle_migrate)

    # db create migration
    db_revision_cmd = db_cmd_subparser.add_parser('revision', help='Generate DB migration')
    db_revision_cmd.add_argument('-m', '--message', dest='message', required=True, type=str)
    db_revision_cmd.add_argument('-a', '--autogenerate', dest='autogenerate', action='store_true', default=False)
    db_revision_cmd.set_defaults(handler=handle_revision)

    return parser

class MainArgs(argparse.Namespace):
    handler: Callable[[argparse.Namespace], None]

def main():
    parser = get_parser()
    args: MainArgs = parser.parse_args()
    args.handler(args)
