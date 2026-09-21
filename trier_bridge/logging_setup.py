# Copyright 2026 Doug Trier
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Bounded, redacted, local logging (docs/CODE-QUALITY.md section 20).

SECURITY: a redaction filter runs on every record before it is written, so a
password, token, or key that reaches a log call is masked at the source
(TB-SEC-015, TB-INV-123). Bounded: rotating files with a fixed total budget
(TB-INV-203). Local: no network handlers exist here or anywhere.
"""
from __future__ import annotations

import logging
import logging.handlers
import re
from pathlib import Path

from .config import ensure_dir

LOG_FILE = "trier-bridge.log"
MAX_BYTES = 1_000_000
BACKUPS = 3

# key=value or key: value forms for common secret names. The value is a quoted
# string, an auth scheme plus its credential ("Bearer xxx", "Basic xxx"), or
# one token. Standalone bearer tokens are masked too.
_SECRET_RX = re.compile(
    r"(?i)\b(password|passwd|passphrase|secret|token|api[_-]?key|private[_-]?key|authorization)"
    r"(\s*[=:]\s*)((?:bearer|basic)\s+\S+|\"[^\"]*\"|'[^']*'|\S+)"
)
_BEARER_RX = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}")
MASK = "[redacted]"


def redact(text: str) -> str:
    text = _SECRET_RX.sub(lambda m: f"{m.group(1)}{m.group(2)}{MASK}", text)
    return _BEARER_RX.sub(f"bearer {MASK}", text)


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Format first, then mask: rewriting the template would break %-formatting
        # and drop the record instead of masking the value.
        record.msg = redact(record.getMessage())
        record.args = ()
        return True


def configure(log_dir: Path, level: int = logging.INFO, also_stderr: bool = False) -> Path:
    """Install the file handler with redaction. Returns the log file path."""
    ensure_dir(log_dir)
    log_path = log_dir / LOG_FILE
    root = logging.getLogger()
    root.setLevel(level)
    for h in list(root.handlers):
        root.removeHandler(h)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    fh = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=MAX_BYTES, backupCount=BACKUPS, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    fh.addFilter(RedactingFilter())
    root.addHandler(fh)
    if also_stderr:
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        sh.addFilter(RedactingFilter())
        root.addHandler(sh)
    return log_path
