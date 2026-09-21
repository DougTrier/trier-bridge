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
"""Durable Trier Bridge-owned state (Foundation 05, docs/STATE-AND-PERSISTENCE.md).

  preferences.py  per-user preferences with Desired/Pending/Durable/Effective tracking
  journal.py      operation journal: one atomic record per consequential operation,
                  restart reconciliation, bounded retention that protects unresolved work

OWNERSHIP: only Trier Bridge state lives here. Linux system state is never
duplicated as authority (TB-INV-010, STATE-AND-PERSISTENCE section 9).
"""
