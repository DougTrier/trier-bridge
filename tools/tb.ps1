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
# tb.ps1 - PowerShell wrapper for the Trier Bridge read-only tools.
# Works in Windows PowerShell 5.1 and PowerShell 7 (Windows or Linux).
# Usage: .\tools\tb.ps1 context
#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$TbArgs
)

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) {
    Write-Host "tb: python (3.12+) not found on PATH"
    exit 2
}

& $python.Source (Join-Path $PSScriptRoot 'tb.py') @TbArgs
exit $LASTEXITCODE
