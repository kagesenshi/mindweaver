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
