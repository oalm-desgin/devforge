"""Tests for template registry system."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import urllib.error

from src.core.registry import TemplateRegistry, TemplateEntry, get_registry
from src.core.errors import ValidationError


class TestTemplateRegistry:
    """Test TemplateRegistry functionality."""
    
    def test_registry_initialization(self, tmp_path):
        """Registry should initialize with empty templates."""
        registry_path = tmp_path / "registry.json"
        cache_dir = tmp_path / "cache"
        
        registry = TemplateRegistry(registry_path=registry_path, cache_dir=cache_dir)
        
        assert len(registry.list_templates()) == 0
        assert registry.registry_path == registry_path
        assert registry.cache_dir == cache_dir
    
    def test_registry_load_existing(self, tmp_path):
        """Registry should load existing templates from file."""
        registry_path = tmp_path / "registry.json"
        cache_dir = tmp_path / "cache"
        
        # Create existing registry
        registry_data = {
            'templates': {
                'test_template': {
                    'name': 'test_template',
                    'version': '1.0.0',
                    'description': 'Test template',
                    'url': 'https://example.com/template.template',
                    'installed': False,
                }
            }
        }
        registry_path.write_text(json.dumps(registry_data), encoding='utf-8')
        
        registry = TemplateRegistry(registry_path=registry_path, cache_dir=cache_dir)
        
        templates = registry.list_templates()
        assert len(templates) == 1
        assert templates[0].name == 'test_template'
    
    def test_registry_save(self, tmp_path):
        """Registry should save templates to file."""
        registry_path = tmp_path / "registry.json"
        cache_dir = tmp_path / "cache"
        
        registry = TemplateRegistry(registry_path=registry_path, cache_dir=cache_dir)
        
        # Add a template
        template = TemplateEntry(
            name='test',
            version='1.0.0',
            description='Test',
            url='https://example.com/test.template'
        )
        registry.templates['test'] = template
        registry._save_registry()
        
        # Verify file was created
        assert registry_path.exists()
        data = json.loads(registry_path.read_text(encoding='utf-8'))
        assert 'test' in data['templates']
    
    @patch('urllib.request.urlopen')
    def test_registry_refresh_success(self, mock_urlopen, tmp_path):
        """Registry refresh should update templates from remote."""
        registry_path = tmp_path / "registry.json"
        cache_dir = tmp_path / "cache"
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'templates': {
                'remote_template': {
                    'name': 'remote_template',
                    'version': '2.0.0',
                    'description': 'Remote template',
                    'url': 'https://example.com/remote.template',
                }
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        registry = TemplateRegistry(registry_path=registry_path, cache_dir=cache_dir)
        registry.refresh()
        
        templates = registry.list_templates()
        assert len(templates) == 1
        assert templates[0].name == 'remote_template'
        assert templates[0].version == '2.0.0'
    
    @patch('urllib.request.urlopen')
    def test_registry_refresh_invalid_format(self, mock_urlopen, tmp_path):
        """Registry refresh should fail on invalid format."""
        registry_path = tmp_path / "registry.json"
        cache_dir = tmp_path / "cache"
        
        # Mock invalid response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({'invalid': 'data'}).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        registry = TemplateRegistry(registry_path=registry_path, cache_dir=cache_dir)
        
        with pytest.raises(ValidationError, match="Invalid registry format"):
            registry.refresh()
    
    @patch('urllib.request.urlopen')
    def test_registry_refresh_network_error(self, mock_urlopen, tmp_path):
        """Registry refresh should handle network errors."""
        registry_path = tmp_path / "registry.json"
        cache_dir = tmp_path / "cache"
        
        # Mock network error
        mock_urlopen.side_effect = urllib.error.URLError("Connection failed")
        
        registry = TemplateRegistry(registry_path=registry_path, cache_dir=cache_dir)
        
        with pytest.raises(ValidationError, match="Failed to fetch registry"):
            registry.refresh()
    
    def test_get_template(self, tmp_path):
        """get_template should return template by name."""
        registry_path = tmp_path / "registry.json"
        cache_dir = tmp_path / "cache"
        
        registry = TemplateRegistry(registry_path=registry_path, cache_dir=cache_dir)
        
        template = TemplateEntry(
            name='test',
            version='1.0.0',
            description='Test',
            url='https://example.com/test.template'
        )
        registry.templates['test'] = template
        
        found = registry.get_template('test')
        assert found is not None
        assert found.name == 'test'
        
        not_found = registry.get_template('nonexistent')
        assert not_found is None
    
    @patch('urllib.request.urlopen')
    def test_install_template_success(self, mock_urlopen, tmp_path):
        """install_template should download and install template."""
        registry_path = tmp_path / "registry.json"
        cache_dir = tmp_path / "cache"
        
        # Create registry with template
        template = TemplateEntry(
            name='test_template',
            version='1.0.0',
            description='Test',
            url='https://example.com/test.template'
        )
        
        registry = TemplateRegistry(registry_path=registry_path, cache_dir=cache_dir)
        registry.templates['test_template'] = template
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.read.return_value = b'Template content: {{ PROJECT_NAME }}'
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Install template
        template_path = registry.install_template('test_template')
        
        assert template_path.exists()
        assert (template_path / 'test_template.template').exists()
        assert template.installed is True
        assert template.installed_path is not None
    
    def test_install_template_not_found(self, tmp_path):
        """install_template should fail for nonexistent template."""
        registry_path = tmp_path / "registry.json"
        cache_dir = tmp_path / "cache"
        
        registry = TemplateRegistry(registry_path=registry_path, cache_dir=cache_dir)
        
        with pytest.raises(ValidationError, match="not found in registry"):
            registry.install_template('nonexistent')
    
    @patch('urllib.request.urlopen')
    def test_install_template_validation(self, mock_urlopen, tmp_path):
        """install_template should validate template schema."""
        registry_path = tmp_path / "registry.json"
        cache_dir = tmp_path / "cache"
        
        template = TemplateEntry(
            name='test_template',
            version='1.0.0',
            description='Test',
            url='https://example.com/test.template'
        )
        
        registry = TemplateRegistry(registry_path=registry_path, cache_dir=cache_dir)
        registry.templates['test_template'] = template
        
        # Mock invalid template (unclosed Jinja2)
        mock_response = MagicMock()
        mock_response.read.return_value = b'Template with {{ unclosed variable'
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with pytest.raises(ValidationError, match="Invalid template"):
            registry.install_template('test_template', validate=True)
    
    def test_uninstall_template(self, tmp_path):
        """uninstall_template should remove installed template."""
        registry_path = tmp_path / "registry.json"
        cache_dir = tmp_path / "cache"
        
        template = TemplateEntry(
            name='test_template',
            version='1.0.0',
            description='Test',
            url='https://example.com/test.template',
            installed=True,
            installed_path=str(cache_dir / 'test_template')
        )
        
        # Create template directory
        template_dir = cache_dir / 'test_template'
        template_dir.mkdir(parents=True)
        (template_dir / 'test.template').write_text('content')
        
        registry = TemplateRegistry(registry_path=registry_path, cache_dir=cache_dir)
        registry.templates['test_template'] = template
        
        registry.uninstall_template('test_template')
        
        assert template.installed is False
        assert template.installed_path is None
        assert not template_dir.exists()
    
    def test_validate_template_valid(self, tmp_path):
        """Template validation should pass for valid templates."""
        registry_path = tmp_path / "registry.json"
        cache_dir = tmp_path / "cache"
        
        registry = TemplateRegistry(registry_path=registry_path, cache_dir=cache_dir)
        
        template_file = tmp_path / "valid.template"
        template_file.write_text("Valid template with {{ PROJECT_NAME }} variable")
        
        # Should not raise
        registry._validate_template(template_file)
    
    def test_validate_template_invalid(self, tmp_path):
        """Template validation should fail for invalid templates."""
        registry_path = tmp_path / "registry.json"
        cache_dir = tmp_path / "cache"
        
        registry = TemplateRegistry(registry_path=registry_path, cache_dir=cache_dir)
        
        # Unclosed variable
        template_file = tmp_path / "invalid.template"
        template_file.write_text("Invalid template with {{ unclosed")
        
        with pytest.raises(ValidationError, match="Invalid template"):
            registry._validate_template(template_file)


class TestRegistryCLI:
    """Test registry CLI commands."""
    
    @patch('src.cli.registry.get_registry')
    def test_cmd_registry_list_empty(self, mock_get_registry, capsys):
        """List command should show message when no templates."""
        from src.cli.registry import cmd_registry_list
        
        mock_registry = MagicMock()
        mock_registry.list_templates.return_value = []
        mock_get_registry.return_value = mock_registry
        
        cmd_registry_list()
        
        captured = capsys.readouterr()
        assert "No templates found" in captured.out
    
    @patch('src.cli.registry.get_registry')
    def test_cmd_registry_install_success(self, mock_get_registry, tmp_path):
        """Install command should install template."""
        from src.cli.registry import cmd_registry_install
        
        mock_registry = MagicMock()
        mock_registry.install_template.return_value = tmp_path / "template"
        mock_get_registry.return_value = mock_registry
        
        cmd_registry_install("test_template")
        
        mock_registry.install_template.assert_called_once_with("test_template", validate=True)
    
    @patch('src.cli.registry.get_registry')
    def test_cmd_registry_refresh_success(self, mock_get_registry, capsys):
        """Refresh command should refresh registry."""
        from src.cli.registry import cmd_registry_refresh
        
        mock_registry = MagicMock()
        mock_registry.list_templates.return_value = [MagicMock(), MagicMock()]
        mock_get_registry.return_value = mock_registry
        
        cmd_registry_refresh()
        
        mock_registry.refresh.assert_called_once_with(None)
        captured = capsys.readouterr()
        assert "refreshed successfully" in captured.out


