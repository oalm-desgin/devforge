"""Tests for preset loader error handling."""

import pytest
from pathlib import Path
from src.core.preset_loader import load_preset, get_preset_default
from src.core.errors import ValidationError


def test_invalid_preset_file(tmp_path):
    """Test that invalid JSON preset file raises ValidationError."""
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json}")

    with pytest.raises(ValidationError):
        load_preset(Path(bad))


def test_missing_preset_file(tmp_path):
    """Test that missing preset file raises ValidationError."""
    missing = tmp_path / "missing.json"
    
    with pytest.raises(ValidationError):
        load_preset(Path(missing))


def test_preset_with_unknown_key(tmp_path):
    """Test that preset with unknown key logs warning but still loads."""
    preset_file = tmp_path / "preset.json"
    preset_file.write_text('{"unknown_key": "value", "default_backend": true}')
    
    # Should not raise, but log warning
    preset = load_preset(Path(preset_file))
    assert preset["default_backend"] is True
    assert "unknown_key" in preset


def test_get_preset_default_with_preset(tmp_path):
    """Test get_preset_default with actual preset."""
    preset = {"default_backend": True, "frontend_port": 3000}
    assert get_preset_default(preset, "default_backend", False) is True
    assert get_preset_default(preset, "frontend_port", 8080) == 3000
    assert get_preset_default(preset, "missing_key", "default") == "default"


def test_get_preset_default_without_preset():
    """Test get_preset_default with None preset."""
    assert get_preset_default(None, "any_key", "default") == "default"

