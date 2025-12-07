"""Tests for cloud infrastructure generation."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.config_models import ProjectConfig, CloudConfig, BackendConfig, FrontendConfig
from src.core.project_generator import ProjectGenerator
from src.core.file_writer import FileWriter
from src.core.errors import GenerationError


class TestCloudConfig:
    """Test CloudConfig model."""
    
    def test_cloud_config_oci(self):
        """CloudConfig should identify OCI provider."""
        config = CloudConfig(provider="oci", region="us-ashburn-1")
        assert config.is_oci is True
        assert config.is_aws is False
        assert config.is_gcp is False
    
    def test_cloud_config_aws(self):
        """CloudConfig should identify AWS provider."""
        config = CloudConfig(provider="aws", region="us-east-1")
        assert config.is_oci is False
        assert config.is_aws is True
        assert config.is_gcp is False
    
    def test_cloud_config_gcp(self):
        """CloudConfig should identify GCP provider."""
        config = CloudConfig(provider="gcp", region="us-central1")
        assert config.is_oci is False
        assert config.is_aws is False
        assert config.is_gcp is True


class TestCloudGeneration:
    """Test cloud infrastructure generation."""
    
    def test_generate_cloud_oci(self, tmp_path):
        """Should generate OCI Terraform files."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(),
            cloud=CloudConfig(provider="oci", region="us-ashburn-1")
        )
        
        generator.generate(config)
        
        terraform_dir = tmp_path / "test-project" / "terraform"
        assert terraform_dir.exists()
        assert (terraform_dir / "main.tf").exists()
        assert (terraform_dir / "variables.tf").exists()
        assert (terraform_dir / "outputs.tf").exists()
        assert (terraform_dir / ".env.example").exists()
    
    def test_generate_cloud_aws(self, tmp_path):
        """Should generate AWS Terraform files."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(),
            cloud=CloudConfig(provider="aws", region="us-east-1")
        )
        
        generator.generate(config)
        
        terraform_dir = tmp_path / "test-project" / "terraform"
        assert terraform_dir.exists()
        assert (terraform_dir / "main.tf").exists()
        assert (terraform_dir / "variables.tf").exists()
        assert (terraform_dir / "outputs.tf").exists()
    
    def test_generate_cloud_gcp(self, tmp_path):
        """Should generate GCP Terraform files."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(),
            cloud=CloudConfig(provider="gcp", region="us-central1")
        )
        
        generator.generate(config)
        
        terraform_dir = tmp_path / "test-project" / "terraform"
        assert terraform_dir.exists()
        assert (terraform_dir / "main.tf").exists()
        assert (terraform_dir / "variables.tf").exists()
        assert (terraform_dir / "outputs.tf").exists()
    
    def test_generate_cloud_optional(self, tmp_path):
        """Cloud generation should be optional."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(),
            cloud=None
        )
        
        generator.generate(config)
        
        terraform_dir = tmp_path / "test-project" / "terraform"
        assert not terraform_dir.exists()
    
    def test_generate_cloud_invalid_provider(self, tmp_path):
        """Should raise error for invalid cloud provider."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(),
            cloud=CloudConfig(provider="invalid", region="us-east-1")
        )
        
        with pytest.raises(GenerationError, match="Unsupported cloud provider"):
            generator.generate(config)
    
    @patch('os.getenv')
    def test_validate_cloud_credentials_oci_warning(self, mock_getenv, tmp_path):
        """Should warn about missing OCI credentials."""
        mock_getenv.return_value = None
        
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(),
            cloud=CloudConfig(provider="oci", region="us-ashburn-1")
        )
        
        # Should not raise, just warn
        generator.generate(config)
        assert (tmp_path / "test-project" / "terraform").exists()
    
    def test_terraform_files_syntax(self, tmp_path):
        """Terraform files should be syntactically valid."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(port=8000),
            frontend=FrontendConfig(port=3000),
            cloud=CloudConfig(provider="aws", region="us-east-1")
        )
        
        generator.generate(config)
        
        terraform_dir = tmp_path / "test-project" / "terraform"
        main_tf = terraform_dir / "main.tf"
        
        # Check file exists and has content
        assert main_tf.exists()
        content = main_tf.read_text()
        
        # Basic syntax checks
        assert "terraform {" in content
        assert "provider" in content
        assert "{{ PROJECT_NAME }}" not in content  # Should be rendered
        assert "test-project" in content  # Should have project name
        
        # Check variables.tf for region
        variables_tf = terraform_dir / "variables.tf"
        assert variables_tf.exists()
        variables_content = variables_tf.read_text()
        assert "us-east-1" in variables_content  # Should have region
    
    def test_cloud_env_file_generated(self, tmp_path):
        """Should generate .env.example file with credentials info."""
        templates_dir = Path(__file__).parent.parent / "templates"
        file_writer = FileWriter(dry_run=False)
        generator = ProjectGenerator(templates_dir, file_writer, None)
        
        config = ProjectConfig(
            project_name="test-project",
            destination_path=tmp_path / "test-project",
            backend=BackendConfig(),
            cloud=CloudConfig(provider="aws", region="us-east-1")
        )
        
        generator.generate(config)
        
        env_file = tmp_path / "test-project" / "terraform" / ".env.example"
        assert env_file.exists()
        content = env_file.read_text()
        assert "CLOUD_PROVIDER=aws" in content
        assert "CLOUD_REGION=us-east-1" in content
        assert "AWS" in content or "aws" in content

