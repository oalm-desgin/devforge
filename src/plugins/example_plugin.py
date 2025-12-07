"""Example plugin for DevForge.

This is a reference implementation showing how to create a custom plugin.
"""

from pathlib import Path

# Required plugin attributes
name: str = "example_plugin"
version: str = "1.0.0"


def register_templates() -> dict[str, Path]:
    """
    Register templates provided by this plugin.
    
    Returns:
        Dictionary mapping template names to template file paths
    """
    plugin_dir = Path(__file__).parent
    
    return {
        "example_config.py": plugin_dir / "templates" / "example_config.py.template",
        "example_utils.py": plugin_dir / "templates" / "example_utils.py.template",
    }


