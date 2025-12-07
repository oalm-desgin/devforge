"""Project generation orchestration."""

import logging
import secrets
import string
from pathlib import Path
from typing import Dict, Any, Optional

from .config_models import ProjectConfig, DatabaseConfig
from .file_writer import FileWriter
from .errors import GenerationError
from .validators import is_port_free, find_free_port, find_free_port_in_range
from .plugin_manager import PluginManager
from ..template_engine import TemplateEngine

logger = logging.getLogger(__name__)


class ProjectGenerator:
    """Orchestrates project generation from templates."""
    
    def __init__(
        self,
        templates_dir: Path,
        file_writer: FileWriter,
        plugins_dir: Optional[Path] = None
    ):
        """
        Initialize project generator.
        
        Args:
            templates_dir: Base directory containing template files
            file_writer: FileWriter instance for safe file operations
            plugins_dir: Optional directory containing plugin modules
        """
        self.templates_dir = Path(templates_dir).resolve()
        self.file_writer = file_writer
        self.template_engine = TemplateEngine(self.templates_dir)
        
        # Initialize plugin manager if plugins directory is provided
        self.plugin_manager: Optional[PluginManager] = None
        if plugins_dir is not None:
            self.plugin_manager = PluginManager(Path(plugins_dir).resolve())
            self.plugin_manager.discover_plugins()
    
    def generate(self, config: ProjectConfig) -> None:
        """
        Generate a complete project from configuration.
        
        Args:
            config: Project configuration
        """
        logger.info(f"Generating project: {config.project_name} at {config.destination_path}")
        
        # Resolve ports automatically BEFORE any template rendering
        self._resolve_ports(config)
        
        # Build template context
        context = self._build_template_context(config)
        
        # Create project root directory
        project_root = config.destination_path
        self.file_writer.create_directory(project_root, exist_ok=False)
        
        # Generate frontend if configured
        if config.frontend:
            self._generate_frontend(project_root, config, context)
        
        # Generate backend if configured
        if config.backend:
            self._generate_backend(project_root, config, context)
            
            # Generate migrations, seed, and entrypoint if database is also configured
            if config.database:
                self._generate_migrations(project_root, config, context)
                self._generate_seed(project_root, config, context)
                self._generate_entrypoint(project_root, config, context)
        
        # Generate database config if configured
        if config.database:
            # Database is handled via docker-compose, but we might add init scripts later
            pass
        
        # Generate infrastructure files
        self._generate_infrastructure(project_root, config, context)
        
        # Generate README
        self._generate_readme(project_root, config, context)
        
        # Generate .gitignore
        self._generate_gitignore(project_root, config, context)
        
        # Generate CI files if requested
        if config.include_ci:
            self._generate_ci(project_root, config, context)
        
        # Generate cloud infrastructure if requested
        if config.cloud:
            self._generate_cloud(project_root, config, context)
        
        # Generate documentation if requested
        self._generate_documentation(project_root, config, context)
        
        # Initialize secrets store if backend+database or CI enabled
        if (config.backend and config.database) or config.include_ci:
            self._initialize_secrets(project_root, config, context)
        
        logger.info(f"Project generation complete: {project_root}")
    
    def _resolve_ports(self, config: ProjectConfig) -> None:
        """
        Automatically resolve and assign ports for all services.
        
        Ports are resolved before template rendering to ensure consistency.
        
        Args:
            config: Project configuration (modified in-place)
        """
        logger.info("Resolving ports automatically...")
        
        # Default ports
        FRONTEND_DEFAULT = 3000
        BACKEND_DEFAULT = 8000
        DATABASE_DEFAULT = 5432
        PORT_RANGE_START = 3000
        PORT_RANGE_END = 3100
        
        # Track assigned ports to avoid conflicts
        assigned_ports = []
        
        # Resolve frontend port (must be in range 3000-3100)
        if config.frontend:
            frontend_port = config.frontend.port if hasattr(config.frontend, 'port') and config.frontend.port else FRONTEND_DEFAULT
            
            # Ensure frontend port is within range
            if frontend_port < PORT_RANGE_START or frontend_port > PORT_RANGE_END:
                frontend_port = PORT_RANGE_START
                logger.info(f"Frontend port adjusted to {frontend_port} (must be in range 3000-3100)")
            
            # Check if requested port is available and not already assigned
            if is_port_free(frontend_port) and frontend_port not in assigned_ports:
                resolved_port = frontend_port
                logger.info(f"Resolved frontend port: {resolved_port}")
            else:
                # Find next available in range 3000-3100
                try:
                    # Start searching from requested port
                    search_start = max(frontend_port, PORT_RANGE_START)
                    resolved_port = None
                    
                    # Try ports from search_start to PORT_RANGE_END
                    for port in range(search_start, PORT_RANGE_END + 1):
                        if is_port_free(port) and port not in assigned_ports:
                            resolved_port = port
                            break
                    
                    # If not found, try from PORT_RANGE_START to search_start
                    if resolved_port is None:
                        for port in range(PORT_RANGE_START, search_start):
                            if is_port_free(port) and port not in assigned_ports:
                                resolved_port = port
                                break
                    
                    if resolved_port is None:
                        raise GenerationError("No available ports in range 3000-3100")
                    
                    if resolved_port != frontend_port:
                        logger.info(f"Resolved frontend port: {resolved_port} (requested {frontend_port} was in use)")
                    else:
                        logger.info(f"Resolved frontend port: {resolved_port}")
                except GenerationError:
                    raise
                except Exception as e:
                    raise GenerationError(f"Failed to resolve frontend port: {e}")
            
            config.frontend.port = resolved_port
            assigned_ports.append(resolved_port)
            
            # Update PortConfig
            if config.ports:
                config.ports.frontend_port = resolved_port
        
        # Resolve backend port
        if config.backend:
            backend_port = config.backend.port if hasattr(config.backend, 'port') and config.backend.port else BACKEND_DEFAULT
            
            # Check if requested port is available
            if is_port_free(backend_port) and backend_port not in assigned_ports:
                resolved_port = backend_port
                logger.info(f"Resolved backend port: {resolved_port}")
            else:
                # Find next available (can go beyond 3100 for backend)
                try:
                    resolved_port = find_free_port(backend_port, max_attempts=100)
                    # Make sure it's not already assigned
                    while resolved_port in assigned_ports:
                        resolved_port = find_free_port(resolved_port + 1, max_attempts=100)
                    if resolved_port != backend_port:
                        logger.info(f"Resolved backend port: {resolved_port} (requested {backend_port} was in use)")
                    else:
                        logger.info(f"Resolved backend port: {resolved_port}")
                except Exception as e:
                    raise GenerationError(f"Failed to resolve backend port: {e}")
            
            config.backend.port = resolved_port
            assigned_ports.append(resolved_port)
            
            # Update PortConfig
            if config.ports:
                config.ports.backend_port = resolved_port
        
        # Resolve database port (engine-specific default)
        if config.database:
            # Get engine-specific default port
            database_default = DatabaseConfig.get_default_port(config.database.stack)
            database_port = config.database.port if hasattr(config.database, 'port') and config.database.port else database_default
            
            # Check if requested port is available
            if is_port_free(database_port) and database_port not in assigned_ports:
                resolved_port = database_port
                logger.info(f"Resolved database port for {config.database.stack}: {resolved_port}")
            else:
                # Find next available (can go beyond 3100 for database)
                try:
                    resolved_port = find_free_port(database_port, max_attempts=100)
                    # Make sure it's not already assigned
                    while resolved_port in assigned_ports:
                        resolved_port = find_free_port(resolved_port + 1, max_attempts=100)
                    if resolved_port != database_port:
                        logger.info(f"Resolved database port for {config.database.stack}: {resolved_port} (default {database_port} was in use)")
                    else:
                        logger.info(f"Resolved database port for {config.database.stack}: {resolved_port}")
                except Exception as e:
                    raise GenerationError(f"Failed to resolve database port for {config.database.stack}: {e}")
            
            config.database.port = resolved_port
            assigned_ports.append(resolved_port)
            
            # Update PortConfig
            if config.ports:
                config.ports.database_port = resolved_port
    
    def _build_template_context(self, config: ProjectConfig) -> Dict[str, Any]:
        """
        Build template context dictionary from config.
        
        Args:
            config: Project configuration
            
        Returns:
            Dictionary of template variables
        """
        # Generate secure password if not set
        if config.database and not config.database.password:
            config.database.password = self._generate_password()
        
        # Build context
        context = {
            "PROJECT_NAME": config.project_name,
            "PROJECT_NAME_UPPER": config.project_name.upper(),
            "PROJECT_NAME_SNAKE": config.project_name.replace("-", "_"),
            "DOCKER_NETWORK": config.docker_network,
        }
        
        # Backend context (always include, set to None if not selected)
        if config.backend:
            context["BACKEND_STACK"] = config.backend.stack
            context["BACKEND_PORT"] = config.backend.port
            context["BACKEND_LANGUAGE"] = config.backend.language
            context["BACKEND_SERVICE_NAME"] = "backend"
        else:
            context["BACKEND_STACK"] = None
            context["BACKEND_PORT"] = None
        
        # Frontend context (always include, set to None if not selected)
        if config.frontend:
            context["FRONTEND_STACK"] = config.frontend.stack
            context["FRONTEND_PORT"] = config.frontend.port
            context["FRONTEND_SERVICE_NAME"] = "frontend"
        else:
            context["FRONTEND_STACK"] = None
            context["FRONTEND_PORT"] = None
        
        # Database context (always include, set to None if not selected)
        if config.database:
            context["DATABASE_STACK"] = config.database.stack
            context["DATABASE_PORT"] = config.database.port
            context["DATABASE_NAME"] = config.database.name
            context["DATABASE_USER"] = config.database.user
            context["DATABASE_PASSWORD"] = config.database.password
            context["DATABASE_SERVICE_NAME"] = "database"
            context["DATABASE_HOST"] = "database"
        else:
            context["DATABASE_STACK"] = None
            context["DATABASE_PORT"] = None
            context["DATABASE_NAME"] = None
            context["DATABASE_USER"] = None
            context["DATABASE_PASSWORD"] = None
            context["DATABASE_HOST"] = None
        
        # Cloud context (if cloud is enabled)
        if config.cloud:
            context["CLOUD_PROVIDER"] = config.cloud.provider
            context["CLOUD_REGION"] = config.cloud.region
        else:
            context["CLOUD_PROVIDER"] = None
            context["CLOUD_REGION"] = None
        
        return context
    
    def _generate_backend(
        self,
        project_root: Path,
        config: ProjectConfig,
        context: Dict[str, Any]
    ) -> None:
        """Generate backend files."""
        backend_dir = project_root / "backend"
        self.file_writer.create_directory(backend_dir)
        
        # Determine backend stack
        if config.backend.stack == "fastapi":
            self._generate_fastapi_backend(backend_dir, context)
        else:
            raise GenerationError(f"Unsupported backend stack: {config.backend.stack}")
    
    def _generate_fastapi_backend(
        self,
        backend_dir: Path,
        context: Dict[str, Any]
    ) -> None:
        """Generate FastAPI backend files."""
        templates = [
            ("backend/fastapi/main.py.template", "main.py"),
            ("backend/fastapi/requirements.txt.template", "requirements.txt"),
            ("backend/fastapi/Dockerfile.template", "Dockerfile"),
        ]
        
        for template_path, output_filename in templates:
            # Use forward slashes for Jinja2 (works on all platforms)
            template_path_str = template_path.replace("\\", "/")
            rendered = self.template_engine.render_template(
                Path(template_path_str),
                context
            )
            output_path = backend_dir / output_filename
            self.file_writer.write_file(output_path, rendered, overwrite=False)
        
        # Render plugin templates for backend if available
        if self.plugin_manager:
            plugin_templates = self.plugin_manager.get_plugin_templates()
            for template_name, template_path in plugin_templates.items():
                # Plugin templates are rendered into the backend directory
                # Template name format: "plugin_name/template_file.ext"
                if '/' in template_name:
                    parts = template_name.split('/', 1)
                    plugin_name, template_file = parts
                else:
                    template_file = template_name
                
                try:
                    rendered = self.template_engine.render_template(
                        template_path,
                        context
                    )
                    output_path = backend_dir / template_file
                    self.file_writer.write_file(output_path, rendered, overwrite=False)
                    logger.debug(f"Rendered plugin template: {template_name}")
                except Exception as e:
                    logger.warning(f"Failed to render plugin template '{template_name}': {e}")
    
    def _generate_migrations(
        self,
        project_root: Path,
        config: ProjectConfig,
        context: Dict[str, Any]
    ) -> None:
        """Generate database migration files (PostgreSQL only)."""
        if config.database and config.database.stack == "postgres":
            backend_dir = project_root / "backend"
            migrations_dir = backend_dir / "migrations"
            versions_dir = migrations_dir / "versions"
            
            self.file_writer.create_directory(migrations_dir, exist_ok=True)
            self.file_writer.create_directory(versions_dir, exist_ok=True)
            
            # Generate env.py
            env_template = Path("backend/migrations/env.py.template")
            rendered_env = self.template_engine.render_template(env_template, context)
            env_path = migrations_dir / "env.py"
            self.file_writer.write_file(env_path, rendered_env, overwrite=False)
            
            # Generate alembic.ini
            alembic_template = Path("backend/migrations/alembic.ini.template")
            rendered_alembic = self.template_engine.render_template(alembic_template, context)
            alembic_path = migrations_dir / "alembic.ini"
            self.file_writer.write_file(alembic_path, rendered_alembic, overwrite=False)
            
            # Generate initial migration
            init_template = Path("backend/migrations/versions/001_init.py.template")
            rendered_init = self.template_engine.render_template(init_template, context)
            init_path = versions_dir / "001_init.py"
            self.file_writer.write_file(init_path, rendered_init, overwrite=False)
    
    def _generate_seed(
        self,
        project_root: Path,
        config: ProjectConfig,
        context: Dict[str, Any]
    ) -> None:
        """Generate database seed script."""
        if config.database:
            backend_dir = project_root / "backend"
            seed_template = Path("backend/seed.py.template")
            rendered_seed = self.template_engine.render_template(seed_template, context)
            seed_path = backend_dir / "seed.py"
            self.file_writer.write_file(seed_path, rendered_seed, overwrite=False)
    
    def _generate_entrypoint(
        self,
        project_root: Path,
        config: ProjectConfig,
        context: Dict[str, Any]
    ) -> None:
        """Generate backend entrypoint script."""
        if config.database:
            backend_dir = project_root / "backend"
            entrypoint_template = Path("backend/entrypoint.sh.template")
            rendered_entrypoint = self.template_engine.render_template(entrypoint_template, context)
            entrypoint_path = backend_dir / "entrypoint.sh"
            self.file_writer.write_file(entrypoint_path, rendered_entrypoint, overwrite=False)
    
    def _generate_frontend(
        self,
        project_root: Path,
        config: ProjectConfig,
        context: Dict[str, Any]
    ) -> None:
        """Generate frontend files."""
        frontend_dir = project_root / "frontend"
        self.file_writer.create_directory(frontend_dir)
        
        # Determine frontend stack
        if config.frontend.stack == "react_ts_vite":
            self._generate_react_ts_vite_frontend(frontend_dir, context)
        else:
            raise GenerationError(f"Unsupported frontend stack: {config.frontend.stack}")
    
    def _generate_react_ts_vite_frontend(
        self,
        frontend_dir: Path,
        context: Dict[str, Any]
    ) -> None:
        """Generate React TypeScript Vite frontend files."""
        templates = [
            ("frontend/react_ts_vite/package.json.template", "package.json"),
            ("frontend/react_ts_vite/vite.config.ts.template", "vite.config.ts"),
            ("frontend/react_ts_vite/tailwind.config.js.template", "tailwind.config.js"),
            ("frontend/react_ts_vite/postcss.config.js.template", "postcss.config.js"),
            ("frontend/react_ts_vite/tsconfig.json.template", "tsconfig.json"),
            ("frontend/react_ts_vite/tsconfig.node.json.template", "tsconfig.node.json"),
            ("frontend/react_ts_vite/index.html.template", "index.html"),
            ("frontend/react_ts_vite/Dockerfile.template", "Dockerfile"),
            ("frontend/react_ts_vite/src/main.tsx.template", "src/main.tsx"),
            ("frontend/react_ts_vite/src/App.tsx.template", "src/App.tsx"),
            ("frontend/react_ts_vite/src/index.css.template", "src/index.css"),
        ]
        
        for template_path, output_filename in templates:
            # Use forward slashes for Jinja2 (works on all platforms)
            template_path_str = template_path.replace("\\", "/")
            rendered = self.template_engine.render_template(
                Path(template_path_str),
                context
            )
            output_path = frontend_dir / output_filename
            # Create parent directory if needed (for src/ files)
            self.file_writer.create_directory(output_path.parent, exist_ok=True)
            self.file_writer.write_file(output_path, rendered, overwrite=False)
    
    def _generate_infrastructure(
        self,
        project_root: Path,
        config: ProjectConfig,
        context: Dict[str, Any]
    ) -> None:
        """Generate infrastructure files (docker-compose, .env)."""
        # Generate docker-compose.yml
        compose_template = "infra/docker-compose.yml.template"
        rendered_compose = self.template_engine.render_template(
            Path(compose_template),
            context
        )
        compose_path = project_root / "docker-compose.yml"
        self.file_writer.write_file(compose_path, rendered_compose, overwrite=False)
        
        # Generate .env file
        env_template = "infra/.env.template"
        rendered_env = self.template_engine.render_template(
            Path(env_template),
            context
        )
        env_path = project_root / ".env"
        self.file_writer.write_file(env_path, rendered_env, overwrite=False)
    
    def _generate_readme(
        self,
        project_root: Path,
        config: ProjectConfig,
        context: Dict[str, Any]
    ) -> None:
        """Generate README.md."""
        readme_template = "README.md.template"
        rendered_readme = self.template_engine.render_template(
            Path(readme_template),
            context
        )
        readme_path = project_root / "README.md"
        self.file_writer.write_file(readme_path, rendered_readme, overwrite=False)
    
    def _generate_gitignore(
        self,
        project_root: Path,
        config: ProjectConfig,
        context: Dict[str, Any]
    ) -> None:
        """Generate .gitignore."""
        gitignore_template = ".gitignore.template"
        rendered_gitignore = self.template_engine.render_template(
            Path(gitignore_template),
            context
        )
        gitignore_path = project_root / ".gitignore"
        self.file_writer.write_file(gitignore_path, rendered_gitignore, overwrite=False)
    
    def _generate_ci(
        self,
        project_root: Path,
        config: ProjectConfig,
        context: Dict[str, Any]
    ) -> None:
        """Generate CI configuration files."""
        # Generate Jenkinsfile
        jenkins_template = Path("ci/Jenkinsfile.template")
        rendered_jenkins = self.template_engine.render_template(
            jenkins_template,
            context
        )
        jenkins_path = project_root / "Jenkinsfile"
        self.file_writer.write_file(jenkins_path, rendered_jenkins, overwrite=False)
        
        # Generate GitHub Actions workflow
        github_template = Path("ci/github-actions.yml.template")
        rendered_github = self.template_engine.render_template(
            github_template,
            context
        )
        
        # Add secret validation if secrets are enabled
        if (config.backend and config.database) or config.include_ci:
            secrets_template = Path("ci/github-secrets.template")
            if (self.templates_dir / secrets_template).exists():
                # Build secrets context
                secrets_context = context.copy()
                required_secrets = []
                if config.database:
                    required_secrets.append("DATABASE_PASSWORD")
                if config.backend:
                    required_secrets.append("BACKEND_SECRET_KEY")
                secrets_context["REQUIRED_SECRETS"] = " ".join(required_secrets)
                
                secrets_section = self.template_engine.render_template(
                    secrets_template,
                    secrets_context
                )
                # Merge secrets section into workflow (append before test job)
                if "jobs:" in rendered_github and "test:" in rendered_github:
                    # Insert secrets validation jobs before test
                    rendered_github = rendered_github.replace(
                        "jobs:",
                        f"jobs:\n{secrets_section.split('jobs:')[-1] if 'jobs:' in secrets_section else secrets_section}"
                    )
        
        # Create .github/workflows directory
        workflows_dir = project_root / ".github" / "workflows"
        self.file_writer.create_directory(workflows_dir, exist_ok=True)
        github_path = workflows_dir / "ci.yml"
        self.file_writer.write_file(github_path, rendered_github, overwrite=False)
    
    def _generate_cloud(
        self,
        project_root: Path,
        config: ProjectConfig,
        context: Dict[str, Any]
    ) -> None:
        """Generate cloud infrastructure files (Terraform)."""
        if not config.cloud:
            return
        
        # Validate cloud credentials
        self._validate_cloud_credentials(config.cloud)
        
        # Create terraform directory
        terraform_dir = project_root / "terraform"
        self.file_writer.create_directory(terraform_dir)
        
        provider = config.cloud.provider
        
        # Generate provider-specific Terraform files
        if provider == "oci":
            self._generate_oci_terraform(terraform_dir, context)
        elif provider == "aws":
            self._generate_aws_terraform(terraform_dir, context)
        elif provider == "gcp":
            self._generate_gcp_terraform(terraform_dir, context)
        else:
            raise GenerationError(f"Unsupported cloud provider: {provider}")
        
        # Generate .env file for cloud credentials
        self._generate_cloud_env(terraform_dir, config.cloud)
    
    def _validate_cloud_credentials(self, cloud_config) -> None:
        """
        Validate cloud provider credentials are present.
        
        Args:
            cloud_config: CloudConfig instance
            
        Raises:
            GenerationError: If credentials are missing
        """
        if cloud_config.provider == "oci":
            # Check for OCI credentials in environment or config
            import os
            required_vars = ["OCI_TENANCY_OCID", "OCI_USER_OCID", "OCI_FINGERPRINT"]
            missing = [var for var in required_vars if not os.getenv(var)]
            if missing:
                logger.warning(
                    f"Missing OCI environment variables: {', '.join(missing)}. "
                    "Please set them before running terraform."
                )
        elif cloud_config.provider == "aws":
            # Check for AWS credentials
            import os
            if not os.getenv("AWS_ACCESS_KEY_ID") and not os.getenv("AWS_PROFILE"):
                logger.warning(
                    "AWS credentials not found. Please configure AWS credentials "
                    "using 'aws configure' or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
                )
        elif cloud_config.provider == "gcp":
            # Check for GCP credentials
            import os
            if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and not os.getenv("GCP_PROJECT"):
                logger.warning(
                    "GCP credentials not found. Please set GOOGLE_APPLICATION_CREDENTIALS "
                    "or run 'gcloud auth application-default login'."
                )
    
    def _generate_oci_terraform(self, terraform_dir: Path, context: Dict[str, Any]) -> None:
        """Generate OCI Terraform files."""
        templates = [
            ("cloud/oci/main.tf.template", "main.tf"),
            ("cloud/oci/variables.tf.template", "variables.tf"),
            ("cloud/oci/outputs.tf.template", "outputs.tf"),
        ]
        
        for template_path, output_file in templates:
            rendered = self.template_engine.render_template(
                Path(template_path),
                context
            )
            output_path = terraform_dir / output_file
            self.file_writer.write_file(output_path, rendered, overwrite=False)
    
    def _generate_aws_terraform(self, terraform_dir: Path, context: Dict[str, Any]) -> None:
        """Generate AWS Terraform files."""
        templates = [
            ("cloud/aws/main.tf.template", "main.tf"),
            ("cloud/aws/variables.tf.template", "variables.tf"),
            ("cloud/aws/outputs.tf.template", "outputs.tf"),
        ]
        
        for template_path, output_file in templates:
            rendered = self.template_engine.render_template(
                Path(template_path),
                context
            )
            output_path = terraform_dir / output_file
            self.file_writer.write_file(output_path, rendered, overwrite=False)
    
    def _generate_gcp_terraform(self, terraform_dir: Path, context: Dict[str, Any]) -> None:
        """Generate GCP Terraform files."""
        templates = [
            ("cloud/gcp/main.tf.template", "main.tf"),
            ("cloud/gcp/variables.tf.template", "variables.tf"),
            ("cloud/gcp/outputs.tf.template", "outputs.tf"),
        ]
        
        for template_path, output_file in templates:
            rendered = self.template_engine.render_template(
                Path(template_path),
                context
            )
            output_path = terraform_dir / output_file
            self.file_writer.write_file(output_path, rendered, overwrite=False)
    
    def _generate_cloud_env(self, terraform_dir: Path, cloud_config) -> None:
        """Generate .env file for cloud credentials."""
        env_content = f"# Cloud Provider: {cloud_config.provider.upper()}\n"
        env_content += f"CLOUD_PROVIDER={cloud_config.provider}\n"
        env_content += f"CLOUD_REGION={cloud_config.region}\n\n"
        
        if cloud_config.provider == "oci":
            env_content += "# OCI Credentials\n"
            env_content += "# Set these environment variables:\n"
            env_content += "# export OCI_TENANCY_OCID=ocid1.tenancy.oc1..xxxxx\n"
            env_content += "# export OCI_USER_OCID=ocid1.user.oc1..xxxxx\n"
            env_content += "# export OCI_FINGERPRINT=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx\n"
            env_content += "# export OCI_PRIVATE_KEY_PATH=~/.oci/oci_api_key.pem\n"
        elif cloud_config.provider == "aws":
            env_content += "# AWS Credentials\n"
            env_content += "# Configure using: aws configure\n"
            env_content += "# Or set:\n"
            env_content += "# export AWS_ACCESS_KEY_ID=xxxxx\n"
            env_content += "# export AWS_SECRET_ACCESS_KEY=xxxxx\n"
            env_content += "# export AWS_DEFAULT_REGION=us-east-1\n"
        elif cloud_config.provider == "gcp":
            env_content += "# GCP Credentials\n"
            env_content += "# Set: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json\n"
            env_content += "# Or run: gcloud auth application-default login\n"
            env_content += "# export GCP_PROJECT=your-project-id\n"
        
        env_path = terraform_dir / ".env.example"
        self.file_writer.write_file(env_path, env_content, overwrite=False)
    
    def _generate_documentation(
        self,
        project_root: Path,
        config: ProjectConfig,
        context: Dict[str, Any]
    ) -> None:
        """Generate MkDocs documentation site."""
        # Create docs directory
        docs_dir = project_root / "docs"
        self.file_writer.create_directory(docs_dir)
        
        # Add INCLUDE_CI to context
        context["INCLUDE_CI"] = config.include_ci
        
        # Generate documentation pages
        doc_templates = [
            ("docs/index.md.template", "index.md"),
            ("docs/install.md.template", "install.md"),
            ("docs/usage.md.template", "usage.md"),
            ("docs/env.md.template", "env.md"),
        ]
        
        # Add CI docs if enabled
        if config.include_ci:
            doc_templates.append(("docs/ci.md.template", "ci.md"))
        
        # Add cloud docs if enabled
        if config.cloud:
            doc_templates.append(("docs/cloud.md.template", "cloud.md"))
        
        # Generate all documentation pages
        for template_path, output_file in doc_templates:
            rendered = self.template_engine.render_template(
                Path(template_path),
                context
            )
            output_path = docs_dir / output_file
            self.file_writer.write_file(output_path, rendered, overwrite=False)
        
        # Generate mkdocs.yml
        mkdocs_template = Path("docs/mkdocs.yml.template")
        rendered_mkdocs = self.template_engine.render_template(
            mkdocs_template,
            context
        )
        mkdocs_path = project_root / "mkdocs.yml"
        self.file_writer.write_file(mkdocs_path, rendered_mkdocs, overwrite=False)
        
        # Generate requirements.txt for MkDocs
        mkdocs_requirements = """mkdocs>=1.5.0
mkdocs-material>=9.0.0
"""
        requirements_path = project_root / "docs-requirements.txt"
        self.file_writer.write_file(requirements_path, mkdocs_requirements, overwrite=False)
    
    def _initialize_secrets(
        self,
        project_root: Path,
        config: ProjectConfig,
        context: Dict[str, Any]
    ) -> None:
        """Initialize secrets store and generate secret key placeholders."""
        # Skip in dry-run mode
        if self.file_writer.dry_run:
            return
        
        from .secrets_manager import SecretsManager
        
        manager = SecretsManager(project_root)
        
        # Initialize secrets store
        manager.init_store()
        
        # Generate required secret keys (but don't set values - user must do that)
        required_secrets = []
        
        if config.database:
            # Database password secret key
            db_secret_key = "DATABASE_PASSWORD"
            required_secrets.append(db_secret_key)
            # Generate a secure password and store it
            if config.database.password:
                manager.set_secret(db_secret_key, config.database.password)
        
        if config.backend:
            # Backend secret key (for sessions, JWT, etc.)
            backend_secret_key = "BACKEND_SECRET_KEY"
            required_secrets.append(backend_secret_key)
            # Generate a secure key
            backend_key = self._generate_password(32)
            manager.set_secret(backend_secret_key, backend_key)
        
        # Generate .gitignore entry for secrets
        gitignore_path = project_root / ".gitignore"
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            if ".secrets.devforge" not in content:
                content += "\n# DevForge secrets (encrypted)\n.secrets.devforge\n"
                content += ".env.secrets\n"
                self.file_writer.write_file(gitignore_path, content, overwrite=True)
        
        # Generate secrets.env.template reference (not actual secrets)
        secrets_template_path = project_root / "secrets.env.example"
        if not secrets_template_path.exists():
            secrets_template = self.templates_dir / "security" / "secrets.env.template"
            if secrets_template.exists():
                # Render template with placeholders (not actual secrets)
                secrets_context = context.copy()
                secrets_context["DATABASE_PASSWORD_SECRET"] = "{{ DATABASE_PASSWORD }}"
                secrets_context["BACKEND_SECRET_KEY"] = "{{ BACKEND_SECRET_KEY }}"
                rendered = self.template_engine.render_template(
                    Path("security/secrets.env.template"),
                    secrets_context
                )
                self.file_writer.write_file(secrets_template_path, rendered, overwrite=False)
        
        logger.info("Secrets store initialized. Use 'devforge secrets inject' to generate .env.secrets")
    
    @staticmethod
    def _generate_password(length: int = 16) -> str:
        """
        Generate a secure random password.
        
        Args:
            length: Password length
            
        Returns:
            Random password string
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

