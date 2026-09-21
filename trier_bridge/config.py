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
"""Per-user paths and atomic state writes.

OWNERSHIP: Trier Bridge writes only under its own XDG directories
(DEC-018 clause g). Nothing here touches any other application's files.
RECOVERY: every write is temp file -> flush -> fsync -> validate -> atomic
replace, so a crash never leaves a half-written file in place of a known-good
one (TB-INV-181, TB-INV-182, docs/SECURITY.md section 12.4).
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

APP_DIR = "trier-bridge"
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Paths:
    config: Path
    data: Path
    state: Path
    cache: Path

    @property
    def preferences_file(self) -> Path:
        return self.config / "preferences.json"

    @property
    def integration_ledger_file(self) -> Path:
        return self.config / "integrations.json"

    @property
    def log_dir(self) -> Path:
        return self.state / "logs"

    @property
    def journal_dir(self) -> Path:
        return self.state / "journal"


def _xdg(env: str, default: str, environ: dict[str, str]) -> Path:
    raw = environ.get(env, "").strip()
    return Path(raw) if raw else Path(environ.get("HOME", "~")).expanduser() / default


def resolve_paths(environ: dict[str, str] | None = None) -> Paths:
    """Resolve XDG base directories; environment is injectable for tests (real dirs, no mocks)."""
    e = dict(os.environ) if environ is None else environ
    return Paths(
        config=_xdg("XDG_CONFIG_HOME", ".config", e) / APP_DIR,
        data=_xdg("XDG_DATA_HOME", ".local/share", e) / APP_DIR,
        state=_xdg("XDG_STATE_HOME", ".local/state", e) / APP_DIR,
        cache=_xdg("XDG_CACHE_HOME", ".cache", e) / APP_DIR,
    )


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


class StateWriteError(OSError):
    """The state could not be written; the previous file, if any, is untouched."""


def atomic_write_bytes(
    path: Path, data: bytes, validate: Callable[[bytes], bool] | None = None
) -> None:
    """Write ``data`` to ``path`` atomically. On any failure the old file remains."""
    try:
        ensure_dir(path.parent)
        fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    except OSError as exc:  # read-only, permission lost, or no space for the temp file
        raise StateWriteError(f"could not write {path.name}: {exc}") from exc
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        if validate is not None and not validate(tmp.read_bytes()):
            raise StateWriteError(f"validation failed for {path.name}; original kept")
        os.replace(tmp, path)
        try:
            dir_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            return  # directory fsync unsupported on this platform (e.g. Windows); file is replaced
        try:
            os.fsync(dir_fd)
        except OSError:
            pass
        finally:
            os.close(dir_fd)
    except Exception as exc:
        try:
            tmp.unlink(missing_ok=True)
        finally:
            pass
        if isinstance(exc, StateWriteError):
            raise
        raise StateWriteError(f"could not write {path.name}: {exc}") from exc


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def _json_valid(raw: bytes) -> bool:
    try:
        json.loads(raw.decode("utf-8"))
        return True
    except (ValueError, UnicodeDecodeError):
        return False


def save_json(path: Path, payload: dict[str, Any]) -> None:
    """Persist a versioned JSON document atomically."""
    doc = {"schema": SCHEMA_VERSION, **payload}
    raw = json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
    atomic_write_bytes(path, raw, validate=_json_valid)


class StateSchemaTooNew(ValueError):
    """A newer Trier Bridge wrote this file; open read-only rather than guess (TB-INV-029)."""


def load_json(path: Path) -> dict[str, Any] | None:
    """Return the document or None if absent. Corrupt files raise; newer schemas raise."""
    if not path.exists():
        return None
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError(f"{path.name}: expected a JSON object")
    schema = int(doc.get("schema", 0))
    if schema > SCHEMA_VERSION:
        raise StateSchemaTooNew(f"{path.name}: schema {schema} is newer than {SCHEMA_VERSION}")
    return doc
