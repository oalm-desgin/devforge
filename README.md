# DevForge

[![CI](https://github.com/yourusername/devforge/workflows/CI/badge.svg)](https://github.com/yourusername/devforge/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](https://github.com/yourusername/devforge/actions)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/yourusername/devforge/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Security](https://img.shields.io/badge/security-scanning-brightgreen.svg)](https://github.com/yourusername/devforge/actions)

**DevForge** is a powerful command-line tool that generates complete, production-ready local development environments for web projects in one command. Stop spending hours setting up project scaffolding—DevForge does it for you.

## 🚀 Features

- ✅ **Full Stack Generation**: Create complete projects with frontend, backend, and database
- ✅ **Multiple Stack Support**: React + TypeScript + Vite, FastAPI, PostgreSQL
- ✅ **Docker Integration**: Automatic Docker Compose configuration
- ✅ **CI/CD Ready**: Optional Jenkins and GitHub Actions templates
- ✅ **Secure Secrets Management**: Encrypted secrets with GitHub sync and leak scanning
- ✅ **Safe & Validated**: Comprehensive validation prevents common mistakes
- ✅ **Dry-Run Mode**: Preview changes before generating
- ✅ **Preset Support**: Reuse configurations with JSON presets
- ✅ **Zero Overwrites**: Never accidentally overwrite existing files

## 📦 Installation

### From Source

```bash
git clone https://github.com/yourusername/devforge.git
cd devforge
pip install -e .
```

### From PyPI (Coming Soon)

```bash
pip install devforge
```

## 🎯 Quick Start

After installation, simply run:

```bash
devforge
```

The tool will interactively guide you through:
- Project name and destination
- Component selection (frontend, backend, database)
- Configuration options

In seconds, you'll have a fully configured development environment ready to use!

## 📖 Usage

### Basic Usage

```bash
devforge
```

Or run directly:

```bash
python src/cli/main.py
```

### Dry-Run Mode

Preview what will be generated without creating any files:

```bash
devforge --dry-run
```

This will show you:
- All directories that would be created
- All files that would be written
- No actual filesystem changes

### Preset Configuration

Use a JSON preset file to set default answers to prompts:

```bash
devforge --preset my-preset.json
```

Example preset file (`my-preset.json`):

```json
{
  "default_frontend": true,
  "default_backend": true,
  "default_database": true,
  "frontend_port": 3000,
  "backend_port": 8000,
  "database_port": 5432
}
```

Preset values are used as defaults, but you can still override them interactively.

### CI/CD Integration

Include CI configuration files in your generated project:

```bash
devforge --with-ci
```

This generates:
- `Jenkinsfile` for Jenkins pipelines
- `.github/workflows/ci.yml` for GitHub Actions

### Interactive TUI Mode

Launch the interactive Rich TUI interface:

```bash
devforge ui
```

The TUI provides:
- Visual project configuration wizard
- Component toggles with keyboard navigation
- Database engine selector
- Real-time port preview
- Dry-run preview before generation

Options:
- `--preset <path>`: Load preset defaults
- `--with-ci`: Include CI configuration
- `--dry-run`: Preview without creating files

### Template Registry

Manage remote templates from the registry:

```bash
# List available templates
devforge registry list

# Refresh registry from remote
devforge registry refresh

# Install a template
devforge registry install <template_name>

# Uninstall a template
devforge registry uninstall <template_name>
```

The registry stores templates in `~/.devforge/registry.json` and caches downloaded templates in `~/.devforge/templates/`. Templates work offline after the first download.

### Cloud Infrastructure (Terraform)

Generate Terraform configurations for cloud deployment:

```bash
devforge --cloud
```

This will prompt you to select a cloud provider:
- **Oracle Cloud Infrastructure (OCI)**
- **Amazon Web Services (AWS)**
- **Google Cloud Platform (GCP)**

The generated `terraform/` directory includes:
- VPC/VCN configuration
- Subnet setup
- Load balancer configuration
- Compute instance setup
- Security groups/firewall rules
- Environment variable examples

After generation, navigate to `terraform/` and run:
```bash
terraform init
terraform plan
terraform apply
```

### Documentation Website

Every generated project includes a complete MkDocs documentation site:

```bash
# View documentation
cd docs
pip install -r ../docs-requirements.txt
mkdocs serve
```

The documentation includes:
- **Installation Guide** - Setup and installation instructions
- **Usage Guide** - How to use the project
- **Environment Variables** - Configuration reference
- **Secrets Management** - Secure secret storage and injection
- **CI/CD Configuration** - If `--with-ci` was used
- **Cloud Infrastructure** - If `--cloud` was used

**Publishing to GitHub Pages:**

1. Build the documentation:
   ```bash
   mkdocs build
   ```

2. Configure GitHub Pages in repository settings to use `gh-pages` branch

3. Add GitHub Actions workflow (automated):
   ```yaml
   name: Deploy Docs
   on:
     push:
       branches: [main]
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: actions/setup-python@v4
         - run: pip install -r docs-requirements.txt
         - run: mkdocs gh-deploy --force
   ```

### Version Information

Check the installed version:

```bash
devforge --version
```

## 🛠️ Supported Stacks

### Frontend
- **React** + **TypeScript** + **Vite** + **Tailwind CSS**

### Backend
- **FastAPI** (Python)

### Database
- **PostgreSQL**

## 🎨 Component Combinations

Generate projects with any valid combination:

| Combination | Description |
|------------|-------------|
| **Full Stack** | Frontend + Backend + Database |
| **Backend + Database** | API-only project |
| **Backend Only** | API without database |
| **Frontend Only** | Standalone frontend application |

## 🔒 Safety Features

- ✅ **No Overwrites**: Existing files are never overwritten without explicit confirmation
- ✅ **Validation**: Comprehensive validation of project names, paths, and configurations
- ✅ **Reserved Names**: Prevents use of reserved names (test, temp, example, etc.)
- ✅ **Port Validation**: Ensures no port conflicts between services
- ✅ **Empty Destination**: Validates that destination directory is empty or doesn't exist

## 📦 Generated Project Includes

Every generated project comes with:

- ✅ Complete folder structure
- ✅ Working starter code with examples
- ✅ Docker Compose configuration
- ✅ Environment variable files (`.env`)
- ✅ Comprehensive README with instructions
- ✅ Git ignore rules
- ✅ Optional CI/CD configuration (with `--with-ci`)

## ⚙️ Command-Line Options

| Option | Description |
|--------|-------------|
| `ui` | Launch interactive Rich TUI interface |
| `plugins` | List available template plugins |
| `registry list` | List available templates in registry |
| `registry refresh` | Refresh registry from remote URL |
| `registry install <name>` | Install a template from registry |
| `registry uninstall <name>` | Uninstall a template |
| `docs` | Generate documentation for existing project |
| `secrets init` | Initialize encrypted secrets store |
| `secrets set <KEY> [VALUE]` | Set a secret value |
| `secrets get <KEY>` | Get a secret value |
| `secrets list` | List all secret keys |
| `secrets inject` | Inject secrets into .env.secrets for runtime |
| `secrets sync-github [--repo OWNER/REPO]` | Sync secrets to GitHub repository |
| `--cloud` | Include cloud infrastructure (Terraform) for OCI, AWS, or GCP |
| `--dry-run` | Preview generation without creating files |
| `--preset <path>` | Load defaults from JSON preset file |
| `--with-ci` | Include CI configuration files (Jenkinsfile, GitHub Actions) |
| `--version` | Show version information and exit |
| `--help` | Show help message and exit |

## 🐛 Error Handling

DevForge provides clear, user-friendly error messages:

- **Validation Errors**: Invalid configurations are caught early with helpful messages
- **Generation Errors**: Template or file system issues are reported clearly
- **Template Errors**: Missing or invalid templates are identified

## 🗺️ Roadmap

### Planned Features

- [ ] Additional frontend frameworks (Vue, Angular)
- [ ] Additional backend frameworks (Spring Boot, Express.js)
- [ ] Additional databases (MongoDB, MySQL)
- [ ] Kubernetes manifests generation
- [ ] Helm chart templates
- [ ] Custom template support
- [ ] Plugin system for extensibility

### Version History

- **v0.1.0** (Current): Initial release with React, FastAPI, PostgreSQL support

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/yourusername/devforge.git
cd devforge
pip install -e ".[dev]"
```

### Setting Up Git Hooks

To enable commit message validation:

**Linux/macOS:**
```bash
chmod +x scripts/setup_git_hooks.sh
./scripts/setup_git_hooks.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\setup_git_hooks.ps1
```

This will install a pre-commit hook that validates commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/) format.

### Commit Message Format

All commits must follow Conventional Commits format:

- `feat: add new feature`
- `fix: fix bug`
- `chore: maintenance task`
- `docs: documentation change`
- `test: add or update tests`
- `refactor: code refactoring`
- `feat!: breaking change` (use `!` for breaking changes)

### CI/CD

The project uses GitHub Actions for continuous integration:

- **Linting**: Runs `ruff` and `black --check` on all Python code
- **Testing**: Runs full test suite on Python 3.10, 3.11, and 3.12 across Ubuntu, Windows, and macOS
- **Coverage**: Enforces 85% minimum code coverage
- **Security**: Scans dependencies with `pip-audit` for vulnerabilities
- **Packaging**: Automatically builds packages on push to main
- **Releases**: Automatically creates GitHub releases on version tags (v*)

### Version Bumping

Version is automatically bumped based on commit types:

- `feat:` → minor version bump
- `fix:` → patch version bump
- Breaking changes (`!`) → major version bump

Run `python scripts/bump_version.py` to bump the version before creating a release tag.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python and Jinja2
- Inspired by the need for faster project setup

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/devforge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/devforge/discussions)

---


