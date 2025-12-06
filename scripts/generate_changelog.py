#!/usr/bin/env python3
"""Generate CHANGELOG.md from git commits."""

import subprocess
import re
from datetime import datetime
from typing import List, Dict, Tuple

def get_commits_since_tag(tag: str = None) -> List[str]:
    """Get all commits since the last tag or all commits if no tag."""
    try:
        if tag:
            result = subprocess.run(
                ['git', 'log', f'{tag}..HEAD', '--pretty=format:%H|%s|%b'],
                capture_output=True,
                text=True,
                check=True
            )
        else:
            result = subprocess.run(
                ['git', 'log', '--pretty=format:%H|%s|%b'],
                capture_output=True,
                text=True,
                check=True
            )
        return [line for line in result.stdout.strip().split('\n') if line]
    except subprocess.CalledProcessError:
        return []

def get_latest_tag() -> str:
    """Get the latest git tag."""
    try:
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def parse_commit(commit_line: str) -> Dict[str, str]:
    """Parse a commit line into components."""
    parts = commit_line.split('|', 2)
    if len(parts) >= 2:
        return {
            'hash': parts[0],
            'subject': parts[1],
            'body': parts[2] if len(parts) > 2 else ''
        }
    return {'hash': '', 'subject': commit_line, 'body': ''}

def categorize_commits(commits: List[str]) -> Dict[str, List[Dict[str, str]]]:
    """Categorize commits by type."""
    categories = {
        'feat': [],
        'fix': [],
        'chore': [],
        'docs': [],
        'test': [],
        'refactor': [],
        'breaking': []
    }
    
    for commit_line in commits:
        commit = parse_commit(commit_line)
        subject = commit['subject']
        
        # Check for breaking changes
        if '!' in subject or 'BREAKING CHANGE' in commit['body']:
            categories['breaking'].append(commit)
        elif subject.startswith('feat'):
            categories['feat'].append(commit)
        elif subject.startswith('fix'):
            categories['fix'].append(commit)
        elif subject.startswith('chore'):
            categories['chore'].append(commit)
        elif subject.startswith('docs'):
            categories['docs'].append(commit)
        elif subject.startswith('test'):
            categories['test'].append(commit)
        elif subject.startswith('refactor'):
            categories['refactor'].append(commit)
    
    return categories

def generate_changelog(categories: Dict[str, List[Dict[str, str]]], version: str = None) -> str:
    """Generate CHANGELOG.md content."""
    lines = []
    
    if version:
        lines.append(f"# Changelog - Version {version}")
    else:
        lines.append("# Changelog")
    
    lines.append("")
    lines.append(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    if categories['breaking']:
        lines.append("## 🚨 Breaking Changes")
        lines.append("")
        for commit in categories['breaking']:
            subject = commit['subject'].replace('!', '').strip()
            lines.append(f"- {subject}")
        lines.append("")
    
    if categories['feat']:
        lines.append("## ✨ Features")
        lines.append("")
        for commit in categories['feat']:
            subject = commit['subject']
            # Remove type prefix
            subject = re.sub(r'^feat(\(.+\))?:\s*', '', subject, flags=re.IGNORECASE)
            lines.append(f"- {subject}")
        lines.append("")
    
    if categories['fix']:
        lines.append("## 🐛 Bug Fixes")
        lines.append("")
        for commit in categories['fix']:
            subject = commit['subject']
            subject = re.sub(r'^fix(\(.+\))?:\s*', '', subject, flags=re.IGNORECASE)
            lines.append(f"- {subject}")
        lines.append("")
    
    if categories['refactor']:
        lines.append("## ♻️ Refactoring")
        lines.append("")
        for commit in categories['refactor']:
            subject = commit['subject']
            subject = re.sub(r'^refactor(\(.+\))?:\s*', '', subject, flags=re.IGNORECASE)
            lines.append(f"- {subject}")
        lines.append("")
    
    if categories['docs']:
        lines.append("## 📚 Documentation")
        lines.append("")
        for commit in categories['docs']:
            subject = commit['subject']
            subject = re.sub(r'^docs(\(.+\))?:\s*', '', subject, flags=re.IGNORECASE)
            lines.append(f"- {subject}")
        lines.append("")
    
    if categories['test']:
        lines.append("## 🧪 Tests")
        lines.append("")
        for commit in categories['test']:
            subject = commit['subject']
            subject = re.sub(r'^test(\(.+\))?:\s*', '', subject, flags=re.IGNORECASE)
            lines.append(f"- {subject}")
        lines.append("")
    
    if categories['chore']:
        lines.append("## 🔧 Maintenance")
        lines.append("")
        for commit in categories['chore']:
            subject = commit['subject']
            subject = re.sub(r'^chore(\(.+\))?:\s*', '', subject, flags=re.IGNORECASE)
            lines.append(f"- {subject}")
        lines.append("")
    
    return '\n'.join(lines)

def main():
    """Main entry point."""
    import sys
    
    # Get version from tag if provided
    version = None
    if len(sys.argv) > 1:
        version = sys.argv[1]
    else:
        # Try to get from git tag
        tag = get_latest_tag()
        if tag:
            version = tag.lstrip('v')
    
    # Get commits
    commits = get_commits_since_tag(tag if tag else None)
    
    if not commits:
        print("# Changelog")
        print("")
        print("No commits found.")
        return
    
    # Categorize commits
    categories = categorize_commits(commits)
    
    # Generate changelog
    changelog = generate_changelog(categories, version)
    print(changelog)

if __name__ == '__main__':
    main()

