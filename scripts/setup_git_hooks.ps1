# Setup git hooks for commit message validation (PowerShell)

$hooksDir = ".git\hooks"
$commitMsgHook = "$hooksDir\commit-msg"

# Create hooks directory if it doesn't exist
if (-not (Test-Path $hooksDir)) {
    New-Item -ItemType Directory -Path $hooksDir | Out-Null
}

# Create commit-msg hook
@"
#!/bin/bash
# Validate commit message format

python scripts/validate_commit_msg.py `$1
"@ | Out-File -FilePath $commitMsgHook -Encoding utf8

Write-Host "Git hooks installed successfully!"
Write-Host "Commit messages will now be validated for Conventional Commits format."

