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
# tb-env.ps1 - read-only host environment profile for evidence records.
# Prints the facts VALIDATION.md asks for in an environment profile
# (OS, shell, toolchain versions, free disk). Nothing is modified.
#Requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$Json
)

function Get-ToolVersion {
    param([string]$Name, [string[]]$VersionArgs)
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) { return $null }
    try {
        $out = & $cmd.Source @VersionArgs 2>$null | Select-Object -First 1
        return [string]$out
    } catch { return "present (version unknown)" }
}

$os = Get-CimInstance Win32_OperatingSystem -ErrorAction SilentlyContinue
$cs = Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue
$root = Split-Path -Parent $PSScriptRoot
$drive = (Get-Item $root).PSDrive
$disk = Get-PSDrive -Name $drive.Name -ErrorAction SilentlyContinue

$now = Get-Date
if ([System.TimeZoneInfo]::Local.IsDaylightSavingTime($now)) { $zone = "CDT" } else { $zone = "CST" }

$profileData = [ordered]@{
    taken        = $now.ToString("yyyy-MM-dd hh:mm tt") + " " + $zone
    host         = $env:COMPUTERNAME
    os           = if ($os) { "$($os.Caption) $($os.Version)" } else { [System.Environment]::OSVersion.VersionString }
    architecture = $env:PROCESSOR_ARCHITECTURE
    ram_gb       = if ($cs) { [math]::Round($cs.TotalPhysicalMemory / 1GB, 1) } else { $null }
    powershell   = $PSVersionTable.PSVersion.ToString()
    python       = Get-ToolVersion 'python' @('--version')
    git          = Get-ToolVersion 'git' @('--version')
    pwsh7        = Get-ToolVersion 'pwsh' @('--version')
    project_root = $root
    free_gb      = if ($disk) { [math]::Round($disk.Free / 1GB, 1) } else { $null }
}

if ($Json) {
    $profileData | ConvertTo-Json
} else {
    Write-Host "== host environment profile"
    foreach ($k in $profileData.Keys) {
        $v = $profileData[$k]
        if ($null -eq $v) { $v = "(unavailable)" }
        Write-Host ("  {0,-13} {1}" -f $k, $v)
    }
}
exit 0
