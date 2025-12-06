"""Main entry point for DevForge CLI."""

import argparse
import logging
import sys
from pathlib import Path

from .prompts import collect_project_config
from ..core.file_writer import FileWriter
from ..core.project_generator import ProjectGenerator
from ..core.validators import validate_path
from ..core.errors import ValidationError, GenerationError, TemplateRenderError
from ..core.version import VERSION

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class ProjectGenerationError(Exception):
    """Custom exception for project generation errors."""
    pass


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="DevForge - Generate complete local development environments for web projects"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be generated without creating files'
    )
    parser.add_argument(
        '--preset',
        type=str,
        help='Path to JSON preset file with default configuration'
    )
    parser.add_argument(
        '--with-ci',
        action='store_true',
        help='Include CI configuration files (Jenkinsfile and GitHub Actions)'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {VERSION}'
    )
    return parser.parse_args()


def main():
    """Main CLI entry point."""
    args = parse_args()
    
    try:
        # Collect configuration from user
        config = collect_project_config(
            preset_path=args.preset if args.preset else None,
            include_ci=args.with_ci
        )
        
        # Final validation of destination path
        is_valid, error_msg = validate_path(config.destination_path)
        if not is_valid:
            logger.error(f"Invalid destination path: {error_msg}")
            sys.exit(1)
        
        # Initialize file writer with dry-run flag
        file_writer = FileWriter(dry_run=args.dry_run)
        
        if args.dry_run:
            logger.info("\n[DRY RUN MODE] No files will be created\n")
        
        # Initialize project generator
        templates_dir = Path(__file__).parent.parent / "templates"
        generator = ProjectGenerator(templates_dir, file_writer)
        
        # Generate project
        logger.info(f"\nGenerating project '{config.project_name}'...")
        generator.generate(config)
        
        # Success message
        if args.dry_run:
            operations = file_writer.get_operations_summary()
            logger.info(f"\n{'=' * 60}")
            logger.info(f"[DRY RUN] Would generate project '{config.project_name}'")
            logger.info(f"Would create {len(operations)} operations:")
            for op_type, op_path in operations[:10]:  # Show first 10
                logger.info(f"  - {op_type}: {op_path}")
            if len(operations) > 10:
                logger.info(f"  ... and {len(operations) - 10} more")
            
            # Show resolved ports in dry-run
            logger.info(f"\nResolved ports:")
            if config.frontend:
                logger.info(f"  Frontend: {config.frontend.port}")
            if config.backend:
                logger.info(f"  Backend: {config.backend.port}")
            if config.database:
                logger.info(f"  Database: {config.database.port}")
            
            logger.info(f"{'=' * 60}\n")
        else:
            logger.info(f"\n✅ Project ready!\n")
            
            # Print final summary with resolved ports and URLs
            if config.frontend:
                logger.info(f"Frontend: http://localhost:{config.frontend.port}")
            if config.backend:
                logger.info(f"Backend:  http://localhost:{config.backend.port}/health")
            if config.database:
                logger.info(f"Database: localhost:{config.database.port}")
            
            logger.info(f"\nNext steps:")
            logger.info(f"  cd {config.destination_path.name}")
            logger.info(f"  docker compose up\n")
        
    except KeyboardInterrupt:
        logger.info("\n\nOperation cancelled by user.")
        sys.exit(1)
    except ValidationError as e:
        logger.error(f"\nValidation error: {e}")
        sys.exit(1)
    except GenerationError as e:
        logger.error(f"\nGeneration error: {e}")
        sys.exit(1)
    except TemplateRenderError as e:
        logger.error(f"\nTemplate error: {e}")
        sys.exit(1)
    except FileExistsError as e:
        logger.error(f"\nError: {e}")
        logger.error("Use --force flag (future feature) to overwrite existing files.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nUnexpected error: {e}")
        logger.error("Please report this issue with the error message above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

