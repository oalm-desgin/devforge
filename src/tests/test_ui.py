"""Tests for Rich TUI interface."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Try to import UI modules (may fail if rich/typer not installed)
try:
    from src.ui.app import (
        prompt_project_name_ui,
        prompt_parent_directory_ui,
        prompt_component_toggle,
        prompt_database_engine_ui,
        show_port_preview,
        resolve_ports_ui,
    )
    UI_AVAILABLE = True
except ImportError:
    UI_AVAILABLE = False

try:
    from typer.testing import CliRunner
    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False

from src.core.config_models import ProjectConfig
from src.core.file_writer import FileWriter

pytestmark = pytest.mark.skipif(not UI_AVAILABLE, reason="rich/typer not installed")


class TestUIPrompts:
    """Test UI prompt functions."""
    
    @patch('src.ui.app.Prompt.ask')
    @patch('src.ui.app.console')
    def test_prompt_project_name_ui_valid(self, mock_console, mock_prompt):
        """Valid project name should be accepted."""
        mock_prompt.return_value = "test_project"
        
        result = prompt_project_name_ui()
        
        assert result == "test_project"
        mock_prompt.assert_called_once()
    
    @patch('src.ui.app.Prompt.ask')
    @patch('src.ui.app.console')
    def test_prompt_project_name_ui_invalid_then_valid(self, mock_console, mock_prompt):
        """Invalid then valid project name should work."""
        mock_prompt.side_effect = ["", "test_project"]
        
        result = prompt_project_name_ui()
        
        assert result == "test_project"
        assert mock_prompt.call_count == 2
    
    @patch('src.ui.app.Prompt.ask')
    @patch('src.ui.app.console')
    def test_prompt_parent_directory_ui_default(self, mock_console, mock_prompt, tmp_path):
        """Default parent directory should use current directory."""
        mock_prompt.return_value = ""
        
        result = prompt_parent_directory_ui()
        
        assert result == Path.cwd()
    
    @patch('src.ui.app.Confirm.ask')
    def test_prompt_component_toggle_true(self, mock_confirm):
        """Component toggle should return True when confirmed."""
        mock_confirm.return_value = True
        
        result = prompt_component_toggle("Frontend")
        
        assert result is True
        mock_confirm.assert_called_once()
    
    @patch('src.ui.app.Confirm.ask')
    def test_prompt_component_toggle_false(self, mock_confirm):
        """Component toggle should return False when not confirmed."""
        mock_confirm.return_value = False
        
        result = prompt_component_toggle("Backend")
        
        assert result is False
        mock_confirm.assert_called_once()
    
    @patch('src.ui.app.Prompt.ask')
    @patch('src.ui.app.console')
    def test_prompt_database_engine_ui_postgres(self, mock_console, mock_prompt):
        """Database engine selection should work for PostgreSQL."""
        mock_prompt.return_value = "1"
        
        result = prompt_database_engine_ui()
        
        assert result == "postgres"
    
    @patch('src.ui.app.Prompt.ask')
    @patch('src.ui.app.console')
    def test_prompt_database_engine_ui_mongo(self, mock_console, mock_prompt):
        """Database engine selection should work for MongoDB."""
        mock_prompt.return_value = "2"
        
        result = prompt_database_engine_ui()
        
        assert result == "mongo"
    
    @patch('src.ui.app.Prompt.ask')
    @patch('src.ui.app.console')
    def test_prompt_database_engine_ui_redis(self, mock_console, mock_prompt):
        """Database engine selection should work for Redis."""
        mock_prompt.return_value = "3"
        
        result = prompt_database_engine_ui()
        
        assert result == "redis"


class TestUIFunctions:
    """Test UI utility functions."""
    
    @patch('src.ui.app.console')
    def test_show_port_preview(self, mock_console):
        """Port preview should display correctly."""
        config = {
            "frontend": True,
            "backend": True,
            "database": True,
            "frontend_port": 3000,
            "backend_port": 8000,
            "database_port": 5432,
            "database_stack": "postgres",
        }
        
        show_port_preview(config)
        
        # Should have called console.print
        assert mock_console.print.called
    
    @patch('src.ui.app.is_port_free')
    @patch('src.ui.app.find_free_port')
    def test_resolve_ports_ui(self, mock_find_port, mock_is_free):
        """Port resolution should work correctly."""
        mock_is_free.return_value = True
        
        config = {
            "frontend": True,
            "backend": True,
            "database": True,
            "database_stack": "postgres",
        }
        
        result = resolve_ports_ui(config)
        
        assert "frontend_port" in result
        assert "backend_port" in result
        assert "database_port" in result


class TestUICLI:
    """Test UI CLI command."""
    
    def test_ui_command_help(self):
        """UI command should show help."""
        runner = CliRunner()
        result = runner.invoke(ui, ["--help"])
        
        assert result.exit_code == 0
        assert "Launch interactive TUI" in result.stdout
    
    @patch('src.ui.app.run_wizard')
    @patch('src.ui.app.Confirm.ask')
    @patch('src.ui.app.ProjectGenerator')
    @patch('src.ui.app.FileWriter')
    def test_ui_command_dry_run(
        self,
        mock_file_writer_class,
        mock_generator_class,
        mock_confirm,
        mock_wizard,
        tmp_path
    ):
        """UI command with dry-run should not create files."""
        mock_file_writer = MagicMock()
        mock_file_writer_class.return_value = mock_file_writer
        mock_file_writer.get_operations_summary.return_value = []
        
        config = ProjectConfig(
            project_name="test",
            destination_path=tmp_path / "test",
        )
        mock_wizard.return_value = config
        
        runner = CliRunner()
        result = runner.invoke(ui, ["--dry-run"])
        
        # Should not call generator.generate
        assert not mock_generator_class.called or not hasattr(mock_generator_class.return_value, 'generate')
    
    @patch('src.ui.app.run_wizard')
    @patch('src.ui.app.Confirm.ask')
    def test_ui_command_cancelled(self, mock_confirm, mock_wizard, tmp_path):
        """UI command should handle cancellation."""
        mock_confirm.return_value = False
        
        config = ProjectConfig(
            project_name="test",
            destination_path=tmp_path / "test",
        )
        mock_wizard.return_value = config
        
        runner = CliRunner()
        result = runner.invoke(ui, [])
        
        # Should exit with code 0 (cancelled)
        assert result.exit_code == 0

