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
"""Bridge Terminal (Foundation 07): Windows commands as typed operations.

  grammar.py   strict tokenizer and command table; parse failure performs no operation
  commands.py  read-only command implementations over the Foundation 04 adapters

Never string-to-shell (TB-SEC-004, TB-INV-083). Unknown commands, unknown
switches, unparsed residue, and any shell syntax are rejected as a whole
(TB-INV-085 to 088). Mode is explicit and never falls through to a shell
(TB-INV-082, TB-INV-102).
"""
