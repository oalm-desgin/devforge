"""Tests for configuration models."""

import pytest
from pathlib import Path

from src.core.config_models import (
    ProjectConfig, FrontendConfig, BackendConfig, DatabaseConfig, PortConfig
)


class TestDatabaseConfig:
    """Test DatabaseConfig."""
    
    def test_is_postgres(self):
        """is_postgres should return True for postgres."""
        db = DatabaseConfig(stack="postgres")
        assert db.is_postgres
        assert not db.is_mongo
        assert not db.is_redis
    
    def test_is_mongo(self):
        """is_mongo should return True for mongo."""
        db = DatabaseConfig(stack="mongo")
        assert db.is_mongo
        assert not db.is_postgres
        assert not db.is_redis
    
    def test_is_redis(self):
        """is_redis should return True for redis."""
        db = DatabaseConfig(stack="redis")
        assert db.is_redis
        assert not db.is_postgres
        assert not db.is_mongo


class TestProjectConfig:
    """Test ProjectConfig."""
    
    def test_default_port_injection(self, tmp_path):
        """PortConfig should be created with correct defaults."""
        config = ProjectConfig(
            project_name="test",
            destination_path=tmp_path / "test",
            frontend=FrontendConfig(port=3000),
            backend=BackendConfig(port=8000),
            database=DatabaseConfig(stack="postgres", port=5432),
        )
        
        assert config.ports.frontend_port == 3000
        assert config.ports.backend_port == 8000
        assert config.ports.database_port == 5432
    
    def test_post_init_default_assignment(self, tmp_path):
        """__post_init__ should assign defaults correctly."""
        config = ProjectConfig(
            project_name="test",
            destination_path=tmp_path / "test",
            database=DatabaseConfig(stack="mongo"),
        )
        
        # Should use mongo default port
        assert config.ports.database_port == 27017
    
    def test_docker_network_default(self, tmp_path):
        """Docker network should default to project_name_network."""
        config = ProjectConfig(
            project_name="myapp",
            destination_path=tmp_path / "myapp",
        )
        
        assert config.docker_network == "myapp_network"
    
    def test_docker_network_custom(self, tmp_path):
        """Custom docker network should be preserved."""
        config = ProjectConfig(
            project_name="myapp",
            destination_path=tmp_path / "myapp",
            docker_network="custom_network",
        )
        
        assert config.docker_network == "custom_network"
    
    def test_no_database_port_default(self, tmp_path):
        """No database should use 5432 as fallback."""
        config = ProjectConfig(
            project_name="test",
            destination_path=tmp_path / "test",
        )
        
        assert config.ports.database_port == 5432


