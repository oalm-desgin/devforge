"""Tests for port resolution logic."""

import pytest
from pathlib import Path

from src.core.config_models import ProjectConfig, FrontendConfig, BackendConfig, DatabaseConfig
from src.core.project_generator import ProjectGenerator
from src.core.file_writer import FileWriter
from src.core.validators import is_port_free


class TestPortResolution:
    """Test automatic port resolution."""
    
    def test_frontend_port_occupied(self, tmp_path, monkeypatch):
        """Frontend port 3000 occupied should use 3001."""
        occupied_ports = {3000}
        
        def mock_is_port_free(port):
            return port not in occupied_ports
        
        monkeypatch.setattr("src.core.project_generator.is_port_free", mock_is_port_free)
        monkeypatch.setattr("src.core.validators.is_port_free", mock_is_port_free)
        
        config = ProjectConfig(
            project_name="test",
            destination_path=tmp_path / "test",
            frontend=FrontendConfig(port=3000),
        )
        
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = ProjectGenerator(templates_dir, FileWriter(dry_run=True))
        generator._resolve_ports(config)
        
        assert config.frontend.port == 3001
    
    def test_backend_port_occupied(self, tmp_path, monkeypatch):
        """Backend port 8000 occupied should use 8001."""
        occupied_ports = {8000}
        
        def mock_is_port_free(port):
            return port not in occupied_ports
        
        monkeypatch.setattr("src.core.project_generator.is_port_free", mock_is_port_free)
        monkeypatch.setattr("src.core.validators.is_port_free", mock_is_port_free)
        
        config = ProjectConfig(
            project_name="test",
            destination_path=tmp_path / "test",
            backend=BackendConfig(port=8000),
        )
        
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = ProjectGenerator(templates_dir, FileWriter(dry_run=True))
        generator._resolve_ports(config)
        
        assert config.backend.port == 8001
    
    def test_postgres_port_occupied(self, tmp_path, monkeypatch):
        """PostgreSQL port 5432 occupied should use 5433."""
        occupied_ports = {5432}
        
        def mock_is_port_free(port):
            return port not in occupied_ports
        
        monkeypatch.setattr("src.core.project_generator.is_port_free", mock_is_port_free)
        monkeypatch.setattr("src.core.validators.is_port_free", mock_is_port_free)
        
        config = ProjectConfig(
            project_name="test",
            destination_path=tmp_path / "test",
            backend=BackendConfig(port=8000),
            database=DatabaseConfig(stack="postgres", port=5432),
        )
        
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = ProjectGenerator(templates_dir, FileWriter(dry_run=True))
        generator._resolve_ports(config)
        
        assert config.database.port == 5433
    
    def test_no_port_collisions(self, tmp_path, monkeypatch):
        """Frontend, backend, and database ports should not collide."""
        occupied_ports = set()
        checked_ports = []
        
        def mock_is_port_free(port):
            checked_ports.append(port)
            return port not in occupied_ports
        
        monkeypatch.setattr("src.core.project_generator.is_port_free", mock_is_port_free)
        monkeypatch.setattr("src.core.validators.is_port_free", mock_is_port_free)
        
        config = ProjectConfig(
            project_name="test",
            destination_path=tmp_path / "test",
            frontend=FrontendConfig(port=3000),
            backend=BackendConfig(port=8000),
            database=DatabaseConfig(stack="postgres", port=5432),
        )
        
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = ProjectGenerator(templates_dir, FileWriter(dry_run=True))
        generator._resolve_ports(config)
        
        ports = {config.frontend.port, config.backend.port, config.database.port}
        assert len(ports) == 3  # All unique
    
    def test_no_port_available_raises_error(self, tmp_path, monkeypatch):
        """Should raise error when no port available in range."""
        def mock_is_port_free(port):
            return False  # All ports occupied
        
        def mock_find_free_port_in_range(start, end):
            from src.core.errors import GenerationError
            raise GenerationError("No available ports in range 3000-3100")
        
        monkeypatch.setattr("src.core.project_generator.is_port_free", mock_is_port_free)
        monkeypatch.setattr("src.core.project_generator.find_free_port_in_range", mock_find_free_port_in_range)
        
        config = ProjectConfig(
            project_name="test",
            destination_path=tmp_path / "test",
            frontend=FrontendConfig(port=3000),
        )
        
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = ProjectGenerator(templates_dir, FileWriter(dry_run=True))
        
        from src.core.errors import GenerationError
        with pytest.raises(GenerationError):
            generator._resolve_ports(config)

