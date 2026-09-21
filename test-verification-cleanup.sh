#!/bin/sh
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
#
# Removes the scratch files created by test-verification-setup.sh.
# Run this after you're done with the checklist. Only removes
# ~/tb-verify-scratch; nothing else is touched.
set -e
DIR="$HOME/tb-verify-scratch"
if [ -d "$DIR" ]; then
    rm -rf "$DIR"
    echo "Removed $DIR"
else
    echo "Nothing to remove ($DIR does not exist)"
fi

# Reminder, not automatic: if you did section 3.6 (del test-copy.txt),
# that file is in the Trash (Recycle Bin), not deleted. Empty the Trash
# yourself in Files if you want it gone for good.
echo "Note: anything you moved to the Trash during testing is still there."
echo "Empty it yourself in Files if you want it gone."
