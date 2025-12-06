"""Tests for validation functions."""

import pytest
from pathlib import Path

from src.core.validators import (
    validate_project_name,
    validate_path,
    is_port_free,
    find_free_port,
    find_free_port_in_range,
    validate_project_config,
)
from src.core.config_models import DatabaseConfig


class TestValidateProjectName:
    """Test project name validation."""
    
    def test_empty_name(self):
        """Empty name should be rejected."""
        is_valid, error = validate_project_name("")
        assert not is_valid
        assert "empty" in error.lower()
    
    def test_name_with_spaces(self):
        """Name with spaces should be rejected."""
        is_valid, error = validate_project_name("my project")
        assert not is_valid
        assert "letters, numbers" in error.lower()
    
    def test_reserved_names(self):
        """Reserved names should be rejected."""
        reserved = ["test", "temp", "example", "default", "con", "prn"]
        for name in reserved:
            is_valid, error = validate_project_name(name)
            assert not is_valid
            assert "reserved" in error.lower()
    
    def test_valid_name(self):
        """Valid names should pass."""
        valid_names = ["myapp", "my-app", "my_app", "myapp123"]
        for name in valid_names:
            is_valid, error = validate_project_name(name)
            assert is_valid, f"{name} should be valid: {error}"
            assert error is None
    
    def test_too_short(self):
        """Name too short should be rejected."""
        is_valid, error = validate_project_name("a")
        assert not is_valid
        assert "at least 2" in error.lower()
    
    def test_too_long(self):
        """Name too long should be rejected."""
        is_valid, error = validate_project_name("a" * 51)
        assert not is_valid
        assert "less than 50" in error.lower()


class TestValidatePath:
    """Test path validation."""
    
    def test_nonexistent_parent(self, tmp_path):
        """Non-existent parent directory should be rejected."""
        invalid_path = tmp_path / "nonexistent" / "project"
        is_valid, error = validate_path(invalid_path)
        assert not is_valid
        assert "parent directory" in error.lower()
    
    def test_valid_path(self, tmp_path):
        """Valid path should pass."""
        valid_path = tmp_path / "project"
        is_valid, error = validate_path(valid_path)
        assert is_valid
        assert error is None


class TestPortFunctions:
    """Test port checking functions."""
    
    def test_find_free_port(self, monkeypatch):
        """find_free_port should skip occupied ports."""
        occupied_ports = {3000, 3001}
        free_port = 3002
        
        def mock_is_port_free(port):
            return port not in occupied_ports
        
        monkeypatch.setattr("src.core.validators.is_port_free", mock_is_port_free)
        
        result = find_free_port(3000, max_attempts=10)
        assert result == free_port
    
    def test_find_free_port_in_range(self, monkeypatch):
        """find_free_port_in_range should respect boundaries."""
        occupied_ports = {3000, 3001, 3002}
        free_port = 3003
        
        def mock_is_port_free(port):
            return port not in occupied_ports
        
        monkeypatch.setattr("src.core.validators.is_port_free", mock_is_port_free)
        
        result = find_free_port_in_range(3000, 3100)
        assert result == free_port
        assert 3000 <= result <= 3100
    
    def test_find_free_port_in_range_no_available(self, monkeypatch):
        """Should raise error if no port available in range."""
        def mock_is_port_free(port):
            return False  # All ports occupied
        
        monkeypatch.setattr("src.core.validators.is_port_free", mock_is_port_free)
        
        with pytest.raises(Exception):  # ValidationError
            find_free_port_in_range(3000, 3005)


class TestDatabaseEngineDefaults:
    """Test database engine default ports."""
    
    def test_postgres_default(self):
        """PostgreSQL default port should be 5432."""
        assert DatabaseConfig.get_default_port("postgres") == 5432
    
    def test_mongo_default(self):
        """MongoDB default port should be 27017."""
        assert DatabaseConfig.get_default_port("mongo") == 27017
    
    def test_redis_default(self):
        """Redis default port should be 6379."""
        assert DatabaseConfig.get_default_port("redis") == 6379
    
    def test_unknown_default(self):
        """Unknown engine should default to 5432."""
        assert DatabaseConfig.get_default_port("unknown") == 5432


class TestValidateProjectConfig:
    """Test project configuration validation."""
    
    def test_database_without_backend(self):
        """Database without backend should fail."""
        is_valid, error = validate_project_config(
            frontend=True,  # Need at least one component
            backend=False,
            database=True
        )
        assert not is_valid
        assert "database" in error.lower() and "backend" in error.lower()
    
    def test_all_components_disabled(self):
        """All components disabled should fail."""
        is_valid, error = validate_project_config(
            frontend=False,
            backend=False,
            database=False
        )
        assert not is_valid
        assert "at least one" in error.lower()
    
    def test_valid_backend_only(self):
        """Backend only should be valid."""
        is_valid, error = validate_project_config(
            frontend=False,
            backend=True,
            database=False
        )
        assert is_valid
        assert error is None
    
    def test_valid_full_stack(self):
        """Full stack should be valid."""
        is_valid, error = validate_project_config(
            frontend=True,
            backend=True,
            database=True
        )
        assert is_valid
        assert error is None


def test_validator_missing_name():
    """Test that empty project name validation fails."""
    is_valid, error = validate_project_name("")
    assert not is_valid
    assert "empty" in error.lower() or "cannot be empty" in error.lower()

