#!/usr/bin/env pwsh

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("constitution", "specify", "plan", "tasks", "clarify", "analyze", "checklist", "implement")]
    [string]$Gate,
    [string]$PathsJson,
    [string]$FeatureDir,
    [string]$RepoRoot,
    [string]$DecisionId = "D-SPECKIT"
)

$ErrorActionPreference = 'Stop'
$uv = if ($env:SENTINEL_GATE_UV) { $env:SENTINEL_GATE_UV } else { "uv" }

function Get-JsonValue {
    param(
        [string]$JsonPath
    )

    if (-not $JsonPath -or -not (Test-Path $JsonPath -PathType Leaf)) {
        return $null
    }

    try {
        return Get-Content $JsonPath -Raw | ConvertFrom-Json
    } catch {
        return $null
    }
}

if (-not $RepoRoot) {
    try {
        $RepoRoot = git rev-parse --show-toplevel
    } catch {
        $RepoRoot = (Resolve-Path .).Path
    }
}

if (-not (Test-Path $RepoRoot -PathType Container)) {
    Write-Error "[sentinel-gate] Repo root '$RepoRoot' does not exist."
    exit 1
}

if ($PathsJson) {
    $jsonData = Get-JsonValue -JsonPath $PathsJson
    if ($jsonData) {
        if (-not $FeatureDir) {
            if ($jsonData.FEATURE_DIR) {
                $FeatureDir = $jsonData.FEATURE_DIR
            } elseif ($jsonData.SPEC_FILE) {
                $FeatureDir = Split-Path $jsonData.SPEC_FILE -Parent
            } elseif ($jsonData.IMPL_PLAN) {
                $FeatureDir = Split-Path $jsonData.IMPL_PLAN -Parent
            }
        }
        if (-not $RepoRoot -and $jsonData.REPO_ROOT) {
            $RepoRoot = $jsonData.REPO_ROOT
        }
    }
}

if (-not $FeatureDir) {
    $FeatureDir = $RepoRoot
}

function Invoke-SentinelCommand {
    param(
        [string]$Description,
        [string[]]$Arguments
    )

    Write-Host "[sentinel-gate] $Description" -ForegroundColor Cyan
    & $uv run sentinel --root $RepoRoot @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Sentinel gate failed: $Description"
    }
}

function Invoke-Contracts {
    Invoke-SentinelCommand -Description "contracts validate" -Arguments @("contracts", "validate")
}

function Invoke-Context {
    Invoke-SentinelCommand -Description "context lint" -Arguments @("context", "lint")
}

function Invoke-Capsule {
    if (-not (Test-Path $FeatureDir -PathType Container)) {
        Write-Host "[sentinel-gate] Skipping capsule check (feature directory missing: $FeatureDir)" -ForegroundColor Yellow
        return
    }
    Invoke-SentinelCommand -Description "capsule generate (dry-run)" -Arguments @(
        "capsule", "generate", $FeatureDir, "--decision", $DecisionId, "--agent", "ROUTER", "--dry-run"
    )
}

function Invoke-Tests {
    Invoke-SentinelCommand -Description "sentinel tests" -Arguments @("sentinels", "run")
}

try {
    switch ($Gate) {
        "constitution" {
            Invoke-Contracts
            Invoke-Context
        }
        "specify" {
            Invoke-Contracts
            Invoke-Context
            Invoke-Capsule
        }
        "plan" | "tasks" | "clarify" | "analyze" | "checklist" {
            Invoke-Contracts
            Invoke-Context
        }
        "implement" {
            Invoke-Contracts
            Invoke-Context
            Invoke-Capsule
            Invoke-Tests
        }
        default {
            throw "Unknown gate '$Gate'."
        }
    }
    Write-Host "[sentinel-gate] Gate '$Gate' completed successfully." -ForegroundColor Green
} catch {
    Write-Error $_
    exit 1
}
