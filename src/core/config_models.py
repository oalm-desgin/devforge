"""Configuration models for DevForge project generation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PortConfig:
    """Port configuration for all services."""
    frontend_port: Optional[int] = None
    backend_port: Optional[int] = None
    database_port: int = 5432


@dataclass
class FrontendConfig:
    """Frontend configuration."""
    stack: str = "react_ts_vite"
    port: int = 3000
    build_command: str = "npm run build"
    dev_command: str = "npm run dev"


@dataclass
class BackendConfig:
    """Backend configuration."""
    stack: str = "fastapi"
    port: int = 8000
    language: str = "python"
    framework_version: Optional[str] = None


@dataclass
class DatabaseConfig:
    """Database configuration."""
    stack: str = "postgres"  # Can be "postgres", "mongo", or "redis"
    port: int = 5432  # External host port (default depends on stack)
    name: str = ""
    user: str = ""
    password: str = ""
    root_password: Optional[str] = None
    
    @staticmethod
    def get_default_port(stack: str) -> int:
        """
        Get the default port for a database stack.
        
        Args:
            stack: Database stack name ("postgres", "mongo", or "redis")
            
        Returns:
            Default port number for the stack
        """
        defaults = {
            "postgres": 5432,
            "mongo": 27017,
            "redis": 6379,
        }
        return defaults.get(stack, 5432)
    
    @property
    def is_postgres(self) -> bool:
        """Check if this is a PostgreSQL database."""
        return self.stack == "postgres"
    
    @property
    def is_mongo(self) -> bool:
        """Check if this is a MongoDB database."""
        return self.stack == "mongo"
    
    @property
    def is_redis(self) -> bool:
        """Check if this is a Redis database."""
        return self.stack == "redis"


@dataclass
class ProjectConfig:
    """Complete project configuration."""
    project_name: str
    destination_path: Path
    frontend: Optional[FrontendConfig] = None
    backend: Optional[BackendConfig] = None
    database: Optional[DatabaseConfig] = None
    ports: Optional[PortConfig] = None
    docker_network: str = ""
    include_ci: bool = False

    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.ports is None:
            # Get database port default based on stack
            if self.database:
                # If port is set to default postgres port but stack is different, use correct default
                default_for_stack = DatabaseConfig.get_default_port(self.database.stack)
                if self.database.port == 5432 and self.database.stack != "postgres":
                    db_port = default_for_stack
                elif self.database.port:
                    db_port = self.database.port
                else:
                    db_port = default_for_stack
            else:
                db_port = 5432  # Default fallback
            
            self.ports = PortConfig(
                frontend_port=self.frontend.port if self.frontend else None,
                backend_port=self.backend.port if self.backend else None,
                database_port=db_port,
            )
        
        if not self.docker_network:
            self.docker_network = f"{self.project_name}_network"

