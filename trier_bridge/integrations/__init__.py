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
"""Desktop integrations chosen by the user (DEC-019, SCOPE-14).

  ledger.py   what was applied and every file it wrote, so removal is exact (DEC-018 g)
  catalog.py  the integrations, their groups, and their apply/remove/status logic

Nothing here is active until the user applies it from the setup screen; every
integration writes only under the user's own XDG directories and is
individually reversible (TB-INV-025, TB-INV-077).
"""
