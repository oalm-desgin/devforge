"""Preset configuration loader for DevForge."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .errors import ValidationError

logger = logging.getLogger(__name__)


def load_preset(preset_path: Path) -> Dict[str, Any]:
    """
    Load preset configuration from JSON file.
    
    Args:
        preset_path: Path to JSON preset file
        
    Returns:
        Dictionary with preset values
        
    Raises:
        ValidationError: If preset file is invalid or cannot be loaded
    """
    if not preset_path.exists():
        raise ValidationError(f"Preset file not found: {preset_path}")
    
    try:
        with open(preset_path, 'r', encoding='utf-8') as f:
            preset = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in preset file: {e}")
    except Exception as e:
        raise ValidationError(f"Failed to load preset file: {e}")
    
    # Validate preset structure
    valid_keys = {
        'frontend', 'backend', 'database',
        'frontend_port', 'backend_port', 'database_port',
        'default_frontend', 'default_backend', 'default_database',
        'database_stack', 'database_engine'
    }
    
    for key in preset.keys():
        if key not in valid_keys:
            logger.warning(f"Unknown preset key: {key}")
    
    logger.info(f"Loaded preset from: {preset_path}")
    return preset


def get_preset_default(
    preset: Optional[Dict[str, Any]],
    key: str,
    default: Any = None
) -> Any:
    """
    Get a default value from preset, or return provided default.
    
    Args:
        preset: Preset dictionary (None if no preset)
        key: Key to look up in preset
        default: Default value if key not found
        
    Returns:
        Preset value or default
    """
    if preset is None:
        return default
    
    return preset.get(key, default)

