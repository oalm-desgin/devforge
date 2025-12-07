# DevForge

[![CI](https://github.com/yourusername/devforge/workflows/CI/badge.svg)](https://github.com/yourusername/devforge/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](https://github.com/yourusername/devforge/actions)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/yourusername/devforge/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Security](https://img.shields.io/badge/security-scanning-brightgreen.svg)](https://github.com/yourusername/devforge/actions)

DevForge

By Omar Al Moumen

DevForge is a full-stack development environment generator that instantly scaffolds production-ready web projects with a complete local infrastructure. It removes the repetitive setup of frontend, backend, databases, Docker, CI/CD, secrets, and documentation into a single automated workflow.

Built entirely in Python, DevForge is designed for developer productivity, DevOps automation, and secure project bootstrapping.


🚀 Key Features

✅ Full Stack Generation – Frontend, backend, and database in one command

✅ Modern Tech Stack – React + TypeScript + Vite, FastAPI, PostgreSQL

✅ Docker Ready – Automatic Docker Compose setup

✅ CI/CD Automation – Jenkins + GitHub Actions templates

✅ Secure Secrets Manager – Encrypted secrets with GitHub sync + leak scanning

✅ MkDocs Documentation Generator – Auto-generated developer docs website

✅ Interactive TUI – Rich terminal UI for configuration

✅ Dry-Run Mode – Preview filesystem changes before generation

✅ Preset System – Reusable JSON configuration profiles

✅ Zero Overwrite Protection – Never destroys existing files


🏗️ Why DevForge Exists

Setting up a new development environment repeatedly is slow, error-prone, and inconsistent. DevForge solves this by automating:

Infrastructure setup

Service configuration

Secrets handling

CI/CD pipelines

Documentation generation

This makes it ideal for:

Internships and hackathons

Startup environments

Academic projects

Rapid prototyping

Team onboarding

📦 Installation
From Source
git clone https://github.com/<your-username>/devforge.git
cd devforge
pip install -e .


⚡ Quick Start
devforge


You will be guided through:

Project name & destination

Frontend, backend, database selection

Port configuration

Optional CI/CD

Optional cloud infrastructure

In seconds, a fully functional environment is generated.

🖥️ Example Commands
Dry Run
devforge --dry-run

With CI/CD
devforge --with-ci

With Cloud (Terraform)
devforge --cloud

Using Presets
devforge --preset my-preset.json

Launch Interactive TUI
devforge ui


🔐 Secrets Management (Security Focus)

DevForge includes a full encrypted secrets system:

devforge secrets init
devforge secrets set DB_PASSWORD mypassword
devforge secrets get DB_PASSWORD
devforge secrets list
devforge secrets inject
devforge secrets sync-github


Security guarantees:

Encrypted at rest using Fernet (AES)

Platform-secure key storage

No plaintext secrets in repositories

Pre-commit secret leak scanner

CI validation for secret exposure


📚 Auto-Generated Documentation Website

Every project includes a live MkDocs website:

pip install -r docs-requirements.txt
mkdocs serve


Included pages:

Installation guide

Usage guide

Environment variables

Secrets management

CI/CD documentation

Cloud infrastructure (if enabled)

☁️ Cloud Infrastructure (Terraform)

Supports:

Oracle Cloud Infrastructure (OCI)

AWS

Google Cloud

Auto-generates:

Networks

Subnets

Security rules

Instances

Load balancers

🛠️ Supported Stacks
Frontend

React

TypeScript

Vite

Tailwind CSS

Backend

FastAPI (Python)

Database

PostgreSQL

🧩 Project Combinations
Mode	Description
Full Stack	Frontend + Backend + Database
API Only	Backend + Database
Backend Only	API without DB
Frontend Only	Standalone app
⚙️ CLI Command Reference
Command	Description
devforge	Start interactive generator
devforge ui	Launch TUI
devforge docs	Generate documentation
devforge plugins	List plugins
devforge registry list	List templates
devforge secrets init	Init encrypted store
devforge secrets set	Store secret
devforge secrets get	Retrieve secret
devforge secrets inject	Inject into runtime
devforge --cloud	Add Terraform
devforge --with-ci	Add CI/CD
devforge --dry-run	Preview without writing

🧠 Engineering Highlights 

Designed full CLI architecture using argparse

Implemented encryption with cryptography

Built secure GitHub Secrets synchronization

Designed registry & template plugin system

Implemented filesystem safety validation

Built MkDocs generator with dynamic parsing

Added GitHub Actions & Jenkins CI scaffolding

150+ automated tests for security & generation

Cross-platform support (Windows, Linux, macOS)

🗺️ Roadmap

Kubernetes Helm chart generation

Vue & Angular frontend support

Spring Boot & Express backend support

MongoDB & MySQL support

Custom user templates

Plugin marketplace

🤝 Contributing
git clone https://github.com/<your-username>/devforge.git
cd devforge
pip install -e ".[dev]"


All contributions must follow Conventional Commits.

👤 Author

Omar Al Moumen
Software Developer
Automation • DevOps • Full-Stack • Security

📄 License

MIT License
