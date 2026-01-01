#!/bin/bash
# Export Cursor workflow to another project

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TARGET_PROJECT="$1"

if [ -z "$TARGET_PROJECT" ]; then
    echo "Usage: ./export-workflow.sh /path/to/new-project"
    exit 1
fi

if [ ! -d "$TARGET_PROJECT" ]; then
    echo "Error: Target directory does not exist: $TARGET_PROJECT"
    exit 1
fi

# Convert to absolute path
TARGET_PROJECT="$(cd "$TARGET_PROJECT" && pwd)"

echo "Exporting workflow from $SCRIPT_DIR to $TARGET_PROJECT..."

# Copy Cursor configuration
echo "Copying .cursor configuration..."
mkdir -p "$TARGET_PROJECT/.cursor/rules"
if [ -f "$SCRIPT_DIR/.cursor/rules/guardrails.md" ]; then
    cp "$SCRIPT_DIR/.cursor/rules/guardrails.md" "$TARGET_PROJECT/.cursor/rules/guardrails.md"
    echo "  ✓ Cursor rules copied"
else
    echo "  ⚠ No .cursor/rules/guardrails.md found in source ($SCRIPT_DIR)"
fi

# Copy documentation
echo "Copying documentation..."
if [ -d "$SCRIPT_DIR/docs" ]; then
    cp -r "$SCRIPT_DIR/docs/" "$TARGET_PROJECT/"
    echo "  ✓ Documentation copied"
else
    echo "  ⚠ No docs/ directory found in source ($SCRIPT_DIR)"
fi

# Create project structure
echo "Creating project structure..."
mkdir -p "$TARGET_PROJECT/scratch"
mkdir -p "$TARGET_PROJECT/sandbox"
mkdir -p "$TARGET_PROJECT/scripts"
mkdir -p "$TARGET_PROJECT/tests"
echo "  ✓ Project folders created"

# Update .gitignore if it exists
if [ -f "$TARGET_PROJECT/.gitignore" ]; then
    if ! grep -q "scratch/" "$TARGET_PROJECT/.gitignore"; then
        echo "" >> "$TARGET_PROJECT/.gitignore"
        echo "# Workflow folders" >> "$TARGET_PROJECT/.gitignore"
        echo "scratch/" >> "$TARGET_PROJECT/.gitignore"
        echo "sandbox/" >> "$TARGET_PROJECT/.gitignore"
        echo "logs/" >> "$TARGET_PROJECT/.gitignore"
        echo "  ✓ Updated .gitignore"
    fi
else
    cat > "$TARGET_PROJECT/.gitignore" << 'GITIGNORE'
# Workflow folders
scratch/
sandbox/
logs/

# Python
*.pyc
__pycache__/
*.py[cod]
*$py.class
.Python
GITIGNORE
    echo "  ✓ Created .gitignore"
fi

echo ""
echo "✅ Workflow exported successfully!"
echo ""
echo "Next steps:"
echo "1. Update docs/CONTEXT.md with your project details"
echo "2. Review docs/DECISIONS.md and remove project-specific ADRs"
echo "3. Clear docs/TASKS.md and add your project tasks"
echo "4. Review .cursor/rules/guardrails.md if needed"
