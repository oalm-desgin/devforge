"""Tests for secret leak scanner."""

import pytest
from pathlib import Path
import subprocess
import sys


class TestSecretScanner:
    """Test secret scanner functionality."""
    
    def test_scan_aws_key(self, tmp_path):
        """Should detect AWS access key."""
        test_file = tmp_path / "test.py"
        test_file.write_text('AWS_KEY = "AKIAIOSFODNN7EXAMPLE"')
        
        script_path = Path(__file__).parent.parent.parent / "scripts" / "scan_secrets.py"
        result = subprocess.run(
            [sys.executable, str(script_path), str(tmp_path)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        assert "AWS" in result.stderr or "secret" in result.stderr.lower()
    
    def test_scan_jwt_token(self, tmp_path):
        """Should detect JWT tokens."""
        test_file = tmp_path / "test.py"
        test_file.write_text('token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgIryi4aXlH0z3zZH1L5aGz6"')
        
        script_path = Path(__file__).parent.parent.parent / "scripts" / "scan_secrets.py"
        result = subprocess.run(
            [sys.executable, str(script_path), str(tmp_path)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        assert "JWT" in result.stderr or "token" in result.stderr.lower()
    
    def test_scan_database_password(self, tmp_path):
        """Should detect database passwords."""
        test_file = tmp_path / "test.py"
        test_file.write_text('database_password = "super_secret_pass123"')
        
        script_path = Path(__file__).parent.parent.parent / "scripts" / "scan_secrets.py"
        result = subprocess.run(
            [sys.executable, str(script_path), str(tmp_path)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        assert "password" in result.stderr.lower() or "database" in result.stderr.lower()
    
    def test_scan_private_key(self, tmp_path):
        """Should detect private keys."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----
""")
        
        script_path = Path(__file__).parent.parent.parent / "scripts" / "scan_secrets.py"
        result = subprocess.run(
            [sys.executable, str(script_path), str(tmp_path)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode != 0
        assert "private key" in result.stderr.lower() or "PRIVATE KEY" in result.stderr
    
    def test_scan_no_secrets(self, tmp_path):
        """Should pass when no secrets found."""
        test_file = tmp_path / "test.py"
        test_file.write_text('x = 42\ny = "hello world"')
        
        script_path = Path(__file__).parent.parent.parent / "scripts" / "scan_secrets.py"
        result = subprocess.run(
            [sys.executable, str(script_path), str(tmp_path)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "No secrets detected" in result.stdout or "✅" in result.stdout
    
    def test_scan_excludes_secrets_file(self, tmp_path):
        """Should exclude .secrets.devforge from scanning."""
        test_file = tmp_path / ".secrets.devforge"
        test_file.write_bytes(b"encrypted_data_here")
        
        # Create a file with a secret that would normally be detected
        normal_file = tmp_path / "normal.py"
        normal_file.write_text('x = "hello"')
        
        script_path = Path(__file__).parent.parent.parent / "scripts" / "scan_secrets.py"
        result = subprocess.run(
            [sys.executable, str(script_path), str(tmp_path)],
            capture_output=True,
            text=True
        )
        
        # Should pass because .secrets.devforge is excluded
        assert result.returncode == 0

