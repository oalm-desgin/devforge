"""CLI commands for secrets management."""

import sys
import getpass
from pathlib import Path
from typing import Optional

from ..core.secrets_manager import SecretsManager
from ..core.errors import GenerationError


def cmd_secrets_init(project_path: Optional[Path] = None) -> None:
    """Initialize secrets store."""
    manager = SecretsManager(project_path)
    created = manager.init_store()
    if created:
        print("✅ Secrets store initialized")
        print(f"   Location: {manager.secrets_file}")
    else:
        print("ℹ️  Secrets store already exists")


def cmd_secrets_set(key: str, value: Optional[str] = None, project_path: Optional[Path] = None) -> None:
    """
    Set a secret value.
    
    Args:
        key: Secret key name
        value: Secret value (if not provided, will prompt)
        project_path: Project root directory
    """
    manager = SecretsManager(project_path)
    
    if not manager.secrets_file.exists():
        print("❌ Secrets store not initialized. Run 'devforge secrets init' first.", file=sys.stderr)
        sys.exit(1)
    
    if value is None:
        value = getpass.getpass(f"Enter value for {key}: ")
        if not value:
            print("❌ Secret value cannot be empty", file=sys.stderr)
            sys.exit(1)
    
    try:
        manager.set_secret(key, value)
        print(f"✅ Set secret: {key}")
    except Exception as e:
        print(f"❌ Failed to set secret: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_secrets_get(key: str, project_path: Optional[Path] = None) -> None:
    """
    Get a secret value.
    
    Args:
        key: Secret key name
        project_path: Project root directory
    """
    manager = SecretsManager(project_path)
    
    if not manager.secrets_file.exists():
        print("❌ Secrets store not initialized. Run 'devforge secrets init' first.", file=sys.stderr)
        sys.exit(1)
    
    value = manager.get_secret(key)
    if value is None:
        print(f"❌ Secret not found: {key}", file=sys.stderr)
        sys.exit(1)
    
    print(value)


def cmd_secrets_list(project_path: Optional[Path] = None) -> None:
    """
    List all secret keys.
    
    Args:
        project_path: Project root directory
    """
    manager = SecretsManager(project_path)
    
    if not manager.secrets_file.exists():
        print("ℹ️  No secrets store found. Run 'devforge secrets init' first.")
        return
    
    keys = manager.list_secrets()
    if not keys:
        print("ℹ️  No secrets stored")
        return
    
    print("Stored secrets:")
    for key in keys:
        print(f"  - {key}")


def cmd_secrets_inject(project_path: Optional[Path] = None, output_file: Optional[Path] = None) -> None:
    """
    Inject secrets into runtime environment file.
    
    Args:
        project_path: Project root directory
        output_file: Output file path (default: .env.secrets)
    """
    manager = SecretsManager(project_path)
    
    try:
        output = manager.inject_runtime_env(output_file)
        print(f"✅ Injected secrets to: {output}")
        print("⚠️  Remember to add .env.secrets to .gitignore")
    except Exception as e:
        print(f"❌ Failed to inject secrets: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_secrets_sync_github(
    repo: Optional[str] = None,
    project_path: Optional[Path] = None
) -> None:
    """
    Sync secrets to GitHub repository secrets.
    
    Args:
        repo: GitHub repository (format: owner/repo, or auto-detect from git)
        project_path: Project root directory
    """
    manager = SecretsManager(project_path)
    
    if not manager.secrets_file.exists():
        print("❌ Secrets store not initialized. Run 'devforge secrets init' first.", file=sys.stderr)
        sys.exit(1)
    
    # Import here to avoid dependency if not using GitHub sync
    try:
        from ...scripts.github_secrets import sync_to_github
    except ImportError:
        # Handle relative import for scripts
        import importlib.util
        script_path = Path(__file__).parent.parent.parent / "scripts" / "github_secrets.py"
        if not script_path.exists():
            print("❌ GitHub secrets sync script not found", file=sys.stderr)
            sys.exit(1)
        
        spec = importlib.util.spec_from_file_location("github_secrets", script_path)
        github_secrets = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(github_secrets)
        sync_to_github = github_secrets.sync_to_github
    
    try:
        sync_to_github(manager, repo)
        print("✅ Secrets synced to GitHub")
    except Exception as e:
        print(f"❌ Failed to sync secrets: {e}", file=sys.stderr)
        sys.exit(1)

