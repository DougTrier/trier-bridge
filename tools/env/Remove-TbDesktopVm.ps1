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
# Remove-TbDesktopVm.ps1 - tear down the disposable Trier Bridge test VM
# (docs/DECISIONS.md DEC-017, ledger ENV-03).
#
# SCOPE GUARDS
#   - Only acts on a VM whose name starts with "tb-".
#   - Only deletes files under <Root>\<Name>\ ; the ISO folder is kept.
#   - Asks for confirmation unless -Force.
#
# Run from an elevated PowerShell:
#   .\tools\env\Remove-TbDesktopVm.ps1
#Requires -Version 5.1
#Requires -RunAsAdministrator
#Requires -Modules Hyper-V
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = "High")]
param(
    [string]$Name = "tb-ubuntu-desktop-2404",
    [string]$Root = "G:\tb-vms",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

function Fail([string]$msg) { Write-Host "ABORT: $msg"; exit 2 }

if ($Name -notmatch '^tb-[A-Za-z0-9-]+$') { Fail "VM name must start with tb- (got '$Name')" }
if ($Root -notmatch '^[A-Za-z]:\\') { Fail "Root must be an absolute local path" }
$vmDir = Join-Path $Root $Name

$vm = Get-VM -Name $Name -ErrorAction SilentlyContinue
if (-not $vm -and -not (Test-Path $vmDir)) { Write-Host "nothing to remove: no VM '$Name' and no $vmDir"; exit 0 }

if (-not $Force -and -not $PSCmdlet.ShouldProcess("$Name and $vmDir", "turn off, unregister, and delete")) { exit 0 }

$changed = @()
if ($vm) {
    if ($vm.State -ne "Off") {
        Stop-VM -Name $Name -TurnOff -Force
        $changed += "turned off"
    }
    Remove-VM -Name $Name -Force
    $changed += "unregistered VM"
}
if (Test-Path $vmDir) {
    # Extra guard: only delete a folder named exactly after the tb- VM under Root.
    $full = (Resolve-Path $vmDir).Path
    if ($full -ne (Join-Path (Resolve-Path $Root).Path $Name)) { Fail "refusing to delete unexpected path $full" }
    Remove-Item -Recurse -Force $full
    $changed += "deleted $full"
}

$reportDir = Join-Path $repoRoot "reports\local"
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$record = [ordered]@{
    removed = (Get-Date).ToString("yyyy-MM-dd hh:mm tt")
    vm      = $Name
    actions = $changed
    kept    = (Join-Path $Root "iso")
}
$record | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $reportDir "env-$Name-removed.json")
Write-Host ("removed '{0}': {1}" -f $Name, ($changed -join "; "))
Write-Host "kept ISO folder $(Join-Path $Root 'iso'); delete it by hand if no longer wanted"
exit 0
