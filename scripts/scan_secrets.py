"""Pre-commit secret leak scanner using entropy and regex detection."""

import re
import sys
from pathlib import Path
from typing import List, Tuple
import math


# Secret patterns (regex)
SECRET_PATTERNS = [
    # AWS keys
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID'),
    (r'aws_secret_access_key\s*[:=]\s*["\']?([A-Za-z0-9/+=]{40})["\']?', 'AWS Secret Access Key'),
    
    # JWT tokens
    (r'eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*', 'JWT Token'),
    
    # API tokens (generic)
    (r'api[_-]?key\s*[:=]\s*["\']?([A-Za-z0-9]{20,})["\']?', 'API Key'),
    (r'apikey\s*[:=]\s*["\']?([A-Za-z0-9]{20,})["\']?', 'API Key'),
    (r'token\s*[:=]\s*["\']?([A-Za-z0-9]{20,})["\']?', 'API Token'),
    
    # Database passwords
    (r'database[_-]?password\s*[:=]\s*["\']?([^\s"\']{8,})["\']?', 'Database Password'),
    (r'db[_-]?password\s*[:=]\s*["\']?([^\s"\']{8,})["\']?', 'Database Password'),
    (r'postgres[_-]?password\s*[:=]\s*["\']?([^\s"\']{8,})["\']?', 'PostgreSQL Password'),
    (r'mysql[_-]?password\s*[:=]\s*["\']?([^\s"\']{8,})["\']?', 'MySQL Password'),
    
    # Private keys
    (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', 'Private Key'),
    (r'-----BEGIN\s+EC\s+PRIVATE\s+KEY-----', 'EC Private Key'),
    (r'-----BEGIN\s+DSA\s+PRIVATE\s+KEY-----', 'DSA Private Key'),
    
    # GitHub tokens
    (r'ghp_[A-Za-z0-9]{36}', 'GitHub Personal Access Token'),
    (r'github[_-]?token\s*[:=]\s*["\']?([A-Za-z0-9]{36,})["\']?', 'GitHub Token'),
    
    # Generic passwords
    (r'password\s*[:=]\s*["\']?([^\s"\']{8,})["\']?', 'Password'),
    (r'pwd\s*[:=]\s*["\']?([^\s"\']{8,})["\']?', 'Password'),
]


def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not text:
        return 0.0
    
    # Count character frequencies
    char_counts = {}
    for char in text:
        char_counts[char] = char_counts.get(char, 0) + 1
    
    # Calculate entropy
    length = len(text)
    entropy = 0.0
    for count in char_counts.values():
        probability = count / length
        entropy -= probability * math.log2(probability)
    
    return entropy


def scan_file(file_path: Path, min_entropy: float = 4.0) -> List[Tuple[int, str, str]]:
    """
    Scan a file for secrets.
    
    Args:
        file_path: Path to file to scan
        min_entropy: Minimum entropy threshold for suspicious strings
        
    Returns:
        List of (line_number, secret_type, matched_text) tuples
    """
    findings = []
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return findings
    
    lines = content.split('\n')
    
    # Check regex patterns
    for line_num, line in enumerate(lines, 1):
        for pattern, secret_type in SECRET_PATTERNS:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                matched_text = match.group(0)
                # Mask the actual secret in output
                if len(matched_text) > 20:
                    display_text = matched_text[:10] + "..." + matched_text[-5:]
                else:
                    display_text = "***MASKED***"
                findings.append((line_num, secret_type, display_text))
    
    # Check high-entropy strings (potential secrets)
    for line_num, line in enumerate(lines, 1):
        # Skip comments and common non-secret patterns
        if line.strip().startswith('#') or line.strip().startswith('//'):
            continue
        
        # Find potential secret values (quoted strings, after =, etc.)
        # Look for strings that look like secrets
        potential_secrets = re.findall(r'["\']([A-Za-z0-9/+=]{20,})["\']', line)
        for secret in potential_secrets:
            entropy = calculate_entropy(secret)
            if entropy >= min_entropy:
                # Additional check: not a common non-secret pattern
                if not re.match(r'^[A-Za-z0-9+/=]+$', secret) or len(secret) < 20:
                    continue
                findings.append((line_num, 'High Entropy String (Potential Secret)', '***MASKED***'))
    
    return findings


def scan_directory(directory: Path, exclude_patterns: List[str] = None) -> List[Tuple[Path, int, str, str]]:
    """
    Scan a directory for secrets.
    
    Args:
        directory: Directory to scan
        exclude_patterns: List of patterns to exclude (e.g., ['*.pyc', '.git'])
        
    Returns:
        List of (file_path, line_number, secret_type, matched_text) tuples
    """
    if exclude_patterns is None:
        exclude_patterns = [
            '*.pyc', '*.pyo', '*.pyd', '__pycache__',
            '.git', '.svn', '.hg', 'node_modules',
            '.secrets.devforge', '.env.secrets',
            '*.log', '*.tmp', '*.swp', '*.swo'
        ]
    
    all_findings = []
    
    for file_path in directory.rglob('*'):
        if file_path.is_dir():
            continue
        
        # Check if file should be excluded
        should_exclude = False
        for pattern in exclude_patterns:
            if pattern in str(file_path) or file_path.match(pattern):
                should_exclude = True
                break
        if should_exclude:
            continue
        
        findings = scan_file(file_path)
        for line_num, secret_type, matched_text in findings:
            all_findings.append((file_path, line_num, secret_type, matched_text))
    
    return all_findings


def main():
    """Main entry point for secret scanner."""
    if len(sys.argv) < 2:
        print("Usage: scan_secrets.py <directory>", file=sys.stderr)
        sys.exit(1)
    
    scan_dir = Path(sys.argv[1])
    if not scan_dir.exists():
        print(f"❌ Error: Directory not found: {scan_dir}", file=sys.stderr)
        sys.exit(1)
    
    findings = scan_directory(scan_dir)
    
    if findings:
        print("❌ SECRET LEAK DETECTED!", file=sys.stderr)
        print(f"\nFound {len(findings)} potential secret(s):\n", file=sys.stderr)
        
        for file_path, line_num, secret_type, matched_text in findings:
            rel_path = file_path.relative_to(scan_dir)
            print(f"  {rel_path}:{line_num} - {secret_type}", file=sys.stderr)
            print(f"    {matched_text}", file=sys.stderr)
        
        print("\n⚠️  Commit blocked. Remove secrets before committing.", file=sys.stderr)
        sys.exit(1)
    else:
        print("OK: No secrets detected")
        sys.exit(0)


if __name__ == '__main__':
    main()

