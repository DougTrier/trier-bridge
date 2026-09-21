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
"""Entry point: ``trier-bridge`` / ``python -m trier_bridge``.

Sets up per-user paths and bounded logging, then hands over to the GTK
application. GTK is imported lazily so the core stays importable (and
testable) on machines without PyGObject.
"""
from __future__ import annotations

import logging
import sys

from . import __version__
from .config import resolve_paths
from .logging_setup import configure

log = logging.getLogger("trier_bridge")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)
    if "--version" in args:
        print(f"trier-bridge {__version__}")
        return 0
    paths = resolve_paths()
    log_path = configure(paths.log_dir, also_stderr="--verbose" in args)
    log.info("trier-bridge %s starting; log at %s", __version__, log_path)
    try:
        from .ui.app import run
    except ImportError as exc:  # PyGObject / GTK 4 / libadwaita missing on this machine
        log.error("desktop libraries unavailable: %s", exc)
        print(
            "Trier Bridge needs python3-gi, GTK 4, and libadwaita, which are part of Ubuntu "
            "Desktop 24.04. Nothing was changed.",
            file=sys.stderr,
        )
        return 2
    return run([a for a in args if a != "--verbose"])


if __name__ == "__main__":
    sys.exit(main())
