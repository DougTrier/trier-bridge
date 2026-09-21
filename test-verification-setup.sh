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
# Creates throwaway test fixtures for TEST-AND-VERIFICATION-POINTS.md.
# Run this once in the VM console before starting the checklist.
# Everything it creates lives under ~/tb-verify-scratch and touches
# nothing else on the system. Safe to re-run any time.
set -e
DIR="$HOME/tb-verify-scratch"
mkdir -p "$DIR"
cd "$DIR"

# For section 3.5/3.6 (copy, delete/Trash)
printf 'This is a throwaway test file for the Files/copy/delete checklist rows.\n' > test.txt

# For section 5.4/5.5 (findstr /I and /R)
cat > sample.txt <<'EOF'
Hello there, this line has a greeting.
This line does not.
HELLO IN CAPS, still a greeting.
Nothing to see on this line either.
EOF

echo "Scratch files ready in $DIR"
echo "  test.txt    - copy/delete tests (checklist section 3)"
echo "  sample.txt  - findstr tests (checklist section 5)"
echo
echo "cd $DIR before running the Command Prompt findstr steps,"
echo "so relative paths like 'sample.txt' resolve."
