"""Tests for database engine support."""

import pytest
from pathlib import Path

from src.core.project_generator import ProjectGenerator
from src.core.file_writer import FileWriter


class TestDatabaseEngines:
    """Test database engine configurations."""
    
    @pytest.fixture
    def templates_dir(self):
        """Get templates directory."""
        return Path(__file__).parent.parent / "templates"
    
    @pytest.fixture
    def generator(self, templates_dir):
        """Create generator instance."""
        return ProjectGenerator(templates_dir, FileWriter(dry_run=False))
    
    def test_postgres_docker_compose_service(self, generator, backend_postgres_config, tmp_path):
        """PostgreSQL should have correct docker-compose service."""
        backend_postgres_config.destination_path = tmp_path / "postgres_test"
        generator.generate(backend_postgres_config)
        
        compose_file = backend_postgres_config.destination_path / "docker-compose.yml"
        content = compose_file.read_text()
        
        assert "image: postgres:15-alpine" in content
        assert "POSTGRES_DB" in content
        assert "POSTGRES_USER" in content
        assert "POSTGRES_PASSWORD" in content
    
    def test_mongo_docker_compose_service(self, generator, backend_mongo_config, tmp_path):
        """MongoDB should have correct docker-compose service."""
        backend_mongo_config.destination_path = tmp_path / "mongo_test"
        generator.generate(backend_mongo_config)
        
        compose_file = backend_mongo_config.destination_path / "docker-compose.yml"
        content = compose_file.read_text()
        
        assert "image: mongo:7" in content
        assert "MONGO_INITDB_DATABASE" in content
    
    def test_redis_docker_compose_service(self, generator, backend_redis_config, tmp_path):
        """Redis should have correct docker-compose service."""
        backend_redis_config.destination_path = tmp_path / "redis_test"
        generator.generate(backend_redis_config)
        
        compose_file = backend_redis_config.destination_path / "docker-compose.yml"
        content = compose_file.read_text()
        
        assert "image: redis:7-alpine" in content
        assert "POSTGRES" not in content
        assert "MONGO" not in content
    
    def test_postgres_env_variables(self, generator, backend_postgres_config, tmp_path):
        """PostgreSQL should have correct env variables."""
        backend_postgres_config.destination_path = tmp_path / "postgres_env"
        generator.generate(backend_postgres_config)
        
        env_file = backend_postgres_config.destination_path / ".env"
        content = env_file.read_text()
        
        assert "DATABASE_PORT=" in content
        assert "DATABASE_NAME=" in content
        assert "DATABASE_USER=" in content
        assert "DATABASE_PASSWORD=" in content
    
    def test_mongo_env_variables(self, generator, backend_mongo_config, tmp_path):
        """MongoDB should have correct env variables."""
        backend_mongo_config.destination_path = tmp_path / "mongo_env"
        generator.generate(backend_mongo_config)
        
        env_file = backend_mongo_config.destination_path / ".env"
        content = env_file.read_text()
        
        assert "DATABASE_PORT=" in content
        assert "DATABASE_NAME=" in content
    
    def test_redis_env_variables(self, generator, backend_redis_config, tmp_path):
        """Redis should have correct env variables."""
        backend_redis_config.destination_path = tmp_path / "redis_env"
        generator.generate(backend_redis_config)
        
        env_file = backend_redis_config.destination_path / ".env"
        content = env_file.read_text()
        
        assert "DATABASE_PORT=" in content
        # Redis doesn't need name/user/password in .env
    
    def test_postgres_backend_connection_string(self, generator, backend_postgres_config, tmp_path):
        """PostgreSQL backend should have DATABASE_URL."""
        backend_postgres_config.destination_path = tmp_path / "postgres_conn"
        generator.generate(backend_postgres_config)
        
        compose_file = backend_postgres_config.destination_path / "docker-compose.yml"
        content = compose_file.read_text()
        
        assert "DATABASE_URL=postgresql://" in content
    
    def test_mongo_backend_connection_string(self, generator, backend_mongo_config, tmp_path):
        """MongoDB backend should have MONGO_URI."""
        backend_mongo_config.destination_path = tmp_path / "mongo_conn"
        generator.generate(backend_mongo_config)
        
        compose_file = backend_mongo_config.destination_path / "docker-compose.yml"
        content = compose_file.read_text()
        
        assert "MONGO_URI=mongodb://" in content
    
    def test_redis_backend_connection_string(self, generator, backend_redis_config, tmp_path):
        """Redis backend should have REDIS_URL."""
        backend_redis_config.destination_path = tmp_path / "redis_conn"
        generator.generate(backend_redis_config)
        
        compose_file = backend_redis_config.destination_path / "docker-compose.yml"
        content = compose_file.read_text()
        
        assert "REDIS_URL=redis://" in content
    
    def test_postgres_creates_volumes(self, generator, backend_postgres_config, tmp_path):
        """PostgreSQL should create volumes."""
        backend_postgres_config.destination_path = tmp_path / "postgres_vol"
        generator.generate(backend_postgres_config)
        
        compose_file = backend_postgres_config.destination_path / "docker-compose.yml"
        content = compose_file.read_text()
        
        assert "postgres_data:" in content
    
    def test_mongo_creates_volumes(self, generator, backend_mongo_config, tmp_path):
        """MongoDB should create volumes."""
        backend_mongo_config.destination_path = tmp_path / "mongo_vol"
        generator.generate(backend_mongo_config)
        
        compose_file = backend_mongo_config.destination_path / "docker-compose.yml"
        content = compose_file.read_text()
        
        assert "mongo_data:" in content
    
    def test_redis_creates_volumes(self, generator, backend_redis_config, tmp_path):
        """Redis should create volumes."""
        backend_redis_config.destination_path = tmp_path / "redis_vol"
        generator.generate(backend_redis_config)
        
        compose_file = backend_redis_config.destination_path / "docker-compose.yml"
        content = compose_file.read_text()
        
        assert "redis_data:" in content


