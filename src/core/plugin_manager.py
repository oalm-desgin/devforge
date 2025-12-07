"""Plugin management system for DevForge."""

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Protocol, runtime_checkable

from .errors import ValidationError

logger = logging.getLogger(__name__)


@runtime_checkable
class PluginProtocol(Protocol):
    """Protocol that plugins must implement."""
    
    name: str
    version: str
    
    def register_templates(self) -> Dict[str, Path]:
        """
        Register templates provided by this plugin.
        
        Returns:
            Dictionary mapping template names to template file paths
        """
        ...


class PluginManager:
    """Manages plugin discovery and registration."""
    
    def __init__(self, plugins_dir: Path):
        """
        Initialize plugin manager.
        
        Args:
            plugins_dir: Directory containing plugin modules
        """
        self.plugins_dir = Path(plugins_dir).resolve()
        self.plugins: Dict[str, PluginProtocol] = {}
        self.plugin_templates: Dict[str, Dict[str, Path]] = {}
    
    def discover_plugins(self) -> List[str]:
        """
        Discover all plugins in the plugins directory.
        
        Returns:
            List of discovered plugin names
        """
        if not self.plugins_dir.exists():
            logger.debug(f"Plugins directory does not exist: {self.plugins_dir}")
            return []
        
        discovered: List[str] = []
        
        # Scan for Python modules in plugins directory
        for item in self.plugins_dir.iterdir():
            # Skip non-Python files and special files
            if item.is_file() and item.suffix == '.py' and not item.name.startswith('_'):
                plugin_name = item.stem
                try:
                    self._load_plugin(plugin_name)
                    discovered.append(plugin_name)
                except ValidationError as e:
                    # Log and skip invalid plugins during discovery
                    logger.warning(f"Invalid plugin '{plugin_name}': {e}")
                except Exception as e:
                    logger.warning(f"Failed to load plugin '{plugin_name}': {e}")
            elif item.is_dir() and not item.name.startswith('_'):
                # Check if directory has __init__.py
                init_file = item / '__init__.py'
                if init_file.exists():
                    plugin_name = item.name
                    try:
                        self._load_plugin(plugin_name)
                        discovered.append(plugin_name)
                    except Exception as e:
                        logger.warning(f"Failed to load plugin '{plugin_name}': {e}")
        
        logger.info(f"Discovered {len(discovered)} plugin(s): {', '.join(discovered)}")
        return discovered
    
    def _load_plugin(self, plugin_name: str) -> None:
        """
        Load a plugin module.
        
        Args:
            plugin_name: Name of the plugin module to load
            
        Raises:
            ValidationError: If plugin is invalid
        """
        try:
            # Import the plugin module
            module_path = self.plugins_dir / f"{plugin_name}.py"
            if module_path.exists():
                spec = importlib.util.spec_from_file_location(
                    f"src.plugins.{plugin_name}",
                    module_path
                )
            else:
                # Try as a package
                module_path = self.plugins_dir / plugin_name / "__init__.py"
                if not module_path.exists():
                    raise ValidationError(f"Plugin module not found: {plugin_name}")
                spec = importlib.util.spec_from_file_location(
                    f"src.plugins.{plugin_name}",
                    module_path
                )
            
            if spec is None or spec.loader is None:
                raise ValidationError(f"Could not load plugin: {plugin_name}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Validate plugin implements required interface
            if not isinstance(module, PluginProtocol):
                # Check if module has a plugin class or object
                plugin_obj = getattr(module, 'plugin', None)
                if plugin_obj is None:
                    # Try to use the module itself as the plugin
                    plugin_obj = module
                
                if not isinstance(plugin_obj, PluginProtocol):
                    raise ValidationError(
                        f"Plugin '{plugin_name}' does not implement PluginProtocol. "
                        f"Required: name, version, register_templates()"
                    )
                
                plugin = plugin_obj
            else:
                plugin = module
            
            # Validate required attributes
            if not hasattr(plugin, 'name') or not isinstance(plugin.name, str):
                raise ValidationError(f"Plugin '{plugin_name}' missing required 'name' attribute")
            
            if not hasattr(plugin, 'version') or not isinstance(plugin.version, str):
                raise ValidationError(f"Plugin '{plugin_name}' missing required 'version' attribute")
            
            if not hasattr(plugin, 'register_templates') or not callable(plugin.register_templates):
                raise ValidationError(
                    f"Plugin '{plugin_name}' missing required 'register_templates()' method"
                )
            
            # Register templates
            try:
                templates = plugin.register_templates()
                if not isinstance(templates, dict):
                    raise ValidationError(
                        f"Plugin '{plugin_name}' register_templates() must return a dict"
                    )
                
                # Validate template paths
                for template_name, template_path in templates.items():
                    if not isinstance(template_path, Path):
                        template_path = Path(template_path)
                    
                    if not template_path.exists():
                        logger.warning(
                            f"Plugin '{plugin.name}' template '{template_name}' not found: {template_path}"
                        )
                
                self.plugin_templates[plugin.name] = templates
                self.plugins[plugin.name] = plugin
                
                logger.info(
                    f"Loaded plugin '{plugin.name}' v{plugin.version} "
                    f"with {len(templates)} template(s)"
                )
            except Exception as e:
                raise ValidationError(f"Plugin '{plugin.name}' register_templates() failed: {e}")
        
        except ImportError as e:
            raise ValidationError(f"Failed to import plugin '{plugin_name}': {e}")
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Unexpected error loading plugin '{plugin_name}': {e}")
    
    def get_plugin(self, name: str) -> Optional[PluginProtocol]:
        """
        Get a plugin by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> Dict[str, PluginProtocol]:
        """
        Get all loaded plugins.
        
        Returns:
            Dictionary mapping plugin names to plugin instances
        """
        return self.plugins.copy()
    
    def get_plugin_templates(self, plugin_name: Optional[str] = None) -> Dict[str, Path]:
        """
        Get templates from plugins.
        
        Args:
            plugin_name: Optional plugin name to filter by
            
        Returns:
            Dictionary mapping template names to template paths
        """
        if plugin_name:
            return self.plugin_templates.get(plugin_name, {}).copy()
        
        # Merge all plugin templates
        all_templates: Dict[str, Path] = {}
        for templates in self.plugin_templates.values():
            all_templates.update(templates)
        
        return all_templates

