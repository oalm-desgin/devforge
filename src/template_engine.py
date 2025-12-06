"""Template rendering engine using Jinja2."""

import logging
from pathlib import Path
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, StrictUndefined

from .core.errors import TemplateRenderError

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Jinja2-based template rendering engine."""
    
    def __init__(self, templates_dir: Path):
        """
        Initialize template engine.
        
        Args:
            templates_dir: Base directory containing template files
        """
        self.templates_dir = Path(templates_dir).resolve()
        
        # Create Jinja2 environment with strict undefined to catch missing variables
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
    
    def render_template(
        self,
        template_path: Path,
        context: Dict[str, Any]
    ) -> str:
        """
        Render a template file with the given context.
        
        Args:
            template_path: Path to template file relative to templates_dir
            context: Dictionary of variables to use in template
            
        Returns:
            Rendered template as string
            
        Raises:
            TemplateNotFound: If template file doesn't exist
            ValueError: If template rendering fails (e.g., missing variable)
        """
        # Convert to relative path string for Jinja2, using forward slashes
        template_rel_path = str(template_path).replace("\\", "/")
        
        try:
            template = self.env.get_template(template_rel_path)
            rendered = template.render(**context)
            logger.debug(f"Rendered template: {template_path}")
            return rendered
        except TemplateNotFound as e:
            logger.error(f"Template not found: {template_path}")
            raise TemplateRenderError(f"Template not found: {template_path}") from e
        except Exception as e:
            logger.error(f"Failed to render template {template_path}: {e}")
            raise TemplateRenderError(f"Template rendering failed: {e}") from e
    
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render a template string directly.
        
        Args:
            template_string: Template content as string
            context: Dictionary of variables to use in template
            
        Returns:
            Rendered template as string
        """
        template = self.env.from_string(template_string)
        return template.render(**context)

