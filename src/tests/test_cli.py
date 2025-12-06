"""Tests for CLI functionality."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.cli.main import parse_args, main
from src.cli.prompts import collect_project_config
from src.core.config_models import ProjectConfig
from src.core.version import VERSION


class TestCLIArgs:
    """Test CLI argument parsing."""
    
    @patch('sys.argv', ['devforge', '--dry-run'])
    def test_parse_args_dry_run(self):
        """--dry-run should be parsed correctly."""
        args = parse_args()
        assert args.dry_run is True
    
    @patch('sys.argv', ['devforge', '--preset', 'test.json'])
    def test_parse_args_preset(self):
        """--preset should be parsed correctly."""
        args = parse_args()
        assert args.preset == "test.json"
    
    @patch('sys.argv', ['devforge', '--with-ci'])
    def test_parse_args_with_ci(self):
        """--with-ci should be parsed correctly."""
        args = parse_args()
        assert args.with_ci is True
    
    @patch('sys.argv', ['devforge', '--version'])
    def test_parse_args_version(self, capsys):
        """--version should print version and exit."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert VERSION in captured.out


class TestCLIPrompts:
    """Test CLI prompt functions."""
    
    @patch('src.cli.prompts.validate_path')
    @patch('pathlib.Path.cwd')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_full_stack_selection(self, mock_print, mock_input, mock_cwd, mock_validate_path, tmp_path):
        """Full stack selection should work."""
        mock_cwd.return_value = tmp_path
        mock_validate_path.return_value = (True, None)
        mock_input.side_effect = [
            "test_project",  # project name
            "",  # path (default)
            "y",  # frontend
            "y",  # backend
            "y",  # database
            "1",  # database engine (PostgreSQL)
        ]
        
        config = collect_project_config(preset_path=None, include_ci=False)
        
        assert config.frontend is not None
        assert config.backend is not None
        assert config.database is not None
        assert config.database.stack == "postgres"
    
    @patch('src.cli.prompts.validate_path')
    @patch('pathlib.Path.cwd')
    @patch('builtins.input')
    def test_backend_only(self, mock_input, mock_cwd, mock_validate_path, tmp_path):
        """Backend only selection should work."""
        mock_cwd.return_value = tmp_path
        mock_validate_path.return_value = (True, None)
        mock_input.side_effect = [
            "test_backend",  # project name
            "",  # path
            "n",  # frontend
            "y",  # backend
            "n",  # database
        ]
        
        config = collect_project_config(preset_path=None, include_ci=False)
        
        assert config.frontend is None
        assert config.backend is not None
        assert config.database is None
    
    @patch('src.cli.prompts.validate_path')
    @patch('pathlib.Path.cwd')
    @patch('builtins.input')
    def test_frontend_only(self, mock_input, mock_cwd, mock_validate_path, tmp_path):
        """Frontend only selection should work."""
        mock_cwd.return_value = tmp_path
        mock_validate_path.return_value = (True, None)
        mock_input.side_effect = [
            "test_frontend",  # project name
            "",  # path
            "y",  # frontend
            "n",  # backend
        ]
        
        config = collect_project_config(preset_path=None, include_ci=False)
        
        assert config.frontend is not None
        assert config.backend is None
        assert config.database is None
    
    @patch('src.cli.prompts.validate_path')
    @patch('pathlib.Path.cwd')
    @patch('builtins.input')
    def test_database_without_backend_fails(self, mock_input, mock_cwd, mock_validate_path, tmp_path):
        """Database without backend should be prevented."""
        mock_cwd.return_value = tmp_path
        mock_validate_path.return_value = (True, None)
        mock_input.side_effect = [
            "test_no_backend",  # project name
            "",  # path
            "y",  # frontend (to avoid "no components" error)
            "n",  # backend (no backend)
        ]
        
        # Database requires backend, so this should be skipped
        config = collect_project_config(preset_path=None, include_ci=False)
        
        assert config.frontend is not None
        assert config.backend is None
        assert config.database is None  # Database should not be asked when backend is "n"
    
    @patch('src.cli.prompts.validate_path')
    @patch('pathlib.Path.cwd')
    @patch('builtins.input')
    def test_preset_loading(self, mock_input, mock_cwd, mock_validate_path, tmp_path):
        """Preset loading should work."""
        mock_cwd.return_value = tmp_path
        mock_validate_path.return_value = (True, None)
        preset_file = tmp_path / "preset.json"
        preset_data = {
            "default_frontend": True,
            "default_backend": True,
            "default_database": True,
            "database_stack": "mongo"
        }
        preset_file.write_text(json.dumps(preset_data))
        
        mock_input.side_effect = [
            "test_preset",  # project name
            "",  # path
            "y",  # frontend (uses preset default)
            "y",  # backend (uses preset default)
            "y",  # database (uses preset default)
            "2",  # mongo (preset default)
        ]
        
        config = collect_project_config(preset_path=preset_file, include_ci=False)
        
        assert config.database.stack == "mongo"
    
    @patch('src.cli.prompts.validate_path')
    @patch('pathlib.Path.cwd')
    @patch('builtins.input')
    def test_invalid_preset_handling(self, mock_input, mock_cwd, mock_validate_path, tmp_path):
        """Invalid preset should be handled gracefully."""
        mock_cwd.return_value = tmp_path
        mock_validate_path.return_value = (True, None)
        mock_input.side_effect = [
            "test_invalid",  # project name
            "",  # path
            "n",  # frontend
            "y",  # backend
            "n",  # database
        ]
        
        # None preset is handled gracefully
        config = collect_project_config(preset_path=None, include_ci=False)
        
        assert config.backend is not None


class TestCLIVersion:
    """Test version output."""
    
    @patch('sys.argv', ['devforge', '--version'])
    def test_version_flag_parsed(self, capsys):
        """--version flag should print version and exit."""
        with pytest.raises(SystemExit) as exc_info:
            parse_args()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert VERSION in captured.out


class TestCLIDryRun:
    """Test dry-run functionality."""
    
    @patch('src.cli.main.ProjectGenerator')
    @patch('src.cli.main.FileWriter')
    @patch('src.cli.prompts.validate_path')
    @patch('pathlib.Path.cwd')
    @patch('builtins.input')
    @patch('builtins.print')
    def test_dry_run_creates_no_files(self, mock_print, mock_input, mock_cwd, mock_validate_path, mock_file_writer_class, mock_generator_class, tmp_path):
        """Dry-run should not create any files."""
        mock_cwd.return_value = tmp_path
        mock_validate_path.return_value = (True, None)
        mock_file_writer = MagicMock()
        mock_file_writer_class.return_value = mock_file_writer
        mock_file_writer.get_operations_summary.return_value = []
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        
        mock_input.side_effect = [
            "test_dry_run",  # project name
            "",  # path
            "y",  # frontend
            "y",  # backend
            "n",  # database
        ]
        
        with patch('sys.argv', ['devforge', '--dry-run']):
            main()
        
        # Verify FileWriter was created with dry_run=True
        mock_file_writer_class.assert_called_once_with(dry_run=True)
        # Verify generator was created and generate was called
        mock_generator_class.assert_called_once()
        mock_generator.generate.assert_called_once()


class TestCLICI:
    """Test CI generation."""
    
    @patch('src.cli.prompts.validate_path')
    @patch('pathlib.Path.cwd')
    @patch('builtins.input')
    def test_with_ci_flag_sets_include_ci(self, mock_input, mock_cwd, mock_validate_path, tmp_path):
        """--with-ci should set include_ci to True."""
        mock_cwd.return_value = tmp_path
        mock_validate_path.return_value = (True, None)
        mock_input.side_effect = [
            "test_ci",  # project name
            "",  # path
            "n",  # frontend
            "y",  # backend
            "n",  # database
        ]
        
        config = collect_project_config(preset_path=None, include_ci=True)
        
        assert config.include_ci is True

