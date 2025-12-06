"""Custom exceptions for DevForge."""


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class GenerationError(Exception):
    """Raised when project generation fails."""
    pass


class TemplateRenderError(Exception):
    """Raised when template rendering fails."""
    pass

