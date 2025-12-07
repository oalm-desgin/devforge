"""CLI commands for template registry management."""

import sys
from pathlib import Path
from typing import Optional

from ..core.registry import get_registry, TemplateRegistry
from ..core.errors import ValidationError


def cmd_registry_list() -> None:
    """List all available templates in the registry."""
    registry = get_registry()
    templates = registry.list_templates()
    
    if not templates:
        print("No templates found in registry.")
        print("Run 'devforge registry refresh' to update the registry.")
        return
    
    print("Available Templates:")
    print("=" * 80)
    
    for template in templates:
        status = "[INSTALLED]" if template.installed else "[AVAILABLE]"
        print(f"\n{status} {template.name} (v{template.version})")
        if template.description:
            print(f"  Description: {template.description}")
        if template.author:
            print(f"  Author: {template.author}")
        if template.tags:
            print(f"  Tags: {', '.join(template.tags)}")
        if template.installed_path:
            print(f"  Installed at: {template.installed_path}")
    
    print("\n" + "=" * 80)


def cmd_registry_install(template_name: str, validate: bool = True) -> None:
    """
    Install a template from the registry.
    
    Args:
        template_name: Name of template to install
        validate: Whether to validate template schema
    """
    registry = get_registry()
    
    try:
        template_path = registry.install_template(template_name, validate=validate)
        print(f"✅ Template '{template_name}' installed successfully!")
        print(f"   Location: {template_path}")
    except ValidationError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_registry_refresh(registry_url: Optional[str] = None) -> None:
    """
    Refresh the registry from remote URL.
    
    Args:
        registry_url: Optional URL to fetch registry from
    """
    registry = get_registry()
    
    try:
        registry.refresh(registry_url)
        print("✅ Registry refreshed successfully!")
        print(f"   {len(registry.list_templates())} templates available")
    except ValidationError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_registry_uninstall(template_name: str) -> None:
    """
    Uninstall a template.
    
    Args:
        template_name: Name of template to uninstall
    """
    registry = get_registry()
    
    try:
        registry.uninstall_template(template_name)
        print(f"✅ Template '{template_name}' uninstalled successfully!")
    except ValidationError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


