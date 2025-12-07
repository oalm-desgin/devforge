#!/bin/bash
# Setup pre-commit hook for secret scanning

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
SCAN_SCRIPT="$SCRIPT_DIR/scan_secrets.py"

if [ ! -d "$HOOKS_DIR" ]; then
    echo "❌ Error: Not a git repository. Run 'git init' first."
    exit 1
fi

if [ ! -f "$SCAN_SCRIPT" ]; then
    echo "❌ Error: Secret scanner script not found: $SCAN_SCRIPT"
    exit 1
fi

PRE_COMMIT_HOOK="$HOOKS_DIR/pre-commit"

# Create or update pre-commit hook
cat > "$PRE_COMMIT_HOOK" << 'EOF'
#!/bin/bash
# Pre-commit hook for secret scanning

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../scripts" && pwd)"
SCAN_SCRIPT="$SCRIPT_DIR/scan_secrets.py"

if [ -f "$SCAN_SCRIPT" ]; then
    python3 "$SCAN_SCRIPT" "$(git rev-parse --show-toplevel)"
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        exit $exit_code
    fi
fi
EOF

chmod +x "$PRE_COMMIT_HOOK"

echo "✅ Pre-commit hook installed"
echo "   Location: $PRE_COMMIT_HOOK"
echo "   Scanner: $SCAN_SCRIPT"

