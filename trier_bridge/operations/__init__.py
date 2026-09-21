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
"""Typed mutations (Foundation 06).

Each module owns one operation family and follows the same lifecycle
(docs/PRIVILEGE-MODEL.md section 4): observe → preview → revalidate identity →
execute one bounded action → verify the postcondition → journal → structured
result. There is no privileged helper; class C operations call the owning
system service, which asks polkit itself.
"""
