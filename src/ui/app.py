"""Interactive Rich TUI application for DevForge."""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich import box
import typer

from ..core.config_models import (
    ProjectConfig,
    FrontendConfig,
    BackendConfig,
    DatabaseConfig,
    PortConfig,
)
from ..core.validators import (
    validate_project_name,
    validate_path,
    validate_project_config,
    is_port_free,
    find_free_port,
)
from ..core.preset_loader import load_preset, get_preset_default
from ..core.errors import ValidationError
from ..core.file_writer import FileWriter
from ..core.project_generator import ProjectGenerator
from ..core.version import VERSION

console = Console()
app = typer.Typer(help="DevForge Interactive UI")


def show_header() -> None:
    """Display application header."""
    header = Text()
    header.append("DevForge", style="bold blue")
    header.append(" - Development Environment Generator", style="dim")
    header.append(f"\nVersion {VERSION}", style="dim")
    
    console.print(Panel(header, box=box.ROUNDED, border_style="blue"))


def prompt_project_name_ui(default: Optional[str] = None) -> str:
    """Prompt for project name with Rich UI."""
    while True:
        prompt_text = "Enter project name"
        if default:
            prompt_text += f" [{default}]"
        prompt_text += ": "
        
        name = Prompt.ask(prompt_text, default=default or "").strip()
        
        if not name and default:
            name = default
        
        is_valid, error_msg = validate_project_name(name)
        if is_valid:
            return name
        
        console.print(f"[red]Error:[/red] {error_msg}")
        console.print("[dim]Please try again.[/dim]\n")


def prompt_parent_directory_ui(default: Optional[str] = None) -> Path:
    """Prompt for parent directory with Rich UI."""
    while True:
        prompt_text = "Enter parent directory path"
        if default:
            prompt_text += f" [{default}]"
        prompt_text += " (or press Enter for current directory): "
        
        path_input = Prompt.ask(prompt_text, default=default or "").strip()
        
        if not path_input:
            parent_path = Path.cwd()
        else:
            parent_path = Path(path_input).expanduser().resolve()
        
        is_valid, error_msg = validate_path(parent_path)
        if is_valid:
            return parent_path
        
        console.print(f"[red]Error:[/red] {error_msg}")
        console.print("[dim]Please try again.[/dim]\n")


def prompt_component_toggle(component_name: str, default: Optional[bool] = None) -> bool:
    """Prompt for component inclusion with toggle."""
    default_text = ""
    if default is True:
        default_text = " [Y/n]"
    elif default is False:
        default_text = " [y/N]"
    else:
        default_text = " [y/n]"
    
    prompt_text = f"Include {component_name}?{default_text}"
    
    if default is not None:
        return Confirm.ask(prompt_text, default=default)
    else:
        return Confirm.ask(prompt_text)


def prompt_database_engine_ui(default: Optional[str] = None) -> str:
    """Prompt for database engine selection with Rich UI."""
    engines = {
        "1": ("postgres", "PostgreSQL"),
        "2": ("mongo", "MongoDB"),
        "3": ("redis", "Redis"),
    }
    
    table = Table(title="Select Database Engine", box=box.ROUNDED)
    table.add_column("Option", style="cyan", no_wrap=True)
    table.add_column("Engine", style="magenta")
    table.add_column("Default Port", style="green")
    
    table.add_row("1", "PostgreSQL", "5432")
    table.add_row("2", "MongoDB", "27017")
    table.add_row("3", "Redis", "6379")
    
    console.print(table)
    
    while True:
        default_text = ""
        if default:
            default_text = f" [{default}]"
        default_text += ": "
        
        choice = Prompt.ask(f"Select database engine{default_text}", default=default or "1").strip()
        
        if choice in engines:
            return engines[choice][0]
        
        console.print("[red]Invalid choice. Please enter 1, 2, or 3.[/red]\n")


def show_port_preview(config: Dict[str, Any]) -> None:
    """Display port preview in a table."""
    table = Table(title="Resolved Ports", box=box.ROUNDED)
    table.add_column("Service", style="cyan")
    table.add_column("Port", style="green", justify="right")
    table.add_column("URL", style="blue")
    
    if config.get("frontend"):
        port = config.get("frontend_port", 3000)
        table.add_row("Frontend", str(port), f"http://localhost:{port}")
    
    if config.get("backend"):
        port = config.get("backend_port", 8000)
        table.add_row("Backend", str(port), f"http://localhost:{port}/health")
    
    if config.get("database"):
        port = config.get("database_port", 5432)
        engine = config.get("database_stack", "postgres")
        table.add_row(f"Database ({engine})", str(port), f"localhost:{port}")
    
    console.print("\n")
    console.print(table)
    console.print()


def show_preview_summary(config: Dict[str, Any]) -> None:
    """Show preview summary before generation."""
    summary = Table(title="Project Configuration Summary", box=box.ROUNDED)
    summary.add_column("Setting", style="cyan")
    summary.add_column("Value", style="green")
    
    summary.add_row("Project Name", config.get("project_name", ""))
    summary.add_row("Destination", str(config.get("destination_path", "")))
    
    components = []
    if config.get("frontend"):
        components.append("Frontend (React + TS + Vite)")
    if config.get("backend"):
        components.append("Backend (FastAPI)")
    if config.get("database"):
        db_stack = config.get("database_stack", "postgres")
        components.append(f"Database ({db_stack})")
    
    summary.add_row("Components", ", ".join(components) if components else "None")
    
    if config.get("include_ci"):
        summary.add_row("CI/CD", "Yes (Jenkins + GitHub Actions)")
    
    console.print("\n")
    console.print(summary)
    console.print()


def resolve_ports_ui(config: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve ports with progress indication."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Resolving ports...", total=None)
        
        # Resolve frontend port
        if config.get("frontend"):
            default_port = 3000
            if not is_port_free(default_port):
                config["frontend_port"] = find_free_port(default_port)
            else:
                config["frontend_port"] = default_port
        
        # Resolve backend port
        if config.get("backend"):
            default_port = 8000
            if not is_port_free(default_port):
                config["backend_port"] = find_free_port(default_port)
            else:
                config["backend_port"] = default_port
        
        # Resolve database port
        if config.get("database"):
            db_stack = config.get("database_stack", "postgres")
            defaults = {
                "postgres": 5432,
                "mongo": 27017,
                "redis": 6379,
            }
            default_port = defaults.get(db_stack, 5432)
            if not is_port_free(default_port):
                config["database_port"] = find_free_port(default_port)
            else:
                config["database_port"] = default_port
        
        progress.update(task, completed=100)
    
    return config


def run_wizard(preset_path: Optional[Path] = None, include_ci: bool = False) -> ProjectConfig:
    """Run the interactive wizard to collect project configuration."""
    show_header()
    
    # Load preset if provided
    preset: Optional[Dict[str, Any]] = None
    if preset_path:
        try:
            preset = load_preset(preset_path)
        except ValidationError as e:
            console.print(f"[red]Error loading preset:[/red] {e}")
            sys.exit(1)
    
    console.print("\n[bold]Let's create your development environment![/bold]\n")
    
    # Step 1: Project name
    default_name = get_preset_default(preset, "project_name", None)
    project_name = prompt_project_name_ui(default_name)
    
    # Step 2: Parent directory
    default_path = get_preset_default(preset, "parent_path", None)
    parent_path = prompt_parent_directory_ui(default_path)
    destination_path = parent_path / project_name
    
    console.print(f"\n[dim]Project will be created in:[/dim] [cyan]{destination_path}[/cyan]\n")
    
    # Step 3: Component selection
    console.print("[bold]Select components to include:[/bold]\n")
    
    default_frontend = get_preset_default(preset, "default_frontend", None)
    include_frontend = prompt_component_toggle("Frontend", default_frontend)
    
    default_backend = get_preset_default(preset, "default_backend", True)
    include_backend = prompt_component_toggle("Backend", default_backend)
    
    include_database = False
    database_stack = "postgres"
    
    if include_backend:
        default_database = get_preset_default(preset, "default_database", None)
        include_database = prompt_component_toggle("Database", default_database)
        
        if include_database:
            default_db_stack = get_preset_default(preset, "database_stack", None)
            if default_db_stack:
                # Map preset value to option number
                stack_map = {"postgres": "1", "mongo": "2", "redis": "3"}
                default_option = stack_map.get(default_db_stack, "1")
            else:
                default_option = "1"
            
            console.print()
            database_stack = prompt_database_engine_ui(default_option)
    else:
        console.print("[dim]Database requires backend. Skipping database selection.[/dim]\n")
    
    # Validate configuration
    is_valid, error_msg = validate_project_config(
        include_frontend,
        include_backend,
        include_database
    )
    if not is_valid:
        console.print(f"[red]Error:[/red] {error_msg}")
        sys.exit(1)
    
    # Build configuration dict
    config_dict: Dict[str, Any] = {
        "project_name": project_name,
        "destination_path": destination_path,
        "frontend": include_frontend,
        "backend": include_backend,
        "database": include_database,
        "database_stack": database_stack,
        "include_ci": include_ci,
    }
    
    # Resolve ports
    config_dict = resolve_ports_ui(config_dict)
    
    # Show port preview
    show_port_preview(config_dict)
    
    # Build ProjectConfig
    frontend = None
    if include_frontend:
        frontend_port = get_preset_default(preset, "frontend_port", config_dict.get("frontend_port", 3000))
        frontend = FrontendConfig(
            stack="react_ts_vite",
            port=frontend_port,
            build_command="npm run build",
            dev_command="npm run dev",
        )
        config_dict["frontend_port"] = frontend_port
    
    backend = None
    if include_backend:
        backend_port = get_preset_default(preset, "backend_port", config_dict.get("backend_port", 8000))
        backend = BackendConfig(
            stack="fastapi",
            port=backend_port,
            language="python",
        )
        config_dict["backend_port"] = backend_port
    
    database = None
    if include_database:
        database_port = get_preset_default(
            preset,
            "database_port",
            config_dict.get("database_port", DatabaseConfig.get_default_port(database_stack))
        )
        database = DatabaseConfig(
            stack=database_stack,
            port=database_port,
            name=project_name.lower().replace("-", "_"),
            user="devforge_user",
            password="devforge_pass",
        )
        config_dict["database_port"] = database_port
    
    # Create PortConfig
    ports = PortConfig(
        frontend_port=config_dict.get("frontend_port"),
        backend_port=config_dict.get("backend_port"),
        database_port=config_dict.get("database_port", 5432),
    )
    
    project_config = ProjectConfig(
        project_name=project_name,
        destination_path=destination_path,
        frontend=frontend,
        backend=backend,
        database=database,
        ports=ports,
        docker_network=f"{project_name}_network",
        include_ci=include_ci,
    )
    
    return project_config


def show_dry_run_preview(config: ProjectConfig) -> None:
    """Show dry-run preview of what would be generated."""
    console.print("\n[bold yellow]DRY RUN MODE[/bold yellow] - No files will be created\n")
    
    show_preview_summary({
        "project_name": config.project_name,
        "destination_path": config.destination_path,
        "frontend": config.frontend is not None,
        "backend": config.backend is not None,
        "database": config.database is not None,
        "database_stack": config.database.stack if config.database else None,
        "include_ci": config.include_ci,
    })


@app.command()
def ui(
    preset: Optional[str] = typer.Option(None, "--preset", "-p", help="Path to JSON preset file"),
    with_ci: bool = typer.Option(False, "--with-ci", help="Include CI configuration files"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without creating files"),
) -> None:
    """
    Launch interactive TUI for project generation.
    """
    try:
        # Run wizard
        preset_path = Path(preset) if preset else None
        project_config = run_wizard(preset_path, with_ci)
        
        # Confirm before generation
        console.print()
        if not dry_run:
            if not Confirm.ask("[bold]Generate project with these settings?[/bold]", default=True):
                console.print("[yellow]Generation cancelled.[/yellow]")
                sys.exit(0)
        
        # Initialize file writer
        file_writer = FileWriter(dry_run=dry_run)
        
        if dry_run:
            # Show dry-run preview
            show_dry_run_preview(project_config)
            
            # Initialize generator to populate operations
            templates_dir = Path(__file__).parent.parent / "templates"
            plugins_dir = Path(__file__).parent.parent / "plugins"
            generator = ProjectGenerator(templates_dir, file_writer, plugins_dir)
            generator.generate(project_config)
            
            # Show operations
            operations = file_writer.get_operations_summary()
            if operations:
                table = Table(title="Files That Would Be Created", box=box.ROUNDED)
                table.add_column("Type", style="cyan")
                table.add_column("Path", style="green")
                
                for op_type, op_path in operations[:20]:  # Show first 20
                    table.add_row(op_type, str(op_path))
                
                if len(operations) > 20:
                    table.add_row("...", f"and {len(operations) - 20} more")
                
                console.print(table)
                console.print()
        else:
            # Initialize project generator
            templates_dir = Path(__file__).parent.parent / "templates"
            plugins_dir = Path(__file__).parent.parent / "plugins"
            generator = ProjectGenerator(templates_dir, file_writer, plugins_dir)
            
            # Generate with progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Generating project...", total=None)
                generator.generate(project_config)
                progress.update(task, completed=100)
            
            # Success message
            console.print("\n[bold green]✅ Project ready![/bold green]\n")
            
            # Show final summary
            show_port_preview({
                "frontend": project_config.frontend is not None,
                "backend": project_config.backend is not None,
                "database": project_config.database is not None,
                "frontend_port": project_config.frontend.port if project_config.frontend else None,
                "backend_port": project_config.backend.port if project_config.backend else None,
                "database_port": project_config.database.port if project_config.database else None,
                "database_stack": project_config.database.stack if project_config.database else None,
            })
            
            console.print(f"[dim]Next steps:[/dim]")
            console.print(f"  [cyan]cd {project_config.destination_path.name}[/cyan]")
            console.print(f"  [cyan]docker compose up[/cyan]\n")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(1)
    except ValidationError as e:
        console.print(f"\n[red]Validation error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {e}")
        sys.exit(1)


def main() -> None:
    """Entry point for UI command."""
    app()


if __name__ == "__main__":
    main()

