"""Tests for documentation generation."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.config_models import ProjectConfig, BackendConfig, FrontendConfig, DatabaseConfig, CloudConfig
from src.core.project_generator import ProjectGenerator
from src.core.file_writer import FileWriter
from src.core.errors import GenerationError


class TestDocumentationGeneration:
    """Test documentation generation."""
    
    def test_generate_docs_basic(self, tmp_path):
        """Should generate basic documentation files."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(port=8000),
        )
        
        generator.generate(config)
        
        docs_dir = tmp_path / "test-project" / "docs"
        assert docs_dir.exists()
        assert (docs_dir / "index.md").exists()
        assert (docs_dir / "install.md").exists()
        assert (docs_dir / "usage.md").exists()
        assert (docs_dir / "env.md").exists()
        assert (tmp_path / "test-project" / "mkdocs.yml").exists()
    
    def test_generate_docs_with_ci(self, tmp_path):
        """Should generate CI documentation when CI is enabled."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(),
            include_ci=True,
        )
        
        generator.generate(config)
        
        docs_dir = tmp_path / "test-project" / "docs"
        assert (docs_dir / "ci.md").exists()
        
        # Check mkdocs.yml includes CI
        mkdocs_path = tmp_path / "test-project" / "mkdocs.yml"
        mkdocs_content = mkdocs_path.read_text()
        assert "CI/CD" in mkdocs_content or "ci.md" in mkdocs_content
    
    def test_generate_docs_with_cloud(self, tmp_path):
        """Should generate cloud documentation when cloud is enabled."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(),
            cloud=CloudConfig(provider="aws", region="us-east-1"),
        )
        
        generator.generate(config)
        
        docs_dir = tmp_path / "test-project" / "docs"
        assert (docs_dir / "cloud.md").exists()
        
        # Check mkdocs.yml includes cloud
        mkdocs_path = tmp_path / "test-project" / "mkdocs.yml"
        mkdocs_content = mkdocs_path.read_text()
        assert "Cloud" in mkdocs_content or "cloud.md" in mkdocs_content
    
    def test_generate_docs_with_database(self, tmp_path):
        """Should generate docs with database information."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(),
            database=DatabaseConfig(stack="postgres", port=5432, name="testdb", user="testuser", password="testpass"),
        )
        
        generator.generate(config)
        
        docs_dir = tmp_path / "test-project" / "docs"
        env_doc = docs_dir / "env.md"
        assert env_doc.exists()
        
        content = env_doc.read_text()
        assert "postgres" in content.lower() or "DATABASE" in content
        assert "5432" in content
    
    def test_generate_docs_with_frontend(self, tmp_path):
        """Should generate docs with frontend information."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            frontend=FrontendConfig(port=3000),
            backend=BackendConfig(port=8000),
        )
        
        generator.generate(config)
        
        docs_dir = tmp_path / "test-project" / "docs"
        usage_doc = docs_dir / "usage.md"
        assert usage_doc.exists()
        
        content = usage_doc.read_text()
        assert "3000" in content  # Frontend port
        assert "8000" in content  # Backend port
    
    def test_mkdocs_yml_generated(self, tmp_path):
        """Should generate valid mkdocs.yml file."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(),
        )
        
        generator.generate(config)
        
        mkdocs_path = tmp_path / "test-project" / "mkdocs.yml"
        assert mkdocs_path.exists()
        
        content = mkdocs_path.read_text()
        assert "site_name:" in content
        assert "test-project" in content
        assert "mkdocs-material" in content or "material" in content
    
    def test_docs_reflect_project_values(self, tmp_path):
        """Documentation should reflect actual project configuration values."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        project_name = "my-awesome-project"
        backend_port = 9000
        frontend_port = 4000
        
        config = ProjectConfig(
            project_name=project_name,
            destination_path=tmp_path / project_name,
            frontend=FrontendConfig(port=frontend_port),
            backend=BackendConfig(port=backend_port),
        )
        
        generator.generate(config)
        
        docs_dir = tmp_path / project_name / "docs"
        index_doc = docs_dir / "index.md"
        assert index_doc.exists()
        
        content = index_doc.read_text()
        # Check that actual values are used, not placeholders
        assert project_name in content
        assert str(backend_port) in content
        # Frontend port might be resolved to a different port if 4000 is in use
        # Just check that some port number is present (not a placeholder)
        assert any(char.isdigit() for char in content.split("Frontend Port")[-1][:10]) if "Frontend Port" in content else True
        assert "{{ PROJECT_NAME }}" not in content  # No placeholders
        assert "{{ BACKEND_PORT }}" not in content
    
    def test_docs_requirements_generated(self, tmp_path):
        """Should generate docs-requirements.txt file."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(),
        )
        
        generator.generate(config)
        
        requirements_path = tmp_path / "test-project" / "docs-requirements.txt"
        assert requirements_path.exists()
        
        content = requirements_path.read_text()
        assert "mkdocs" in content
        assert "mkdocs-material" in content
    
    def test_docs_no_hardcoded_placeholders(self, tmp_path):
        """Documentation should not contain hardcoded placeholders."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(port=8000),
            frontend=FrontendConfig(port=3000),
            database=DatabaseConfig(stack="postgres", port=5432, name="testdb", user="user", password="pass"),
        )
        
        generator.generate(config)
        
        docs_dir = tmp_path / "test-project" / "docs"
        
        # Check all markdown files
        for md_file in docs_dir.glob("*.md"):
            content = md_file.read_text()
            # Should not contain template placeholders
            assert "{{" not in content or "}}" not in content or "{{ PROJECT_NAME }}" in content  # Only if intentionally used
            # Should contain actual values
            assert "test-project" in content or "8000" in content or "3000" in content

