# Copyright 2026 Doug Trier
# SPDX-License-Identifier: Apache-2.0
"""TB-T123/TB-T203: secrets never reach the log; the log is bounded."""
import logging
import logging.handlers
from pathlib import Path

from trier_bridge.logging_setup import BACKUPS, MAX_BYTES, configure, redact


def test_redact_common_secret_forms() -> None:
    assert redact("password=hunter22") == "password=[redacted]"
    assert redact("Token: 'abc123xyz'") == "Token: [redacted]"
    assert redact('api_key="K-1234567"') == "api_key=[redacted]"
    assert redact("Authorization: Bearer eyJhbGciOi.abc.def") == "Authorization: [redacted]"
    assert redact("nothing secret here") == "nothing secret here"


def test_file_handler_redacts_and_stays_local(tmp_path: Path) -> None:
    log_path = configure(tmp_path / "logs", level=logging.INFO)
    logging.getLogger("tb.test").info("connecting with password=%s to share", "s3cr3tpw")
    logging.shutdown()
    text = log_path.read_text(encoding="utf-8")
    assert "s3cr3tpw" not in text and "[redacted]" in text
    root = logging.getLogger()
    assert all(not isinstance(h, logging.handlers.SocketHandler) for h in root.handlers)


def test_log_budget_is_bounded() -> None:
    assert MAX_BYTES * (BACKUPS + 1) <= 4_000_000
