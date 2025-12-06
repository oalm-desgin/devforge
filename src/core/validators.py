"""Validation functions for DevForge."""

import re
from pathlib import Path
from typing import Tuple, Optional, Dict

from .errors import ValidationError


def validate_project_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate project name.
    
    Args:
        name: Project name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Project name cannot be empty"
    
    if len(name) < 2:
        return False, "Project name must be at least 2 characters long"
    
    if len(name) > 50:
        return False, "Project name must be less than 50 characters"
    
    # Allow alphanumeric, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False, "Project name can only contain letters, numbers, hyphens, and underscores"
    
    # Check for reserved names (Windows reserved + common reserved)
    reserved_names = {
        'con', 'prn', 'aux', 'nul',
        'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
        'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9',
        'test', 'temp', 'example', 'default', 'sample',
    }
    if name.lower() in reserved_names:
        return False, f"'{name}' is a reserved name and cannot be used"
    
    return True, None


def validate_path(path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate destination path.
    
    Args:
        path: Path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path:
        return False, "Path cannot be empty"
    
    # Convert to absolute path
    path = path.resolve()
    
    # Check if parent directory exists
    parent = path.parent
    if not parent.exists():
        return False, f"Parent directory does not exist: {parent}"
    
    # Check if parent is writable
    if not parent.is_dir():
        return False, f"Parent path is not a directory: {parent}"
    
    # Check if we can write to parent (by attempting to create a test file)
    try:
        test_file = parent / ".devforge_test_write"
        test_file.touch()
        test_file.unlink()
    except (PermissionError, OSError) as e:
        return False, f"Cannot write to directory {parent}: {e}"
    
    # Check if target directory already exists and is not empty
    if path.exists():
        if path.is_file():
            return False, f"Path exists but is a file: {path}"
        # Check if directory is empty
        try:
            if any(path.iterdir()):
                return False, f"Directory already exists and is not empty: {path}"
        except PermissionError as e:
            return False, f"Cannot access directory {path}: {e}"
    
    return True, None


def check_port_available(port: int) -> bool:
    """
    Check if a port is available (basic check).
    
    Note: This is a simple check. In Phase 3, we'll enhance this.
    
    Args:
        port: Port number to check
        
    Returns:
        True if port appears available, False otherwise
    """
    import socket
    
    if port < 1 or port > 65535:
        return False
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True
    except OSError:
        return False


def is_port_free(port: int) -> bool:
    """
    Check if a port is free (available for binding).
    
    Args:
        port: Port number to check
        
    Returns:
        True if port is free, False otherwise
    """
    return check_port_available(port)


def find_free_port(start_port: int, max_attempts: int = 100) -> int:
    """
    Find the next free port starting from start_port.
    
    Args:
        start_port: Starting port number
        max_attempts: Maximum number of ports to check
        
    Returns:
        First available port number
        
    Raises:
        ValidationError: If no free port found in range
    """
    port = start_port
    for _ in range(max_attempts):
        if is_port_free(port):
            return port
        port += 1
    
    raise ValidationError(
        f"No available port found starting from {start_port} (checked {max_attempts} ports)"
    )


def find_free_port_in_range(start: int, end: int) -> int:
    """
    Find a free port within the specified range [start, end].
    
    Args:
        start: Start of port range (inclusive)
        end: End of port range (inclusive)
        
    Returns:
        First available port in range
        
    Raises:
        ValidationError: If no free port found in range
    """
    if start < 1 or end > 65535 or start > end:
        raise ValidationError(f"Invalid port range: {start}-{end}")
    
    for port in range(start, end + 1):
        if is_port_free(port):
            return port
    
    raise ValidationError(f"No available ports in range {start}-{end}")


def validate_project_config(
    frontend: Optional[bool],
    backend: Optional[bool],
    database: Optional[bool]
) -> Tuple[bool, Optional[str]]:
    """
    Validate project configuration combinations.
    
    Rules:
    - At least one component (frontend or backend) must be selected
    - Database can only be selected if backend is selected
    
    Args:
        frontend: Whether frontend is included (True/False/None)
        backend: Whether backend is included (True/False/None)
        database: Whether database is included (True/False/None)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Convert None to False for validation
    has_frontend = frontend is True
    has_backend = backend is True
    has_database = database is True
    
    # Rule 1: At least one component must be selected
    if not has_frontend and not has_backend:
        return False, "At least one component (frontend or backend) must be selected"
    
    # Rule 2: Database requires backend
    if has_database and not has_backend:
        return False, "Database can only be included if backend is included"
    
    return True, None


def validate_ports_are_unique(ports: Dict[str, Optional[int]]) -> Tuple[bool, Optional[str]]:
    """
    Validate that all specified ports are unique.
    
    Args:
        ports: Dictionary mapping service names to port numbers (None means not used)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    used_ports = {}
    for service, port in ports.items():
        if port is not None:
            if port in used_ports.values():
                conflicting_service = [k for k, v in used_ports.items() if v == port][0]
                return False, f"Port {port} is used by both {service} and {conflicting_service}"
            used_ports[service] = port
    
    return True, None


def validate_destination_is_empty(path: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate that destination path is empty or doesn't exist.
    
    Args:
        path: Path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not path.exists():
        return True, None
    
    if path.is_file():
        return False, f"Path exists but is a file: {path}"
    
    try:
        if any(path.iterdir()):
            return False, f"Directory already exists and is not empty: {path}"
    except PermissionError as e:
        return False, f"Cannot access directory {path}: {e}"
    
    return True, None


def suggest_available_port(start_port: int) -> int:
    """
    Suggest an available port starting from start_port.
    
    Args:
        start_port: Starting port number
        
    Returns:
        First available port number
    """
    port = start_port
    max_attempts = 100
    
    for _ in range(max_attempts):
        if check_port_available(port):
            return port
        port += 1
    
    # If we can't find one, return the original (will fail later)
    return start_port

