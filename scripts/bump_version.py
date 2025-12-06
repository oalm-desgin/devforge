#!/usr/bin/env python3
"""Automatically bump version based on commit messages."""

import re
import subprocess
import sys
from pathlib import Path

def get_commits_since_last_tag() -> list:
    """Get commit messages since the last tag."""
    try:
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True,
            text=True,
            check=True
        )
        last_tag = result.stdout.strip()
        result = subprocess.run(
            ['git', 'log', f'{last_tag}..HEAD', '--pretty=format:%s'],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError:
        # No tags found, get all commits
        result = subprocess.run(
            ['git', 'log', '--pretty=format:%s'],
            capture_output=True,
            text=True,
            check=True
        )
    
    return [line for line in result.stdout.strip().split('\n') if line]

def determine_version_bump(commits: list) -> str:
    """
    Determine version bump type based on commits.
    
    Returns: 'major', 'minor', or 'patch'
    """
    has_breaking = False
    has_feat = False
    has_fix = False
    
    for commit in commits:
        # Check for breaking changes
        if '!' in commit or 'BREAKING CHANGE' in commit.upper():
            has_breaking = True
        elif commit.startswith('feat'):
            has_feat = True
        elif commit.startswith('fix'):
            has_fix = True
    
    if has_breaking:
        return 'major'
    elif has_feat:
        return 'minor'
    elif has_fix:
        return 'patch'
    else:
        return 'patch'  # Default to patch for other changes

def parse_version(version_str: str) -> tuple:
    """Parse version string into (major, minor, patch)."""
    match = re.match(r'(\d+)\.(\d+)\.(\d+)', version_str)
    if match:
        return tuple(int(x) for x in match.groups())
    raise ValueError(f"Invalid version format: {version_str}")

def bump_version(current_version: str, bump_type: str) -> str:
    """Bump version according to type."""
    major, minor, patch = parse_version(current_version)
    
    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    elif bump_type == 'patch':
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

def update_version_file(new_version: str):
    """Update src/core/version.py."""
    version_file = Path('src/core/version.py')
    content = version_file.read_text()
    content = re.sub(
        r'VERSION = "[^"]+"',
        f'VERSION = "{new_version}"',
        content
    )
    version_file.write_text(content)
    print(f"Updated {version_file} to version {new_version}")

def update_pyproject_toml(new_version: str):
    """Update pyproject.toml."""
    pyproject_file = Path('pyproject.toml')
    content = pyproject_file.read_text()
    content = re.sub(
        r'version = "[^"]+"',
        f'version = "{new_version}"',
        content
    )
    pyproject_file.write_text(content)
    print(f"Updated {pyproject_file} to version {new_version}")

def main():
    """Main entry point."""
    # Get current version
    version_file = Path('src/core/version.py')
    current_version = re.search(
        r'VERSION = "([^"]+)"',
        version_file.read_text()
    ).group(1)
    
    print(f"Current version: {current_version}")
    
    # Get commits since last tag
    commits = get_commits_since_last_tag()
    if not commits:
        print("No commits found. Using patch bump.")
        commits = ['chore: version bump']
    
    # Determine bump type
    bump_type = determine_version_bump(commits)
    print(f"Bump type: {bump_type}")
    
    # Calculate new version
    new_version = bump_version(current_version, bump_type)
    print(f"New version: {new_version}")
    
    # Update files
    update_version_file(new_version)
    update_pyproject_toml(new_version)
    
    print(f"\nVersion bumped from {current_version} to {new_version}")
    print(f"Run: git add src/core/version.py pyproject.toml")
    print(f"     git commit -m 'chore: bump version to {new_version}'")

if __name__ == '__main__':
    main()

