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
"""Where shipped data lives (catalog, help).

Order: TRIER_BRIDGE_DATA_DIR (development override), the source tree when
running from a checkout, then the packaged location /usr/share/trier-bridge
(docs/PACKAGING.md section 3).
"""
from __future__ import annotations

import os
from pathlib import Path

PACKAGED_DATA_DIR = Path("/usr/share/trier-bridge")


def data_dir(environ: dict[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    override = env.get("TRIER_BRIDGE_DATA_DIR", "").strip()
    if override:
        return Path(override)
    source = Path(__file__).resolve().parents[1] / "data"
    if (source / "catalog" / "concepts.json").is_file():
        return source
    return PACKAGED_DATA_DIR


def catalog_path(environ: dict[str, str] | None = None) -> Path:
    return data_dir(environ) / "catalog" / "concepts.json"


def terminal_runner_path(environ: dict[str, str] | None = None) -> Path:
    """The shipped helper that holds a terminal window open around one fixed program."""
    return data_dir(environ) / "terminal" / "tb-hold-terminal.py"
