"""Pytest configuration and shared fixtures."""

import socket
from pathlib import Path
from typing import Optional

import pytest

from src.core.config_models import (
    ProjectConfig, FrontendConfig, BackendConfig, DatabaseConfig, PortConfig
)


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def fake_env(monkeypatch):
    """Create a fake environment with test values."""
    def _set_env(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, str(value))
    return _set_env


@pytest.fixture
def empty_config_factory(tmp_path):
    """Factory for creating empty configs."""
    def _create(name: str = "test_project"):
        return ProjectConfig(
            project_name=name,
            destination_path=tmp_path / name,
        )
    return _create


@pytest.fixture
def backend_only_config(tmp_path):
    """Config with backend only."""
    return ProjectConfig(
        project_name="test_backend",
        destination_path=tmp_path / "test_backend",
        backend=BackendConfig(port=8000),
        ports=PortConfig(backend_port=8000),
    )


@pytest.fixture
def backend_postgres_config(tmp_path):
    """Config with backend and PostgreSQL."""
    return ProjectConfig(
        project_name="test_backend_postgres",
        destination_path=tmp_path / "test_backend_postgres",
        backend=BackendConfig(port=8000),
        database=DatabaseConfig(
            stack="postgres",
            port=5432,
            name="test_db",
            user="test_user",
            password="test_pass",
        ),
        ports=PortConfig(
            backend_port=8000,
            database_port=5432,
        ),
    )


@pytest.fixture
def backend_mongo_config(tmp_path):
    """Config with backend and MongoDB."""
    return ProjectConfig(
        project_name="test_backend_mongo",
        destination_path=tmp_path / "test_backend_mongo",
        backend=BackendConfig(port=8000),
        database=DatabaseConfig(
            stack="mongo",
            port=27017,
            name="test_db",
            user="test_user",
            password="test_pass",
        ),
        ports=PortConfig(
            backend_port=8000,
            database_port=27017,
        ),
    )


@pytest.fixture
def backend_redis_config(tmp_path):
    """Config with backend and Redis."""
    return ProjectConfig(
        project_name="test_backend_redis",
        destination_path=tmp_path / "test_backend_redis",
        backend=BackendConfig(port=8000),
        database=DatabaseConfig(
            stack="redis",
            port=6379,
            name="test_db",
        ),
        ports=PortConfig(
            backend_port=8000,
            database_port=6379,
        ),
    )


@pytest.fixture
def frontend_backend_postgres_config(tmp_path):
    """Config with frontend, backend, and PostgreSQL."""
    return ProjectConfig(
        project_name="test_full_stack",
        destination_path=tmp_path / "test_full_stack",
        frontend=FrontendConfig(port=3000),
        backend=BackendConfig(port=8000),
        database=DatabaseConfig(
            stack="postgres",
            port=5432,
            name="test_db",
            user="test_user",
            password="test_pass",
        ),
        ports=PortConfig(
            frontend_port=3000,
            backend_port=8000,
            database_port=5432,
        ),
    )


@pytest.fixture
def mock_port_free(monkeypatch):
    """Mock port availability checks."""
    free_ports = set()
    
    def _is_port_free(port: int) -> bool:
        return port in free_ports
    
    def _set_port_free(port: int):
        free_ports.add(port)
    
    def _set_port_occupied(port: int):
        free_ports.discard(port)
    
    # Mock socket binding
    original_socket = socket.socket
    
    def mock_socket(*args, **kwargs):
        sock = original_socket(*args, **kwargs)
        original_bind = sock.bind
        
        def mock_bind(address):
            port = address[1]
            if port not in free_ports:
                raise OSError(f"Port {port} is in use")
            return original_bind(address)
        
        sock.bind = mock_bind
        return sock
    
    monkeypatch.setattr(socket, "socket", mock_socket)
    
    return _set_port_free, _set_port_occupied


