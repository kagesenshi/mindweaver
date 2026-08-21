# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import argparse
from unittest.mock import patch
from mindweaver.cli import get_parser, handle_queue_flush


def test_cli_parser_queue_flush():
    """Verify that the queue flush command is correctly registered in the CLI parser."""
    parser = get_parser()
    
    # Parse the queue flush arguments
    args = parser.parse_args(["queue", "flush"])
    
    assert args.command == "queue"
    assert args.queue_command == "flush"
    assert args.handler == handle_queue_flush


@patch("mindweaver.celery_app.app.control.purge")
def test_handle_queue_flush(mock_purge):
    """Verify that handle_queue_flush invokes the celery purge method."""
    mock_purge.return_value = 42
    
    args = argparse.Namespace()
    handle_queue_flush(args)
    
    mock_purge.assert_called_once()


def test_cli_parser_run_defaults():
    """Verify default arguments for run command."""
    parser = get_parser()
    args = parser.parse_args(["run"])
    assert args.command == "run"
    assert args.port == 8000
    assert args.host == "127.0.0.1"
    assert args.log_file == "logs/mindweaver.log"


def test_cli_parser_run_custom():
    """Verify custom arguments for run command."""
    parser = get_parser()
    args = parser.parse_args(["run", "-p", "9000", "-b", "0.0.0.0", "-l", "/tmp/custom.log"])
    assert args.command == "run"
    assert args.port == 9000
    assert args.host == "0.0.0.0"
    assert args.log_file == "/tmp/custom.log"


@patch("uvicorn.run")
@patch("pathlib.Path.mkdir")
def test_handle_run(mock_mkdir, mock_uvicorn_run):
    """Verify handle_run correctly updates logging configuration and calls uvicorn.run."""
    from mindweaver.cli import handle_run, RunArgs
    from pathlib import Path
    
    args = RunArgs()
    args.port = 8000
    args.host = "127.0.0.1"
    args.log_file = "/tmp/test-logs/mw.log"
    
    handle_run(args)
    
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_uvicorn_run.assert_called_once()
    
    # Verify the log_config passed to uvicorn.run
    call_kwargs = mock_uvicorn_run.call_args[1]
    assert "log_config" in call_kwargs
    log_config = call_kwargs["log_config"]
    
    assert "file_default" in log_config["handlers"]
    assert "file_access" in log_config["handlers"]
    assert log_config["handlers"]["file_default"]["filename"] == str(Path("/tmp/test-logs/mw.log").resolve())
    assert "file_default" in log_config["loggers"]["uvicorn"]["handlers"]
    assert "file_access" in log_config["loggers"]["uvicorn.access"]["handlers"]

