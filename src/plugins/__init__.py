"""Plugin system for DevForge."""

from pathlib import Path
from typing import Optional

from ..core.plugin_manager import PluginManager

# Default plugins directory
_PLUGINS_DIR = Path(__file__).parent

# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager(plugins_dir: Optional[Path] = None) -> PluginManager:
    """
    Get or create the global plugin manager instance.
    
    Args:
        plugins_dir: Optional custom plugins directory
        
    Returns:
        PluginManager instance
    """
    global _plugin_manager
    
    if _plugin_manager is None:
        if plugins_dir is None:
            plugins_dir = _PLUGINS_DIR
        _plugin_manager = PluginManager(plugins_dir)
        _plugin_manager.discover_plugins()
    
    return _plugin_manager


def discover_plugins(plugins_dir: Optional[Path] = None) -> list[str]:
    """
    Discover all available plugins.
    
    Args:
        plugins_dir: Optional custom plugins directory
        
    Returns:
        List of discovered plugin names
    """
    manager = get_plugin_manager(plugins_dir)
    return list(manager.get_all_plugins().keys())


