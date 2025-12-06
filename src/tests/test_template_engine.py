"""Tests for template engine error handling."""

import pytest
from pathlib import Path
from src.template_engine import TemplateEngine
from src.core.errors import TemplateRenderError


def test_template_missing_variable(tmp_path):
    """Test that missing template variable raises exception."""
    # Create a templates directory structure
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    # Create a template file with missing variable
    tpl = templates_dir / "bad.j2"
    tpl.write_text("Hello {{ MISSING }}")
    
    engine = TemplateEngine(templates_dir)
    
    with pytest.raises(TemplateRenderError):
        engine.render_template(Path("bad.j2"), {})


def test_template_not_found(tmp_path):
    """Test that missing template file raises TemplateRenderError."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    engine = TemplateEngine(templates_dir)
    
    with pytest.raises(TemplateRenderError):
        engine.render_template(Path("nonexistent.template"), {})


def test_render_string(tmp_path):
    """Test render_string method."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    engine = TemplateEngine(templates_dir)
    
    result = engine.render_string("Hello {{ name }}", {"name": "World"})
    assert result == "Hello World"


def test_render_string_missing_variable(tmp_path):
    """Test render_string with missing variable raises exception."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    engine = TemplateEngine(templates_dir)
    
    with pytest.raises(Exception):  # Will raise UndefinedError from Jinja2
        engine.render_string("Hello {{ MISSING }}", {})

