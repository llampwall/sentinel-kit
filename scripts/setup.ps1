#!/usr/bin/env pwsh
<#
.SYNOPSIS
Bootstrap SentinelKit tooling (uv/specify-cli + pnpm workspace).

.DESCRIPTION
Runs the same flow as `make sentinel-install` for Windows users:
1. Installs/refreshes specify-cli via uv.
2. Enables Corepack and activates the pinned pnpm version.
3. Installs dependencies inside `.sentinel/` (accepts optional PNPM flags).

.PARAMETER PnpmFlags
Additional arguments passed to `pnpm install` (e.g. --registry overrides).
#>

[CmdletBinding()]
param(
    [string]$PnpmFlags
)

$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/powershell/common.ps1"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$repoUri = [System.Uri]::new($repoRoot.ProviderPath).AbsoluteUri
$sentinelDir = Join-Path $repoRoot ".sentinel"

if (-not $PnpmFlags -and $env:PNPM_FLAGS) {
    $PnpmFlags = $env:PNPM_FLAGS
}

function Write-StepInfo {
    param(
        [string]$Message,
        [ConsoleColor]$Color = [ConsoleColor]::Cyan
    )
    Write-Host $Message -ForegroundColor $Color
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,
        [Parameter(Mandatory = $true)]
        [ScriptBlock]$Script
    )

    Write-StepInfo "==> $Message"
    & $Script
    Write-StepInfo "✓ $Message" -Color Green
}

Invoke-Step "Installing specify-cli via uv" {
    uv tool install --from $repoUri specify-cli
}

Invoke-Step "Enabling Corepack and pnpm 9.12.0" {
    corepack enable
    corepack prepare pnpm@9.12.0 --activate
}

Invoke-Step "Installing .sentinel workspace dependencies" {
    Push-Location $sentinelDir
    if ([string]::IsNullOrWhiteSpace($PnpmFlags)) {
        pnpm install
    }
    else {
        pnpm install $PnpmFlags
    }
    Pop-Location
}

Write-StepInfo "Sentinel tooling ready. Optional PNPM flags can be supplied via -PnpmFlags or PNPM_FLAGS env variable for proxy/caching setups."
