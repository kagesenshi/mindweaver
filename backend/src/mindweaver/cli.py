import argparse
from dataclasses import dataclass
from alembic.config import Config as AlembicConfig
from alembic.command import revision, upgrade
from typing import Callable
from mindweaver.config import settings
from mindweaver.app import app
from sqlmodel import SQLModel, Session, select
import mindweaver.fw.model
import mindweaver.service.data_source
from mindweaver.service.data_source import DataSource
from mindweaver.crypto import generate_fernet_key, rotate_key, EncryptionError
import asyncio
import sqlalchemy as sa
import uvicorn
from .config import logger


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
    print("\n" + "=" * 60)
    print("Generated new Fernet encryption key:")
    print("=" * 60)
    print(key)
    print("=" * 60)
    print("\nIMPORTANT: Store this key securely!")
    print("Set it as the MINDWEAVER_FERNET_KEY environment variable.")
    print("=" * 60 + "\n")


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
            # Fetch all data sources
            statement = select(DataSource).where(DataSource.type == "Database")
            data_sources = session.exec(statement).all()

            if not data_sources:
                logger.info("No database data sources found.")
                return

            logger.info(f"Found {len(data_sources)} database data source(s) to rotate.")

            rotated_count = 0
            for ds in data_sources:
                try:
                    # Check if parameters contain a password
                    if ds.parameters and "password" in ds.parameters:
                        encrypted_password = ds.parameters["password"]
                        if encrypted_password:
                            # Rotate the password
                            new_encrypted_password = rotate_key(
                                args.old_key, args.new_key, encrypted_password
                            )
                            # Update the data source
                            ds.parameters["password"] = new_encrypted_password
                            session.add(ds)
                            rotated_count += 1
                            logger.info(
                                f"Rotated key for data source: {ds.name} (ID: {ds.id})"
                            )
                except EncryptionError as e:
                    logger.error(
                        f"Failed to rotate key for data source {ds.name} (ID: {ds.id}): {str(e)}"
                    )
                except Exception as e:
                    logger.error(
                        f"Unexpected error rotating key for data source {ds.name} (ID: {ds.id}): {str(e)}"
                    )

            # Commit all changes
            session.commit()
            logger.info(f"\nKey rotation completed successfully!")
            logger.info(
                f"Rotated {rotated_count} out of {len(data_sources)} data source(s)."
            )
            logger.info(f"\nIMPORTANT: Update MINDWEAVER_FERNET_KEY to the new key.")

    except Exception as e:
        logger.error(f"Failed to rotate keys: {str(e)}")
    finally:
        engine.dispose()


def get_parser() -> argparse.ArgumentParser:
    """
    Construct argument parser
    """
    parser = argparse.ArgumentParser(description="Mindweaver CLI")
    subparsers = parser.add_subparsers(dest="command")

    # run
    run_cmd = subparsers.add_parser("run", help="Run the application")
    run_cmd.add_argument("-p", "--port", dest="port", type=int, default=8000)
    run_cmd.add_argument("-b", "--bind", dest="host", type=str, default="127.0.0.1")
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
