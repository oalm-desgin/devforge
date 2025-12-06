#!/usr/bin/env python3
"""Validate commit message format according to Conventional Commits."""

import re
import sys

def validate_commit_message(message: str) -> bool:
    """
    Validate commit message follows Conventional Commits format.
    
    Valid formats:
    - feat: description
    - fix: description
    - chore: description
    - docs: description
    - test: description
    - refactor: description
    - feat!: breaking change
    - feat(scope): description
    """
    # Pattern for conventional commits
    pattern = r'^(feat|fix|chore|docs|test|refactor)(\(.+\))?(!)?: .+'
    
    # Check if message matches pattern
    if not re.match(pattern, message, re.IGNORECASE):
        return False
    
    # Check minimum length
    if len(message) < 10:
        return False
    
    return True

def main():
    """Main entry point for git hook."""
    # Get commit message from stdin or file
    if len(sys.argv) > 1:
        commit_msg_file = sys.argv[1]
        with open(commit_msg_file, 'r') as f:
            message = f.read().strip()
    else:
        message = sys.stdin.read().strip()
    
    # Remove comments and empty lines
    lines = [line for line in message.split('\n') if line and not line.startswith('#')]
    if not lines:
        print("Error: Empty commit message")
        sys.exit(1)
    
    # Validate first line (subject)
    subject = lines[0]
    if not validate_commit_message(subject):
        print("Error: Invalid commit message format")
        print("")
        print("Commit messages must follow Conventional Commits format:")
        print("  feat: add new feature")
        print("  fix: fix bug")
        print("  chore: maintenance task")
        print("  docs: documentation change")
        print("  test: add or update tests")
        print("  refactor: code refactoring")
        print("  feat!: breaking change")
        print("  feat(scope): scoped change")
        print("")
        print(f"Your message: {subject}")
        sys.exit(1)
    
    print(f"✓ Valid commit message: {subject}")
    sys.exit(0)

if __name__ == '__main__':
    main()

