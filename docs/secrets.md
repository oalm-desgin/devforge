# Secure Secrets & Environment Management

DevForge provides a comprehensive secrets management system that ensures no plaintext secrets are ever committed to your repository.

## Overview

The secrets management system includes:

- **Encrypted local storage** - Secrets are encrypted at rest using Fernet (AES-128)
- **Platform-specific key management** - Encryption keys stored in secure system storage
- **Runtime injection** - Secrets injected only at runtime, never in templates
- **GitHub Secrets sync** - Automatic synchronization with GitHub repository secrets
- **Pre-commit scanning** - Automatic detection of secret leaks before commits

## Quick Start

### 1. Initialize Secrets Store

```bash
devforge secrets init
```

This creates an encrypted `.secrets.devforge` file in your project root.

### 2. Set Secrets

```bash
# Interactive (prompts for value)
devforge secrets set DATABASE_PASSWORD

# Direct value
devforge secrets set DATABASE_PASSWORD "my_secure_password"
```

### 3. List Secrets

```bash
devforge secrets list
```

### 4. Inject Secrets for Runtime

```bash
devforge secrets inject
```

This generates `.env.secrets` which can be loaded by Docker Compose or your application.

### 5. Sync to GitHub

```bash
# Auto-detect repository from git remote
devforge secrets sync-github

# Or specify repository
devforge secrets sync-github --repo owner/repo
```

## Security Features

### Encryption

- **Algorithm**: Fernet (AES-128 in CBC mode)
- **Key Storage**:
  - **Windows**: Credential Manager (fallback to `~/.devforge/key`)
  - **macOS**: Keychain (fallback to `~/.devforge/key`)
  - **Linux**: `~/.devforge/key` (readable only by owner)

### No Plaintext Secrets

- Secrets are **never** rendered into template files
- Only encrypted `.secrets.devforge` is stored locally
- `.env.secrets` is generated at runtime and should be gitignored
- All secrets are masked in logs

### Pre-commit Scanning

The secret scanner automatically detects:

- AWS access keys
- JWT tokens
- API tokens
- Database passwords
- Private keys
- High-entropy strings (potential secrets)

**Setup pre-commit hook:**

```bash
# Linux/macOS
bash scripts/setup_secret_hooks.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File scripts/setup_secret_hooks.ps1
```

## Integration with Docker

### Automatic Injection

When you run `devforge secrets inject`, it generates `.env.secrets`:

```bash
DATABASE_PASSWORD="encrypted_value_here"
BACKEND_SECRET_KEY="another_secret"
```

### Docker Compose Integration

Add to your `docker-compose.yml`:

```yaml
services:
  backend:
    env_file:
      - .env.secrets
  database:
    env_file:
      - .env.secrets
```

Then load secrets before starting:

```bash
devforge secrets inject
docker compose up
```

## CI/CD Integration

### GitHub Actions

DevForge automatically adds secret validation to your CI workflow:

```yaml
jobs:
  validate-secrets:
    runs-on: ubuntu-latest
    steps:
      - name: Check for required secrets
        run: |
          # Validates all required secrets are present
```

### Required Secrets

When you generate a project with backend+database or CI enabled, these secrets are automatically created:

- `DATABASE_PASSWORD` - Database password
- `BACKEND_SECRET_KEY` - Backend session/JWT secret

### Secret Validation

The CI pipeline will:

1. **Validate presence** - Check all required secrets exist
2. **Scan for leaks** - Run secret scanner on codebase
3. **Mask output** - All secret values are masked in logs
4. **Fail on detection** - Pipeline fails if secrets are detected in code

## GitHub Secrets Sync

### Prerequisites

1. Set `GITHUB_TOKEN` in your secrets store:
   ```bash
   devforge secrets set GITHUB_TOKEN "ghp_your_token_here"
   ```

2. Token must have `repo` scope and `secrets:write` permission

### Syncing Secrets

```bash
devforge secrets sync-github
```

This will:
- Read all secrets from `.secrets.devforge`
- Encrypt each secret with repository's public key
- Upload to GitHub repository secrets
- Exclude `GITHUB_TOKEN` from sync (it's used for authentication)

### Viewing Synced Secrets

Go to your GitHub repository:
- Settings → Secrets and variables → Actions
- All synced secrets will be listed there

## Best Practices

### 1. Never Commit Secrets

- ✅ `.secrets.devforge` is automatically gitignored
- ✅ `.env.secrets` is automatically gitignored
- ✅ Always use `devforge secrets set` instead of editing files directly

### 2. Use Strong Passwords

```bash
# Generate secure password (32 characters)
devforge secrets set DATABASE_PASSWORD $(openssl rand -base64 32)
```

### 3. Rotate Secrets Regularly

```bash
# Update secret
devforge secrets set DATABASE_PASSWORD "new_password"

# Re-sync to GitHub
devforge secrets sync-github
```

### 4. Use Different Secrets per Environment

- Development: Local `.secrets.devforge`
- Staging: GitHub Secrets
- Production: GitHub Secrets + additional security

### 5. Audit Secret Access

```bash
# List all stored secrets
devforge secrets list

# Check what's in GitHub
# (via GitHub UI: Settings → Secrets)
```

## Troubleshooting

### "Secrets store not initialized"

Run:
```bash
devforge secrets init
```

### "Encryption key not found"

The encryption key is stored in:
- Windows: Credential Manager → DevForge:EncryptionKey
- macOS: Keychain → DevForge:EncryptionKey
- Linux: `~/.devforge/key`

If missing, reinitialize:
```bash
devforge secrets init
```

### "GitHub sync failed"

1. Verify `GITHUB_TOKEN` is set:
   ```bash
   devforge secrets get GITHUB_TOKEN
   ```

2. Check token permissions (needs `repo` and `secrets:write`)

3. Verify repository format: `owner/repo`

### Pre-commit hook not working

1. Verify hook is installed:
   ```bash
   ls -la .git/hooks/pre-commit
   ```

2. Reinstall if needed:
   ```bash
   bash scripts/setup_secret_hooks.sh
   ```

## API Reference

### SecretsManager

```python
from src.core.secrets_manager import SecretsManager

manager = SecretsManager(project_root)
manager.init_store()
manager.set_secret("KEY", "value")
value = manager.get_secret("KEY")
keys = manager.list_secrets()
manager.inject_runtime_env()
```

### CLI Commands

```bash
devforge secrets init              # Initialize store
devforge secrets set <KEY> [VALUE]  # Set secret
devforge secrets get <KEY>          # Get secret
devforge secrets list               # List all keys
devforge secrets inject             # Generate .env.secrets
devforge secrets sync-github [--repo OWNER/REPO]  # Sync to GitHub
```

## Security Guarantees

- ✅ **Encryption at rest** - All secrets encrypted with AES-128
- ✅ **No plaintext in repo** - Secrets never committed
- ✅ **Platform security** - Keys stored in system credential stores
- ✅ **Runtime only** - Secrets injected only when needed
- ✅ **Leak prevention** - Pre-commit scanning blocks commits
- ✅ **CI validation** - Automated secret presence checks
- ✅ **Masked logs** - All secret values masked in output

## See Also

- [Installation Guide](install.md)
- [Usage Guide](usage.md)
- [Environment Variables](env.md)
- [CI/CD Configuration](ci.md)

