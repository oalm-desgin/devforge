"""Remote template registry management for DevForge."""

import json
import logging
import shutil
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from .errors import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class TemplateEntry:
    """Entry in the template registry."""
    name: str
    version: str
    description: str
    url: str
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    installed: bool = False
    installed_path: Optional[str] = None
    last_updated: Optional[str] = None


class TemplateRegistry:
    """Manages remote template registry."""
    
    def __init__(self, registry_path: Optional[Path] = None, cache_dir: Optional[Path] = None):
        """
        Initialize template registry.
        
        Args:
            registry_path: Path to registry JSON file (default: ~/.devforge/registry.json)
            cache_dir: Directory to cache downloaded templates (default: ~/.devforge/templates)
        """
        if registry_path is None:
            home = Path.home()
            devforge_dir = home / ".devforge"
            devforge_dir.mkdir(exist_ok=True)
            registry_path = devforge_dir / "registry.json"
        
        if cache_dir is None:
            home = Path.home()
            devforge_dir = home / ".devforge"
            cache_dir = devforge_dir / "templates"
        
        self.registry_path = Path(registry_path)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.templates: Dict[str, TemplateEntry] = {}
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load registry from disk."""
        if not self.registry_path.exists():
            self.templates = {}
            return
        
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.templates = {
                name: TemplateEntry(**entry_data)
                for name, entry_data in data.get('templates', {}).items()
            }
            logger.debug(f"Loaded {len(self.templates)} templates from registry")
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to load registry: {e}. Starting with empty registry.")
            self.templates = {}
    
    def _save_registry(self) -> None:
        """Save registry to disk."""
        data = {
            'templates': {
                name: asdict(entry)
                for name, entry in self.templates.items()
            },
            'last_updated': datetime.now().isoformat(),
        }
        
        try:
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved registry to {self.registry_path}")
        except OSError as e:
            raise ValidationError(f"Failed to save registry: {e}")
    
    def refresh(self, registry_url: Optional[str] = None) -> None:
        """
        Refresh registry from remote URL.
        
        Args:
            registry_url: Optional URL to fetch registry from. If None, uses default.
            
        Raises:
            ValidationError: If refresh fails
        """
        if registry_url is None:
            # Default registry URL (can be overridden)
            registry_url = "https://raw.githubusercontent.com/yourusername/devforge-registry/main/registry.json"
        
        logger.info(f"Refreshing registry from {registry_url}")
        
        try:
            with urllib.request.urlopen(registry_url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Validate registry schema
            if not isinstance(data, dict) or 'templates' not in data:
                raise ValidationError("Invalid registry format: missing 'templates' key")
            
            # Update templates
            updated_count = 0
            for name, entry_data in data['templates'].items():
                if not isinstance(entry_data, dict):
                    logger.warning(f"Skipping invalid template entry: {name}")
                    continue
                
                # Validate required fields
                required_fields = ['name', 'version', 'description', 'url']
                if not all(field in entry_data for field in required_fields):
                    logger.warning(f"Skipping template '{name}': missing required fields")
                    continue
                
                # Create or update entry
                entry = TemplateEntry(
                    name=entry_data['name'],
                    version=entry_data.get('version', '1.0.0'),
                    description=entry_data.get('description', ''),
                    url=entry_data['url'],
                    author=entry_data.get('author'),
                    tags=entry_data.get('tags', []),
                    installed=self.templates.get(name, TemplateEntry(
                        name=name, version='', description='', url=''
                    )).installed,
                    installed_path=self.templates.get(name, TemplateEntry(
                        name=name, version='', description='', url=''
                    )).installed_path,
                    last_updated=datetime.now().isoformat(),
                )
                
                self.templates[name] = entry
                updated_count += 1
            
            self._save_registry()
            logger.info(f"Registry refreshed: {updated_count} templates available")
        
        except urllib.error.URLError as e:
            raise ValidationError(f"Failed to fetch registry: {e}")
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in registry: {e}")
        except Exception as e:
            raise ValidationError(f"Unexpected error refreshing registry: {e}")
    
    def list_templates(self) -> List[TemplateEntry]:
        """
        List all available templates.
        
        Returns:
            List of template entries
        """
        return list(self.templates.values())
    
    def get_template(self, name: str) -> Optional[TemplateEntry]:
        """
        Get a template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template entry or None if not found
        """
        return self.templates.get(name)
    
    def install_template(self, name: str, validate: bool = True) -> Path:
        """
        Install a template from the registry.
        
        Args:
            name: Template name
            validate: Whether to validate template schema
            
        Returns:
            Path to installed template directory
            
        Raises:
            ValidationError: If template not found or installation fails
        """
        template = self.templates.get(name)
        if not template:
            raise ValidationError(f"Template '{name}' not found in registry")
        
        logger.info(f"Installing template '{name}' v{template.version}")
        
        # Check if already installed
        if template.installed and template.installed_path:
            installed_path = Path(template.installed_path)
            if installed_path.exists():
                logger.info(f"Template '{name}' already installed at {installed_path}")
                return installed_path
        
        # Download template
        try:
            template_dir = self.cache_dir / name
            template_dir.mkdir(parents=True, exist_ok=True)
            
            # Download from URL
            logger.info(f"Downloading template from {template.url}")
            with urllib.request.urlopen(template.url, timeout=30) as response:
                content = response.read().decode('utf-8')
            
            # Save template file
            template_file = template_dir / f"{name}.template"
            template_file.write_text(content, encoding='utf-8')
            
            # Validate template if requested
            if validate:
                self._validate_template(template_file)
            
            # Update registry entry
            template.installed = True
            template.installed_path = str(template_dir)
            template.last_updated = datetime.now().isoformat()
            self._save_registry()
            
            logger.info(f"Template '{name}' installed to {template_dir}")
            return template_dir
        
        except urllib.error.URLError as e:
            raise ValidationError(f"Failed to download template: {e}")
        except Exception as e:
            # Clean up on error
            if template_dir.exists():
                shutil.rmtree(template_dir)
            raise ValidationError(f"Failed to install template: {e}")
    
    def uninstall_template(self, name: str) -> None:
        """
        Uninstall a template.
        
        Args:
            name: Template name
            
        Raises:
            ValidationError: If template not found
        """
        template = self.templates.get(name)
        if not template:
            raise ValidationError(f"Template '{name}' not found in registry")
        
        if not template.installed or not template.installed_path:
            logger.info(f"Template '{name}' is not installed")
            return
        
        try:
            template_dir = Path(template.installed_path)
            if template_dir.exists():
                shutil.rmtree(template_dir)
                logger.info(f"Removed template directory: {template_dir}")
            
            template.installed = False
            template.installed_path = None
            self._save_registry()
            
            logger.info(f"Template '{name}' uninstalled")
        except Exception as e:
            raise ValidationError(f"Failed to uninstall template: {e}")
    
    def _validate_template(self, template_path: Path) -> None:
        """
        Validate a template file.
        
        Args:
            template_path: Path to template file
            
        Raises:
            ValidationError: If template is invalid
        """
        if not template_path.exists():
            raise ValidationError(f"Template file not found: {template_path}")
        
        content = template_path.read_text(encoding='utf-8')
        
        # Basic validation: check for Jinja2 syntax
        # This is a simple check - more sophisticated validation could be added
        if '{{' in content and '}}' not in content:
            raise ValidationError("Invalid template: unclosed Jinja2 variable")
        
        if '{%' in content and '%}' not in content:
            raise ValidationError("Invalid template: unclosed Jinja2 block")
        
        logger.debug(f"Template validation passed: {template_path}")


def get_registry(registry_path: Optional[Path] = None) -> TemplateRegistry:
    """
    Get or create the global registry instance.
    
    Args:
        registry_path: Optional custom registry path
        
    Returns:
        TemplateRegistry instance
    """
    return TemplateRegistry(registry_path=registry_path)


