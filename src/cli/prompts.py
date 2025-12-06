"""Interactive prompts for DevForge CLI."""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

from ..core.config_models import (
    ProjectConfig,
    FrontendConfig,
    BackendConfig,
    DatabaseConfig,
    PortConfig,
)
from ..core.validators import validate_project_name, validate_path, validate_project_config
from ..core.preset_loader import load_preset, get_preset_default
from ..core.errors import ValidationError


def prompt_project_name() -> str:
    """
    Prompt user for project name.
    
    Returns:
        Validated project name
    """
    while True:
        name = input("Enter project name: ").strip()
        
        is_valid, error_msg = validate_project_name(name)
        if is_valid:
            return name
        
        print(f"Error: {error_msg}", file=sys.stderr)
        print("Please try again.\n")


def prompt_include_frontend() -> bool:
    """
    Prompt user whether to include a frontend.
    
    Returns:
        True if frontend should be included, False otherwise
    """
    return prompt_include_frontend_with_default(None)


def prompt_include_frontend_with_default(default: Optional[bool]) -> bool:
    """
    Prompt user whether to include a frontend with optional default.
    
    Args:
        default: Default value (True/False/None)
        
    Returns:
        True if frontend should be included, False otherwise
    """
    default_str = "y" if default is True else "n" if default is False else "n"
    prompt_text = f"Include frontend? (y/n, default: {default_str}): "
    
    while True:
        response = input(prompt_text).strip().lower()
        
        if not response:
            return default if default is not None else False
        
        if response == 'n' or response == 'no':
            return False
        elif response == 'y' or response == 'yes':
            return True
        else:
            print("Please enter 'y' or 'n'.")


def prompt_include_backend() -> bool:
    """
    Prompt user whether to include a backend.
    
    Returns:
        True if backend should be included, False otherwise
    """
    return prompt_include_backend_with_default(True)


def prompt_include_backend_with_default(default: Optional[bool]) -> bool:
    """
    Prompt user whether to include a backend with optional default.
    
    Args:
        default: Default value (True/False/None)
        
    Returns:
        True if backend should be included, False otherwise
    """
    default_str = "y" if default is True else "n" if default is False else "y"
    prompt_text = f"Include backend? (y/n, default: {default_str}): "
    
    while True:
        response = input(prompt_text).strip().lower()
        
        if not response:
            return default if default is not None else True
        
        if response == 'n' or response == 'no':
            return False
        elif response == 'y' or response == 'yes':
            return True
        else:
            print("Please enter 'y' or 'n'.")


def prompt_include_database() -> bool:
    """
    Prompt user whether to include a database.
    
    Note: Database can only be included if backend is included.
    
    Returns:
        True if database should be included, False otherwise
    """
    return prompt_include_database_with_default(True)


def prompt_database_engine(default: Optional[str] = None) -> str:
    """
    Prompt user to select database engine.
    
    Args:
        default: Default engine stack value ("postgres", "mongo", "redis") or None
        
    Returns:
        Database stack value: "postgres", "mongo", or "redis"
    """
    # Map user-friendly names to stack values
    engine_map = {
        "1": "postgres",
        "2": "mongo",
        "3": "redis",
        "postgres": "postgres",
        "postgresql": "postgres",
        "mongo": "mongo",
        "mongodb": "mongo",
        "redis": "redis",
    }
    
    # Determine default option
    if default:
        default_stack = default.lower()
        if default_stack in ["postgres", "postgresql"]:
            default_option = "1"
            default_display = "PostgreSQL"
        elif default_stack in ["mongo", "mongodb"]:
            default_option = "2"
            default_display = "MongoDB"
        elif default_stack == "redis":
            default_option = "3"
            default_display = "Redis"
        else:
            default_option = "1"
            default_display = "PostgreSQL"
    else:
        default_option = "1"
        default_display = "PostgreSQL"
    
    while True:
        print("\nSelect database engine:")
        print("  1) PostgreSQL (default)")
        print("  2) MongoDB")
        print("  3) Redis")
        prompt_text = f"Enter choice (1-3, default: {default_option}): "
        
        response = input(prompt_text).strip().lower()
        
        if not response:
            return engine_map[default_option]
        
        if response in engine_map:
            return engine_map[response]
        
        # Try direct match
        if response in ["postgres", "postgresql"]:
            return "postgres"
        elif response in ["mongo", "mongodb"]:
            return "mongo"
        elif response == "redis":
            return "redis"
        
        print("Please enter 1, 2, 3, or the engine name.")


def prompt_include_database_with_default(default: Optional[bool]) -> bool:
    """
    Prompt user whether to include a database with optional default.
    
    Args:
        default: Default value (True/False/None)
        
    Returns:
        True if database should be included, False otherwise
    """
    default_str = "y" if default is True else "n" if default is False else "y"
    prompt_text = f"Include database? (y/n, default: {default_str}): "
    
    while True:
        response = input(prompt_text).strip().lower()
        
        if not response:
            return default if default is not None else True
        
        if response == 'n' or response == 'no':
            return False
        elif response == 'y' or response == 'yes':
            return True
        else:
            print("Please enter 'y' or 'n'.")


def prompt_destination_path() -> Path:
    """
    Prompt user for destination path.
    
    Returns:
        Validated destination path
    """
    while True:
        path_input = input("Enter destination path (or press Enter for current directory): ").strip()
        
        if not path_input:
            # Default to current directory
            cwd = Path.cwd()
            path_input = str(cwd)
        
        try:
            path = Path(path_input).expanduser().resolve()
            
            # For Phase 1, we'll ask for the parent directory and append project name later
            # But for now, let's ask for the full path including project name
            is_valid, error_msg = validate_path(path)
            if is_valid:
                return path
            
            print(f"Error: {error_msg}", file=sys.stderr)
            print("Please try again.\n")
        except Exception as e:
            print(f"Error: Invalid path - {e}", file=sys.stderr)
            print("Please try again.\n")


def collect_project_config(preset_path: Optional[Path] = None, include_ci: bool = False) -> ProjectConfig:
    """
    Collect all project configuration through interactive prompts.
    
    Args:
        preset_path: Optional path to JSON preset file with defaults
        
    Returns:
        ProjectConfig object
    """
    # Load preset if provided
    preset = None
    if preset_path:
        try:
            preset = load_preset(Path(preset_path))
        except ValidationError as e:
            print(f"Error loading preset: {e}", file=sys.stderr)
            sys.exit(1)
    
    print("=" * 60)
    print("DevForge - Development Environment Generator")
    print("=" * 60)
    print()
    
    # Get project name
    project_name = prompt_project_name()
    
    # Get destination path (parent directory)
    print(f"\nProject will be created in a folder named '{project_name}'.")
    parent_path_input = input("Enter parent directory path (or press Enter for current directory): ").strip()
    
    if not parent_path_input:
        parent_path = Path.cwd()
    else:
        parent_path = Path(parent_path_input).expanduser().resolve()
    
    # Validate parent path
    is_valid, error_msg = validate_path(parent_path)
    if not is_valid:
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)
    
    # Full destination path
    destination_path = parent_path / project_name
    
    # Ask about components (use preset defaults if available)
    print("\nSelect components to include:")
    
    # Frontend
    default_frontend = get_preset_default(preset, 'default_frontend', None)
    frontend_prompt = "Include frontend?"
    if default_frontend is True:
        frontend_prompt += " (y/n, default: y): "
    elif default_frontend is False:
        frontend_prompt += " (y/n, default: n): "
    else:
        frontend_prompt += " (y/n, default: n): "
    
    include_frontend = prompt_include_frontend_with_default(default_frontend)
    
    # Backend
    default_backend = get_preset_default(preset, 'default_backend', True)
    include_backend = prompt_include_backend_with_default(default_backend)
    
    # Database can only be included if backend is included
    include_database = False
    if include_backend:
        default_database = get_preset_default(preset, 'default_database', True)
        include_database = prompt_include_database_with_default(default_database)
    else:
        print("Database requires backend. Skipping database selection.")
    
    # Validation: Check component combinations
    is_valid, error_msg = validate_project_config(
        include_frontend,
        include_backend,
        include_database
    )
    if not is_valid:
        print(f"\nError: {error_msg}", file=sys.stderr)
        sys.exit(1)
    
    # Create frontend config if selected
    frontend = None
    if include_frontend:
        # Use preset port if provided, otherwise default to 3000
        frontend_port = get_preset_default(preset, 'frontend_port', 3000)
        frontend = FrontendConfig(
            stack="react_ts_vite",
            port=frontend_port,
            build_command="npm run build",
            dev_command="npm run dev",
        )
        print("\nFrontend: React + TypeScript + Vite + Tailwind")
    
    # Create backend config if selected
    backend = None
    if include_backend:
        # Use preset port if provided, otherwise default to 8000
        backend_port = get_preset_default(preset, 'backend_port', 8000)
        backend = BackendConfig(
            stack="fastapi",
            port=backend_port,
            language="python",
        )
        print("Backend: FastAPI")
    
    # Create database config if selected
    database = None
    if include_database:
        # Get database engine from preset or prompt user
        preset_database_stack = get_preset_default(preset, 'database_stack', None)
        if preset_database_stack:
            # Preset specifies engine, use it as default
            database_stack = prompt_database_engine(default=preset_database_stack)
        else:
            # No preset, prompt user
            database_stack = prompt_database_engine(default=None)
        
        # Get default port for selected engine
        default_port = DatabaseConfig.get_default_port(database_stack)
        
        # Use preset port if provided, otherwise use engine default
        database_port = get_preset_default(preset, 'database_port', default_port)
        
        database = DatabaseConfig(
            stack=database_stack,
            port=database_port,
            name=f"{project_name}_db",
            user=f"{project_name}_user",
            password="",  # Will be generated
        )
        
        # Display selected engine
        engine_names = {
            "postgres": "PostgreSQL",
            "mongo": "MongoDB",
            "redis": "Redis",
        }
        print(f"Database: {engine_names.get(database_stack, 'Unknown')}")
    
    # Create port config
    ports = PortConfig(
        frontend_port=frontend.port if frontend else None,
        backend_port=backend.port if backend else None,
        database_port=database.port if database else 5432,
    )
    
    # Build project config
    config = ProjectConfig(
        project_name=project_name,
        destination_path=destination_path,
        frontend=frontend,
        backend=backend,
        database=database,
        ports=ports,
        docker_network=f"{project_name}_network",
        include_ci=include_ci,
    )
    
    return config

