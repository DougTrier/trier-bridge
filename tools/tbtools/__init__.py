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
"""Trier Bridge read-only engineering tools.

OWNERSHIP: tools/ only. These modules never modify project files; the only
writes are reports under reports/local/ (gitignored).
SECURITY: no shell execution, no network. Git is invoked with a fixed argv.
This package is engineering automation (ENGINEERING.md section 10). It is not
a product implementation-stack decision (AGENTS.md section 4).
"""
