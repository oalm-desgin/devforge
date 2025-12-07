"""Tests for secrets management."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.core.secrets_manager import SecretsManager


class TestSecretsManager:
    """Test secrets manager functionality."""
    
    def test_init_store(self, tmp_path):
        """Should initialize secrets store."""
        manager = SecretsManager(tmp_path)
        created = manager.init_store()
        
        assert created is True
        assert manager.secrets_file.exists()
    
    def test_init_store_already_exists(self, tmp_path):
        """Should not recreate existing store."""
        manager = SecretsManager(tmp_path)
        manager.init_store()
        created = manager.init_store()
        
        assert created is False
        assert manager.secrets_file.exists()
    
    def test_set_and_get_secret(self, tmp_path):
        """Should set and retrieve secrets."""
        manager = SecretsManager(tmp_path)
        manager.init_store()
        
        manager.set_secret("TEST_KEY", "test_value")
        value = manager.get_secret("TEST_KEY")
        
        assert value == "test_value"
    
    def test_get_nonexistent_secret(self, tmp_path):
        """Should return None for nonexistent secret."""
        manager = SecretsManager(tmp_path)
        manager.init_store()
        
        value = manager.get_secret("NONEXISTENT")
        assert value is None
    
    def test_list_secrets(self, tmp_path):
        """Should list all secret keys."""
        manager = SecretsManager(tmp_path)
        manager.init_store()
        
        manager.set_secret("KEY1", "value1")
        manager.set_secret("KEY2", "value2")
        manager.set_secret("KEY3", "value3")
        
        keys = manager.list_secrets()
        assert len(keys) == 3
        assert "KEY1" in keys
        assert "KEY2" in keys
        assert "KEY3" in keys
    
    def test_list_secrets_empty(self, tmp_path):
        """Should return empty list for empty store."""
        manager = SecretsManager(tmp_path)
        manager.init_store()
        
        keys = manager.list_secrets()
        assert keys == []
    
    def test_inject_runtime_env(self, tmp_path):
        """Should inject secrets into environment file."""
        manager = SecretsManager(tmp_path)
        manager.init_store()
        
        manager.set_secret("DATABASE_PASSWORD", "secret123")
        manager.set_secret("API_KEY", "key456")
        
        output_file = manager.inject_runtime_env()
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "DATABASE_PASSWORD" in content
        assert "API_KEY" in content
        assert "secret123" in content
        assert "key456" in content
    
    def test_encryption_round_trip(self, tmp_path):
        """Should encrypt and decrypt secrets correctly."""
        manager = SecretsManager(tmp_path)
        manager.init_store()
        
        original_value = "super_secret_password_123"
        manager.set_secret("PASSWORD", original_value)
        
        # Read encrypted file directly
        encrypted_data = manager.secrets_file.read_bytes()
        assert original_value.encode() not in encrypted_data  # Should be encrypted
        
        # Decrypt via manager
        decrypted_value = manager.get_secret("PASSWORD")
        assert decrypted_value == original_value
    
    def test_set_secret_without_init(self, tmp_path):
        """Should raise error when setting secret without init."""
        manager = SecretsManager(tmp_path)
        
        with pytest.raises(ValueError, match="not initialized"):
            manager.set_secret("KEY", "value")
    
    def test_thread_safety(self, tmp_path):
        """Should handle concurrent access safely."""
        import threading
        
        manager = SecretsManager(tmp_path)
        manager.init_store()
        
        def set_secrets(prefix):
            for i in range(10):
                manager.set_secret(f"{prefix}_KEY_{i}", f"value_{i}")
        
        threads = [threading.Thread(target=set_secrets, args=(f"t{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        keys = manager.list_secrets()
        assert len(keys) == 50  # 5 threads * 10 keys each
    
    def test_key_manager_file_fallback(self, tmp_path):
        """Should use file storage when platform-specific storage unavailable."""
        manager = SecretsManager(tmp_path)
        
        # Mock platform to simulate unsupported system
        with patch('src.core.secrets_manager.platform.system', return_value='unknown'):
            with patch.object(manager.key_manager, '_store_windows_key', return_value=False):
                with patch.object(manager.key_manager, '_store_macos_key', return_value=False):
                    key = manager.key_manager.generate_key()
                    assert key is not None
                    assert manager.key_manager.key_file.exists()

