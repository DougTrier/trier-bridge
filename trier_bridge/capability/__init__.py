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
"""Capability discovery (Foundation 02, docs/PLATFORMS.md section 6).

OWNERSHIP: the only place that decides what this machine is and which
backends exist. Everything is read-only and side-effect free (TB-INV-036,
TB-INV-046). Unknown stays Unknown (TB-INV-035).

  model.py      CapabilityRecord, EnvironmentProfile, freshness rules
  facts.py      pure parsers for os-release and similar text (testable anywhere)
  discovery.py  the Linux reads: D-Bus properties and files, bounded timeouts
"""
