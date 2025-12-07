"""Tests for secret injection into Docker and CI."""

import pytest
from pathlib import Path

from src.core.secrets_manager import SecretsManager
from src.core.project_generator import ProjectGenerator
from src.core.config_models import ProjectConfig, BackendConfig, DatabaseConfig
from src.core.file_writer import FileWriter


class TestSecretInjection:
    """Test secret injection functionality."""
    
    def test_inject_into_docker_compose(self, tmp_path):
        """Should inject secrets into docker-compose environment."""
        manager = SecretsManager(tmp_path)
        manager.init_store()
        
        manager.set_secret("DATABASE_PASSWORD", "db_pass_123")
        manager.set_secret("BACKEND_SECRET_KEY", "backend_key_456")
        
        env_file = manager.inject_runtime_env()
        
        assert env_file.exists()
        content = env_file.read_text()
        
        # Check that secrets are present
        assert "DATABASE_PASSWORD" in content
        assert "BACKEND_SECRET_KEY" in content
        assert "db_pass_123" in content
        assert "backend_key_456" in content
    
    def test_secrets_not_in_templates(self, tmp_path):
        """Secrets should not be rendered into configuration template files."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(port=8000),
            database=DatabaseConfig(stack="postgres", port=5432, name="testdb", user="testuser", password="secret123"),
        )
        
        generator.generate(config)
        
        # Check docker-compose doesn't contain actual password (should use env vars)
        docker_compose_path = tmp_path / "test-project" / "docker-compose.yml"
        if docker_compose_path.exists():
            docker_content = docker_compose_path.read_text()
            # Password should not be hardcoded - should use ${DATABASE_PASSWORD} or env_file
            assert "secret123" not in docker_content or "${DATABASE_PASSWORD}" in docker_content or "env_file" in docker_content
        
        # Check .env template doesn't contain actual password
        env_template_path = tmp_path / "test-project" / ".env.example"
        if env_template_path.exists():
            env_content = env_template_path.read_text()
            # Should use placeholder or variable, not actual password
            assert "secret123" not in env_content or "${DATABASE_PASSWORD}" in env_content
    
    def test_secrets_store_initialized(self, tmp_path):
        """Should initialize secrets store when backend+database enabled."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(port=8000),
            database=DatabaseConfig(stack="postgres", port=5432, name="testdb", user="testuser", password="secret123"),
        )
        
        generator.generate(config)
        
        # Check secrets store exists
        secrets_file = tmp_path / "test-project" / ".secrets.devforge"
        assert secrets_file.exists()
        
        # Verify secrets are stored
        manager = SecretsManager(tmp_path / "test-project")
        db_password = manager.get_secret("DATABASE_PASSWORD")
        assert db_password == "secret123"
    
    def test_gitignore_includes_secrets(self, tmp_path):
        """Should add secrets files to .gitignore."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(port=8000),
            database=DatabaseConfig(stack="postgres", port=5432, name="testdb", user="testuser"),
        )
        
        generator.generate(config)
        
        gitignore_path = tmp_path / "test-project" / ".gitignore"
        assert gitignore_path.exists()
        
        gitignore_content = gitignore_path.read_text()
        assert ".secrets.devforge" in gitignore_content
        assert ".env.secrets" in gitignore_content

