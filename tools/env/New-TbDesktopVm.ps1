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
# New-TbDesktopVm.ps1 - create the disposable Trier Bridge Ubuntu Desktop
# test VM in Hyper-V (docs/DECISIONS.md DEC-017, AGENTS.md section 15).
#
# SECURITY / SCOPE GUARDS
#   - Only creates a VM whose name starts with "tb-". Refuses anything else.
#   - Never enumerates or touches other VMs; only Get-VM -Name <this VM>.
#   - Never creates or changes a virtual switch; uses an existing one.
#   - Writes only under -Root (default G:\tb-vms) and reports\local.
#   - Refuses to overwrite an existing VM or VHDX of the same name.
#   - Disables checkpoints and host auto-start on the new VM.
#
# Run once from an elevated PowerShell (Hyper-V cmdlets need it):
#   .\tools\env\New-TbDesktopVm.ps1 -Start
#Requires -Version 5.1
#Requires -RunAsAdministrator
#Requires -Modules Hyper-V
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$Name = "tb-ubuntu-desktop-2404",
    [string]$Root = "G:\tb-vms",
    [string]$IsoPath = "",
    [int]$Cpu = 4,
    [int]$MemoryGB = 8,
    [int]$MemoryMinGB = 4,
    [int]$MemoryMaxGB = 12,
    [int]$DiskGB = 64,
    [string]$SwitchName = "Default Switch",
    [switch]$Start
)

$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$repoRoot = Split-Path -Parent (Split-Path -Parent $here)
$seedSrc = Join-Path $here "autoinstall"
$stamp = Get-Date

function Fail([string]$msg) { Write-Host "ABORT: $msg"; exit 2 }

# ---- guards -----------------------------------------------------------------
if ($Name -notmatch '^tb-[A-Za-z0-9-]+$') { Fail "VM name must start with tb- (got '$Name')" }
if ($Root -notmatch '^[A-Za-z]:\\') { Fail "Root must be an absolute local path" }
if (Get-VM -Name $Name -ErrorAction SilentlyContinue) { Fail "VM '$Name' already exists; run Remove-TbDesktopVm.ps1 first" }
$sw = Get-VMSwitch -Name $SwitchName -ErrorAction SilentlyContinue
if (-not $sw) { Fail "virtual switch '$SwitchName' not found; this script never creates switches" }
foreach ($f in @("user-data", "meta-data")) {
    if (-not (Test-Path (Join-Path $seedSrc $f))) { Fail "missing $seedSrc\$f" }
}

$vmDir = Join-Path $Root $Name
$isoDir = Join-Path $Root "iso"
$osVhd = Join-Path $vmDir "$Name.vhdx"
$seedVhd = Join-Path $vmDir "$Name-seed.vhdx"
if (Test-Path $osVhd) { Fail "$osVhd already exists; refusing to overwrite" }
if (Test-Path $seedVhd) { Fail "$seedVhd already exists; refusing to overwrite" }

# ---- ISO --------------------------------------------------------------------
if (-not $IsoPath) {
    $cand = Get-ChildItem -Path $isoDir -Filter "ubuntu-24.04*-desktop-amd64.iso" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $cand) { Fail "no ubuntu-24.04*-desktop-amd64.iso under $isoDir; pass -IsoPath" }
    $IsoPath = $cand.FullName
}
if (-not (Test-Path $IsoPath)) { Fail "ISO not found: $IsoPath" }

$isoHash = (Get-FileHash -Algorithm SHA256 -Path $IsoPath).Hash.ToLower()
$sumsPath = Join-Path (Split-Path -Parent $IsoPath) "SHA256SUMS"
$hashState = "NOT_VERIFIED (no SHA256SUMS beside the ISO)"
if (Test-Path $sumsPath) {
    $isoName = Split-Path -Leaf $IsoPath
    $line = Get-Content $sumsPath | Where-Object { $_ -match [regex]::Escape($isoName) } | Select-Object -First 1
    if (-not $line) {
        $hashState = "NOT_VERIFIED (ISO name not listed in SHA256SUMS)"
    } elseif ($line.Split(" ")[0].ToLower() -eq $isoHash) {
        $hashState = "VERIFIED"
    } else {
        Fail "ISO SHA256 mismatch against $sumsPath - do not use this image"
    }
}
Write-Host "ISO: $IsoPath"
Write-Host "SHA256: $isoHash ($hashState)"

if (-not $PSCmdlet.ShouldProcess($Name, "create Hyper-V VM under $vmDir")) { exit 0 }

# ---- disks ------------------------------------------------------------------
New-Item -ItemType Directory -Force -Path $vmDir | Out-Null
New-VHD -Path $osVhd -SizeBytes ($DiskGB * 1GB) -Dynamic | Out-Null
Write-Host "created $osVhd ($DiskGB GB dynamic)"

# Seed disk: a small FAT volume labeled CIDATA that cloud-init/subiquity read
# as a NoCloud datasource, carrying the autoinstall answers.
New-VHD -Path $seedVhd -SizeBytes 64MB -Fixed | Out-Null
$disk = Mount-VHD -Path $seedVhd -PassThru | Get-Disk
try {
    $disk | Initialize-Disk -PartitionStyle MBR -PassThru | Out-Null
    $part = New-Partition -DiskNumber $disk.Number -UseMaximumSize -AssignDriveLetter
    $vol = Format-Volume -Partition $part -FileSystem FAT -NewFileSystemLabel "CIDATA" -Confirm:$false
    $letter = ($part | Get-Partition).DriveLetter
    if (-not $letter) { $letter = $vol.DriveLetter }
    $dest = "${letter}:\"
    Copy-Item (Join-Path $seedSrc "user-data") (Join-Path $dest "user-data")
    Copy-Item (Join-Path $seedSrc "meta-data") (Join-Path $dest "meta-data")
    Write-Host "seed volume CIDATA written at $dest"
} finally {
    Dismount-VHD -Path $seedVhd
}

# ---- VM ---------------------------------------------------------------------
$vm = New-VM -Name $Name -Generation 2 -MemoryStartupBytes ($MemoryGB * 1GB) -VHDPath $osVhd -Path $Root -SwitchName $SwitchName
Set-VM -Name $Name -ProcessorCount $Cpu `
    -DynamicMemory -MemoryMinimumBytes ($MemoryMinGB * 1GB) -MemoryMaximumBytes ($MemoryMaxGB * 1GB) `
    -AutomaticStartAction Nothing -AutomaticStopAction ShutDown `
    -CheckpointType Disabled -AutomaticCheckpointsEnabled $false `
    -Notes ("Trier Bridge disposable test VM. Created " + $stamp.ToString("yyyy-MM-dd HH:mm") + ". See tools/env/README.md. Remove with Remove-TbDesktopVm.ps1.")
Set-VMFirmware -VMName $Name -EnableSecureBoot On -SecureBootTemplate "MicrosoftUEFICertificateAuthority"
Add-VMHardDiskDrive -VMName $Name -Path $seedVhd
$dvd = Add-VMDvdDrive -VMName $Name -Path $IsoPath -Passthru
Set-VMFirmware -VMName $Name -FirstBootDevice $dvd
Enable-VMIntegrationService -VMName $Name -Name "Guest Service Interface" -ErrorAction SilentlyContinue
Write-Host "created VM '$Name': gen2, $Cpu vCPU, $MemoryGB GB (dyn $MemoryMinGB-$MemoryMaxGB), switch '$SwitchName', secure boot (MS UEFI CA), checkpoints disabled"

# ---- evidence record ----------------------------------------------------------
$reportDir = Join-Path $repoRoot "reports\local"
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$record = [ordered]@{
    created      = $stamp.ToString("yyyy-MM-dd hh:mm tt")
    vm           = $Name
    generation   = 2
    cpu          = $Cpu
    memory_gb    = $MemoryGB
    memory_range = "$MemoryMinGB-$MemoryMaxGB"
    disk_gb      = $DiskGB
    switch       = $SwitchName
    iso          = $IsoPath
    iso_sha256   = $isoHash
    iso_hash     = $hashState
    vm_dir       = $vmDir
    host         = $env:COMPUTERNAME
    note         = "Environment profile: Ubuntu 24.04 Desktop / Hyper-V Gen2 / GNOME expected / systemd / NetworkManager expected. Claims require in-guest evidence."
}
$record | ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $reportDir "env-$Name.json")
Write-Host "evidence: reports\local\env-$Name.json"

if ($Start) {
    Start-VM -Name $Name
    Write-Host "started. Open the console with:  vmconnect.exe localhost $Name"
    Write-Host "The installer will ask once whether to continue with the autoinstall; answer yes. Install then completes unattended and reboots."
} else {
    Write-Host "not started. Start with:  Start-VM -Name $Name ; vmconnect.exe localhost $Name"
}
exit 0
