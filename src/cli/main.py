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
        '--cloud',
        action='store_true',
        help='Include cloud infrastructure (Terraform) for OCI, AWS, or GCP'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {VERSION}'
    )
    parser.add_argument(
        'command',
        nargs='?',
        choices=['plugins', 'ui', 'registry', 'docs', 'secrets'],
        help='Command to run (plugins: list available plugins, ui: launch interactive TUI, registry: manage template registry, docs: generate documentation, secrets: manage secrets)'
    )
    parser.add_argument(
        'registry_subcommand',
        nargs='?',
        choices=['list', 'install', 'refresh', 'uninstall'],
        help='Registry subcommand (list, install, refresh, uninstall)'
    )
    parser.add_argument(
        'registry_arg',
        nargs='?',
        help='Argument for registry subcommand (template name for install/uninstall, URL for refresh)'
    )
    return parser.parse_args()


def main():
    """Main CLI entry point."""
    args = parse_args()
    
    # Handle plugins command
    if args.command == 'plugins':
        from ..plugins import get_plugin_manager
        manager = get_plugin_manager()
        plugins = manager.get_all_plugins()
        
        if not plugins:
            print("No plugins found.")
            return
        
        print("Available plugins:")
        print("=" * 60)
        for name, plugin in plugins.items():
            print(f"  {name} (v{plugin.version})")
            templates = manager.get_plugin_templates(name)
            if templates:
                print(f"    Templates: {', '.join(templates.keys())}")
        print("=" * 60)
        return
    
    # Handle ui command
    if args.command == 'ui':
        from ..ui.app import ui
        ui(
            preset=args.preset,
            with_ci=args.with_ci,
            dry_run=args.dry_run,
        )
        return
    
    # Handle registry command
    if args.command == 'registry':
        from .registry import (
            cmd_registry_list,
            cmd_registry_install,
            cmd_registry_refresh,
            cmd_registry_uninstall,
        )
        
        subcommand = args.registry_subcommand or 'list'
        
        if subcommand == 'list':
            cmd_registry_list()
        elif subcommand == 'install':
            if not args.registry_arg:
                print("Error: Template name required for 'install' command", file=sys.stderr)
                print("Usage: devforge registry install <template_name>", file=sys.stderr)
                sys.exit(1)
            cmd_registry_install(args.registry_arg)
        elif subcommand == 'refresh':
            cmd_registry_refresh(args.registry_arg)
        elif subcommand == 'uninstall':
            if not args.registry_arg:
                print("Error: Template name required for 'uninstall' command", file=sys.stderr)
                print("Usage: devforge registry uninstall <template_name>", file=sys.stderr)
                sys.exit(1)
            cmd_registry_uninstall(args.registry_arg)
        return
    
    # Handle docs command
    if args.command == 'docs':
        from .docs import cmd_docs_generate
        cmd_docs_generate()
        return
    
    # Handle secrets command
    if args.command == 'secrets':
        from .secrets import (
            cmd_secrets_init,
            cmd_secrets_set,
            cmd_secrets_get,
            cmd_secrets_list,
            cmd_secrets_inject,
            cmd_secrets_sync_github
        )
        
        if not args.secrets_subcommand:
            parser.print_help()
            sys.exit(1)
        
        if args.secrets_subcommand == 'init':
            cmd_secrets_init()
        elif args.secrets_subcommand == 'set':
            if not args.secrets_key:
                print("❌ Error: Secret key required for 'set' command", file=sys.stderr)
                sys.exit(1)
            cmd_secrets_set(args.secrets_key, args.secrets_value)
        elif args.secrets_subcommand == 'get':
            if not args.secrets_key:
                print("❌ Error: Secret key required for 'get' command", file=sys.stderr)
                sys.exit(1)
            cmd_secrets_get(args.secrets_key)
        elif args.secrets_subcommand == 'list':
            cmd_secrets_list()
        elif args.secrets_subcommand == 'inject':
            cmd_secrets_inject()
        elif args.secrets_subcommand == 'sync-github':
            cmd_secrets_sync_github(args.repo)
        return
    
    try:
        # Collect configuration from user
        config = collect_project_config(
            preset_path=args.preset if args.preset else None,
            include_ci=args.with_ci,
            include_cloud=args.cloud
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
        plugins_dir = Path(__file__).parent.parent / "plugins"
        generator = ProjectGenerator(templates_dir, file_writer, plugins_dir)
        
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

