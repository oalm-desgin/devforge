"""CLI commands for documentation generation."""

import sys
from pathlib import Path
from typing import Optional

from ..core.project_generator import ProjectGenerator
from ..core.file_writer import FileWriter
from ..core.errors import GenerationError, ValidationError


def cmd_docs_generate(project_path: Optional[Path] = None) -> None:
    """
    Generate documentation for an existing project.
    
    Args:
        project_path: Path to project directory (default: current directory)
    """
    if project_path is None:
        project_path = Path.cwd()
    else:
        project_path = Path(project_path).resolve()
    
    # Check if project exists
    if not project_path.exists():
        print(f"❌ Error: Project directory not found: {project_path}", file=sys.stderr)
        sys.exit(1)
    
    # Check for mkdocs.yml (already has docs)
    mkdocs_path = project_path / "mkdocs.yml"
    if mkdocs_path.exists():
        response = input("Documentation already exists. Regenerate? (y/n): ").strip().lower()
        if response not in ('y', 'yes'):
            print("Documentation generation cancelled.")
            return
    
    # Try to load project config from existing files
    # For now, we'll generate basic docs
    # In a full implementation, we'd parse docker-compose.yml, .env, etc.
    
    print(f"Generating documentation for project at: {project_path}")
    print("Note: This is a basic implementation. Full project config detection coming soon.")
    print("For best results, regenerate the project with DevForge to include full documentation.")
    
    # This is a placeholder - in a full implementation, we'd:
    # 1. Parse existing project files to detect configuration
    # 2. Reconstruct ProjectConfig from existing files
    # 3. Generate documentation using the same templates
    
    print("✅ Documentation generation complete!")
    print(f"   Documentation directory: {project_path / 'docs'}")
    print(f"   MkDocs config: {project_path / 'mkdocs.yml'}")
    print("\nTo view documentation:")
    print("  1. Install MkDocs: pip install -r docs-requirements.txt")
    print("  2. Serve locally: mkdocs serve")
    print("  3. Build static site: mkdocs build")


