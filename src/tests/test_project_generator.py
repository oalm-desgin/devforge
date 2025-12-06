"""Tests for ProjectGenerator."""

import pytest
from pathlib import Path

from src.core.project_generator import ProjectGenerator
from src.core.file_writer import FileWriter
from src.core.config_models import ProjectConfig, BackendConfig, DatabaseConfig, FrontendConfig


class TestProjectGenerator:
    """Test project generation."""
    
    @pytest.fixture
    def templates_dir(self):
        """Get templates directory."""
        return Path(__file__).parent.parent / "templates"
    
    @pytest.fixture
    def generator(self, templates_dir):
        """Create generator instance."""
        return ProjectGenerator(templates_dir, FileWriter(dry_run=False))
    
    def test_backend_only_generation(self, generator, backend_only_config, tmp_path):
        """Backend only should generate backend files."""
        backend_only_config.destination_path = tmp_path / "backend_only"
        generator.generate(backend_only_config)
        
        backend_dir = backend_only_config.destination_path / "backend"
        assert backend_dir.exists()
        assert (backend_dir / "main.py").exists()
        assert (backend_dir / "requirements.txt").exists()
        assert (backend_dir / "Dockerfile").exists()
    
    def test_backend_postgres_generation(self, generator, backend_postgres_config, tmp_path):
        """Backend + Postgres should generate migrations and seed."""
        backend_postgres_config.destination_path = tmp_path / "backend_postgres"
        generator.generate(backend_postgres_config)
        
        backend_dir = backend_postgres_config.destination_path / "backend"
        assert (backend_dir / "migrations" / "env.py").exists()
        assert (backend_dir / "migrations" / "alembic.ini").exists()
        assert (backend_dir / "migrations" / "versions" / "001_init.py").exists()
        assert (backend_dir / "seed.py").exists()
        assert (backend_dir / "entrypoint.sh").exists()
    
    def test_frontend_backend_postgres_generation(self, generator, frontend_backend_postgres_config, tmp_path):
        """Full stack should generate all components."""
        frontend_backend_postgres_config.destination_path = tmp_path / "full_stack"
        generator.generate(frontend_backend_postgres_config)
        
        assert (frontend_backend_postgres_config.destination_path / "frontend").exists()
        assert (frontend_backend_postgres_config.destination_path / "backend").exists()
        assert (frontend_backend_postgres_config.destination_path / "docker-compose.yml").exists()
    
    def test_no_database_no_db_service(self, generator, backend_only_config, tmp_path):
        """No database should not include db service in docker-compose."""
        backend_only_config.destination_path = tmp_path / "no_db"
        generator.generate(backend_only_config)
        
        compose_file = backend_only_config.destination_path / "docker-compose.yml"
        content = compose_file.read_text()
        
        assert "database:" not in content
    
    def test_with_database_correct_service(self, generator, backend_postgres_config, tmp_path):
        """With database should include correct service."""
        backend_postgres_config.destination_path = tmp_path / "with_db"
        generator.generate(backend_postgres_config)
        
        compose_file = backend_postgres_config.destination_path / "docker-compose.yml"
        content = compose_file.read_text()
        
        assert "database:" in content
        assert "postgres:15-alpine" in content
    
    def test_environment_variables_rendered(self, generator, backend_postgres_config, tmp_path):
        """Environment variables should be rendered correctly."""
        backend_postgres_config.destination_path = tmp_path / "env_test"
        generator.generate(backend_postgres_config)
        
        env_file = backend_postgres_config.destination_path / ".env"
        content = env_file.read_text()
        
        assert "DATABASE_PORT=" in content
        assert "DATABASE_NAME=" in content
        assert "DATABASE_USER=" in content
    
    def test_migrations_only_for_postgres(self, generator, backend_mongo_config, tmp_path):
        """Migrations should only be generated for PostgreSQL."""
        backend_mongo_config.destination_path = tmp_path / "mongo_test"
        generator.generate(backend_mongo_config)
        
        backend_dir = backend_mongo_config.destination_path / "backend"
        # MongoDB should have seed and entrypoint but NOT migrations
        assert (backend_dir / "seed.py").exists()
        assert (backend_dir / "entrypoint.sh").exists()
        assert not (backend_dir / "migrations").exists()
    
    def test_entrypoint_exists_when_database_enabled(self, generator, backend_postgres_config, tmp_path):
        """Entrypoint should exist when database is enabled."""
        backend_postgres_config.destination_path = tmp_path / "entrypoint_test"
        generator.generate(backend_postgres_config)
        
        backend_dir = backend_postgres_config.destination_path / "backend"
        assert (backend_dir / "entrypoint.sh").exists()
    
    def test_dry_run_creates_zero_files(self, templates_dir, backend_postgres_config, tmp_path):
        """Dry-run should create zero files."""
        dry_generator = ProjectGenerator(templates_dir, FileWriter(dry_run=True))
        backend_postgres_config.destination_path = tmp_path / "dry_run_test"
        
        dry_generator.generate(backend_postgres_config)
        
        # Should not create the project directory
        assert not backend_postgres_config.destination_path.exists()
    
    def test_templates_render_without_errors(self, generator, frontend_backend_postgres_config, tmp_path):
        """All templates should render without Jinja errors."""
        frontend_backend_postgres_config.destination_path = tmp_path / "template_test"
        
        # Should not raise any template errors
        generator.generate(frontend_backend_postgres_config)
        
        # Verify files were created (indicates successful rendering)
        assert (frontend_backend_postgres_config.destination_path / "backend" / "main.py").exists()


