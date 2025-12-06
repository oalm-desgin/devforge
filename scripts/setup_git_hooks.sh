#!/bin/bash
# Setup git hooks for commit message validation

HOOKS_DIR=".git/hooks"
COMMIT_MSG_HOOK="$HOOKS_DIR/commit-msg"

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Create commit-msg hook
cat > "$COMMIT_MSG_HOOK" << 'EOF'
#!/bin/bash
# Validate commit message format

python scripts/validate_commit_msg.py "$1"
EOF

# Make hook executable
chmod +x "$COMMIT_MSG_HOOK"

echo "Git hooks installed successfully!"
echo "Commit messages will now be validated for Conventional Commits format."

