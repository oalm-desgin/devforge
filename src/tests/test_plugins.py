"""Tests for plugin system."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.plugin_manager import PluginManager, PluginProtocol
from src.core.errors import ValidationError


class TestPluginManager:
    """Test PluginManager functionality."""
    
    def test_discover_plugins_empty_directory(self, tmp_path):
        """Discover should return empty list when no plugins exist."""
        manager = PluginManager(tmp_path)
        plugins = manager.discover_plugins()
        assert plugins == []
        assert len(manager.get_all_plugins()) == 0
    
    def test_discover_plugins_valid_plugin(self, tmp_path):
        """Discover should load valid plugin."""
        # Create a valid plugin
        plugin_file = tmp_path / "test_plugin.py"
        plugin_file.write_text('''
from pathlib import Path

name = "test_plugin"
version = "1.0.0"

def register_templates():
    return {"test.template": Path(__file__).parent / "test.template"}
''')
        
        # Create template file
        template_file = tmp_path / "test.template"
        template_file.write_text("Test template")
        
        manager = PluginManager(tmp_path)
        plugins = manager.discover_plugins()
        
        assert "test_plugin" in plugins
        assert len(manager.get_all_plugins()) == 1
        plugin = manager.get_plugin("test_plugin")
        assert plugin is not None
        assert plugin.name == "test_plugin"
        assert plugin.version == "1.0.0"
    
    def test_discover_plugins_missing_name(self, tmp_path):
        """Plugin without name should be skipped during discovery."""
        plugin_file = tmp_path / "bad_plugin.py"
        plugin_file.write_text('''
version = "1.0.0"

def register_templates():
    return {}
''')
        
        manager = PluginManager(tmp_path)
        plugins = manager.discover_plugins()
        # Invalid plugins are skipped, not raised
        assert len(plugins) == 0
        # But _load_plugin should raise ValidationError
        with pytest.raises(ValidationError, match="does not implement PluginProtocol"):
            manager._load_plugin("bad_plugin")
    
    def test_discover_plugins_missing_version(self, tmp_path):
        """Plugin without version should be skipped during discovery."""
        plugin_file = tmp_path / "bad_plugin.py"
        plugin_file.write_text('''
name = "bad_plugin"

def register_templates():
    return {}
''')
        
        manager = PluginManager(tmp_path)
        plugins = manager.discover_plugins()
        assert len(plugins) == 0
        # But _load_plugin should raise ValidationError
        with pytest.raises(ValidationError, match="does not implement PluginProtocol"):
            manager._load_plugin("bad_plugin")
    
    def test_discover_plugins_missing_register_templates(self, tmp_path):
        """Plugin without register_templates should be skipped during discovery."""
        plugin_file = tmp_path / "bad_plugin.py"
        plugin_file.write_text('''
name = "bad_plugin"
version = "1.0.0"
''')
        
        manager = PluginManager(tmp_path)
        plugins = manager.discover_plugins()
        assert len(plugins) == 0
        # But _load_plugin should raise ValidationError
        with pytest.raises(ValidationError, match="does not implement PluginProtocol"):
            manager._load_plugin("bad_plugin")
    
    def test_discover_plugins_invalid_register_templates_return(self, tmp_path):
        """Plugin with invalid register_templates return should be skipped."""
        plugin_file = tmp_path / "bad_plugin.py"
        plugin_file.write_text('''
name = "bad_plugin"
version = "1.0.0"

def register_templates():
    return "not a dict"
''')
        
        manager = PluginManager(tmp_path)
        plugins = manager.discover_plugins()
        assert len(plugins) == 0
        # But _load_plugin should raise ValidationError
        with pytest.raises(ValidationError, match="must return a dict"):
            manager._load_plugin("bad_plugin")
    
    def test_get_plugin_templates(self, tmp_path):
        """get_plugin_templates should return registered templates."""
        plugin_file = tmp_path / "test_plugin.py"
        template_file = tmp_path / "test.template"
        template_file.write_text("Test")
        
        plugin_file.write_text('''
from pathlib import Path

name = "test_plugin"
version = "1.0.0"

def register_templates():
    return {"test.template": Path(__file__).parent / "test.template"}
''')
        
        manager = PluginManager(tmp_path)
        manager.discover_plugins()
        
        templates = manager.get_plugin_templates("test_plugin")
        assert "test.template" in templates
        assert templates["test.template"].exists()
    
    def test_get_plugin_templates_all(self, tmp_path):
        """get_plugin_templates without plugin name should return all templates."""
        # Create two plugins
        plugin1_file = tmp_path / "plugin1.py"
        template1 = tmp_path / "template1.template"
        template1.write_text("Template 1")
        plugin1_file.write_text('''
from pathlib import Path

name = "plugin1"
version = "1.0.0"

def register_templates():
    return {"template1": Path(__file__).parent / "template1.template"}
''')
        
        plugin2_file = tmp_path / "plugin2.py"
        template2 = tmp_path / "template2.template"
        template2.write_text("Template 2")
        plugin2_file.write_text('''
from pathlib import Path

name = "plugin2"
version = "1.0.0"

def register_templates():
    return {"template2": Path(__file__).parent / "template2.template"}
''')
        
        manager = PluginManager(tmp_path)
        manager.discover_plugins()
        
        all_templates = manager.get_plugin_templates()
        assert "template1" in all_templates
        assert "template2" in all_templates
        assert len(all_templates) == 2
    
    def test_get_plugin_nonexistent(self, tmp_path):
        """get_plugin should return None for nonexistent plugin."""
        manager = PluginManager(tmp_path)
        assert manager.get_plugin("nonexistent") is None


class TestPluginIntegration:
    """Test plugin integration with ProjectGenerator."""
    
    def test_project_generator_with_plugins(self, tmp_path):
        """ProjectGenerator should discover plugins when plugins_dir provided."""
        from src.core.project_generator import ProjectGenerator
        from src.core.file_writer import FileWriter
        
        # Create plugin
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        plugin_file = plugins_dir / "test_plugin.py"
        template_file = plugins_dir / "test.template"
        template_file.write_text("Plugin template: {{ PROJECT_NAME }}")
        
        plugin_file.write_text('''
from pathlib import Path

name = "test_plugin"
version = "1.0.0"

def register_templates():
    return {"test.template": Path(__file__).parent / "test.template"}
''')
        
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        file_writer = FileWriter(dry_run=True)
        generator = ProjectGenerator(templates_dir, file_writer, plugins_dir)
        
        # Plugin manager should be initialized
        assert generator.plugin_manager is not None
        assert len(generator.plugin_manager.get_all_plugins()) == 1
    
    def test_project_generator_without_plugins(self, tmp_path):
        """ProjectGenerator should work without plugins_dir."""
        from src.core.project_generator import ProjectGenerator
        from src.core.file_writer import FileWriter
        
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        file_writer = FileWriter(dry_run=True)
        generator = ProjectGenerator(templates_dir, file_writer)
        
        # Plugin manager should be None
        assert generator.plugin_manager is None

