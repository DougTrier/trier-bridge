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
"""Trier Bridge: a Windows-to-Linux experience compatibility layer.

Package layout (docs/ENGINEERING.md section 4):
  core/        typed operations, states, identities, errors: pure Python, no GTK, no I/O
  config.py    XDG paths and atomic per-user state writes (TB-INV-181)
  logging_setup.py  bounded, redacted local logging (TB-INV-123, CODE-QUALITY section 20)
  ui/          GTK 4 / libadwaita presentation: collects intent, mirrors state, never authority

Everything here runs as the signed-in user. There is no privileged component
(docs/PRIVILEGE-MODEL.md).
"""

__version__ = "0.1.0.dev1"
APP_ID = "org.triertech.TrierBridge"
APP_NAME = "Trier Bridge"
