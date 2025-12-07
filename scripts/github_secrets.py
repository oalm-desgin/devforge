"""Sync secrets to GitHub repository secrets via API."""

import base64
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict

try:
    import requests
except ImportError:
    print("❌ Error: 'requests' library required for GitHub sync. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger(__name__)

# Mask all secret values in logs
_original_log = logger.info
def _masked_log(msg, *args, **kwargs):
    """Log with masked secrets."""
    # Simple masking - in production, use more sophisticated masking
    masked_msg = msg
    if isinstance(msg, str):
        # Mask common secret patterns
        import re
        masked_msg = re.sub(r'(password|secret|token|key)\s*[:=]\s*[^\s]+', r'\1: ***MASKED***', msg, flags=re.IGNORECASE)
    _original_log(masked_msg, *args, **kwargs)
logger.info = _masked_log


def sync_to_github(secrets_manager, repo: Optional[str] = None) -> None:
    """
    Sync secrets from DevForge store to GitHub repository secrets.
    
    Args:
        secrets_manager: SecretsManager instance
        repo: GitHub repository (format: owner/repo, or auto-detect from git)
    """
    # Get GitHub token from secrets
    github_token = secrets_manager.get_secret("GITHUB_TOKEN")
    if not github_token:
        print("❌ Error: GITHUB_TOKEN not found in secrets store", file=sys.stderr)
        print("   Set it with: devforge secrets set GITHUB_TOKEN", file=sys.stderr)
        sys.exit(1)
    
    # Determine repository
    if not repo:
        repo = _detect_repo_from_git(secrets_manager.project_root)
        if not repo:
            print("❌ Error: Could not detect repository. Specify with --repo owner/repo", file=sys.stderr)
            sys.exit(1)
    
    owner, repo_name = repo.split('/', 1) if '/' in repo else (None, repo)
    if not owner:
        print("❌ Error: Invalid repository format. Use: owner/repo", file=sys.stderr)
        sys.exit(1)
    
    # Get public key for encryption
    public_key_data = _get_repo_public_key(owner, repo_name, github_token)
    if not public_key_data:
        print("❌ Error: Failed to get repository public key", file=sys.stderr)
        sys.exit(1)
    
    # Get all secrets
    all_secrets = {}
    for key in secrets_manager.list_secrets():
        if key == "GITHUB_TOKEN":  # Don't sync the token itself
            continue
        value = secrets_manager.get_secret(key)
        if value:
            all_secrets[key] = value
    
    if not all_secrets:
        print("ℹ️  No secrets to sync (excluding GITHUB_TOKEN)")
        return
    
    # Sync each secret
    success_count = 0
    for key, value in all_secrets.items():
        if _update_repo_secret(owner, repo_name, key, value, public_key_data, github_token):
            success_count += 1
            print(f"✅ Synced: {key}")
        else:
            print(f"❌ Failed to sync: {key}", file=sys.stderr)
    
    print(f"\n✅ Synced {success_count}/{len(all_secrets)} secrets to GitHub")


def _detect_repo_from_git(project_root: Path) -> Optional[str]:
    """Detect GitHub repository from git remote."""
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            # Parse git URL formats
            if 'github.com' in url:
                # https://github.com/owner/repo.git or git@github.com:owner/repo.git
                parts = url.replace('.git', '').split('/')
                if 'github.com' in parts:
                    idx = parts.index('github.com')
                    if idx + 2 < len(parts):
                        return f"{parts[idx+1]}/{parts[idx+2]}"
        return None
    except Exception:
        return None


def _get_repo_public_key(owner: str, repo: str, token: str) -> Optional[Dict]:
    """Get repository public key for secret encryption."""
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get public key: {e}")
        return None


def _update_repo_secret(
    owner: str,
    repo: str,
    secret_name: str,
    secret_value: str,
    public_key_data: Dict,
    token: str
) -> bool:
    """Update a repository secret."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    
    try:
        # Decode public key
        public_key_bytes = base64.b64decode(public_key_data['key'])
        public_key = load_pem_public_key(public_key_bytes)
        
        # Encrypt secret value
        encrypted = public_key.encrypt(
            secret_value.encode('utf-8'),
            padding.PKCS1v15()
        )
        encrypted_value = base64.b64encode(encrypted).decode('utf-8')
        
        # Update secret via API
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "encrypted_value": encrypted_value,
            "key_id": public_key_data['key_id']
        }
        
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to update secret {secret_name}: {e}")
        return False

