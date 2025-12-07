# Setup pre-commit hook for secret scanning (PowerShell)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = if (Test-Path .git) { (Get-Location).Path } else { throw "Not a git repository. Run 'git init' first." }
$HooksDir = Join-Path $ProjectRoot ".git\hooks"
$ScanScript = Join-Path $ScriptDir "scan_secrets.py"

if (-not (Test-Path $ScanScript)) {
    Write-Host "❌ Error: Secret scanner script not found: $ScanScript" -ForegroundColor Red
    exit 1
}

$PreCommitHook = Join-Path $HooksDir "pre-commit"

# Create pre-commit hook
$HookContent = @"
# Pre-commit hook for secret scanning

`$ScriptDir = Split-Path -Parent `$MyInvocation.MyCommand.Path
`$ProjectRoot = (Get-Location).Path
`$ScanScript = Join-Path `$ScriptDir "..\..\scripts\scan_secrets.py"

if (Test-Path `$ScanScript) {
    python `$ScanScript `$ProjectRoot
    if (`$LASTEXITCODE -ne 0) {
        exit `$LASTEXITCODE
    }
}
"@

$HookContent | Out-File -FilePath $PreCommitHook -Encoding UTF8

# Make executable (Unix-like systems)
if (Get-Command chmod -ErrorAction SilentlyContinue) {
    & chmod +x $PreCommitHook
}

Write-Host "✅ Pre-commit hook installed" -ForegroundColor Green
Write-Host "   Location: $PreCommitHook"
Write-Host "   Scanner: $ScanScript"

