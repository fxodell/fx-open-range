#!/usr/bin/env python3
"""
Cross-platform script to setup Cursor project structure.

Creates:
- .cursor/rules/guardrails.md
- docs/ folder with template files
- .gitignore with standard entries

Works on Mac, Linux, and Windows.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Set


# Template content for guardrails.md
GUARDRAILS_TEMPLATE = """Always read docs/CONTEXT.md and docs/TASKS.md before editing.
Keep changes minimal and scoped.
Prefer small diffs and incremental commits.
After modifying logic, add tests or provide exact manual test steps.
Do not change architecture without adding an ADR to docs/DECISIONS.md.
Never edit generated, build, or vendor files.
If behavior changes, update docs/CONTEXT.md.
Do not create throwaway files in the repo root.
Put experiments in /scratch (gitignored) or /sandbox.
Before finishing a task, remove trial files or move them to /scratch.

---
alwaysApply: true
---
"""

# Template content for CONTEXT.md
CONTEXT_TEMPLATE = """> This file is the single source of truth for humans and AI agents.
> All agents must read this before making changes.

# Project Context

## What we're building
- **Product**: [Describe your product/service]
- **Users**: [Describe your users]
- **Primary goal**: [Main objective]

## Current status
- **Working**: 
  - [List what's working]

- **Broken**: 
  - [List known issues]

- **In progress**: 
  - [List work in progress]

## Architecture snapshot
- **Frontend**: [Frontend technology or None]
- **Backend**: [Backend technology]
- **Data store**: [Database or storage]
- **Auth**: [Authentication method]
- **Integrations**: 
  - [List integrations]
- **Deployment**: [How it's deployed]

## How to run
- **Dev**: 
  ```bash
  # Add development commands
  ```

- **Tests**: 
  ```bash
  # Add test commands
  ```

- **Build**: 
  ```bash
  # Add build commands
  ```

- **Deploy**: 
  - [Deployment instructions]

## Constraints
- **Must**: 
  - [List requirements]

- **Must not**: 
  - [List restrictions]

- **Performance/SLA**: 
  - [Performance requirements]

## Known risks / sharp edges
- [List known issues or risks]

## Changelog (newest first)
- [Date]: [Change description]
"""

# Template content for TASKS.md
TASKS_TEMPLATE = """# Project Tasks

This document tracks current tasks, improvements, and future work.

## Current Tasks

### High Priority
- [ ] [Add high priority tasks]

### Medium Priority
- [ ] [Add medium priority tasks]

### Low Priority
- [ ] [Add low priority tasks]

## Future Enhancements
- [ ] [Add future enhancement ideas]

## Completed Tasks
- [x] [Move completed tasks here]

## Notes
- Tasks should be moved to "Completed" when finished
- Add new tasks as they arise
- Prioritize based on project goals and user needs
- Break down large tasks into smaller, actionable items
"""

# Template content for DECISIONS.md
DECISIONS_TEMPLATE = """# Architectural Decisions (ADR)

This document records architectural decisions made for this project.

## ADR-001 - [Decision Title]
- **Date**: [Date]
- **Decision**: [What was decided]
- **Why**: 
  - [Reason 1]
  - [Reason 2]
- **Alternatives considered**: 
  - [Alternative 1]
  - [Alternative 2]
- **Consequences**: 
  - [Consequence 1]
  - [Consequence 2]

## ADR-002 - [Next Decision]
- **Date**: [Date]
- **Decision**: [What was decided]
- **Why**: 
  - [Reasons]
- **Alternatives considered**: 
  - [Alternatives]
- **Consequences**: 
  - [Consequences]
"""

# Standard .gitignore sections
GITIGNORE_SECTIONS = {
    'python': """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
""",
    'ides': """# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
""",
    'os': """# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
""",
    'logs': """# Logs
logs/
*.log
""",
    'env': """# Environment variables
.env
.env.local
""",
    'experiments': """# Experiments / throwaway
scratch/
tmp/
playground/
notes/
sandbox/
*.scratch.*
*.tmp.*
""",
    'ai': """# Claude/Assistant files
.claude/

# Cursor
.cursor/
""",
    'testing': """# pytest
.pytest_cache/
.coverage
htmlcov/

# mypy
.mypy_cache/
.dmypy.json
dmypy.json
""",
    'jupyter': """# Jupyter Notebook
.ipynb_checkpoints
"""
}


class SetupScript:
    def __init__(self, project_dir: Path, force: bool = False, minimal: bool = False):
        self.project_dir = project_dir.resolve()
        self.force = force
        self.minimal = minimal
        self.created = []
        self.updated = []
        self.skipped = []
        self.errors = []

    def run(self):
        """Main execution method."""
        print(f"Setting up Cursor project structure in: {self.project_dir}")
        print()

        # Validate project directory
        if not self.project_dir.exists():
            print(f"Error: Project directory does not exist: {self.project_dir}")
            return False

        if not self.project_dir.is_dir():
            print(f"Error: Path is not a directory: {self.project_dir}")
            return False

        # Check write permissions
        if not self._check_write_permissions():
            print(f"Error: No write permissions in: {self.project_dir}")
            return False

        # Create structure
        self._create_cursor_rules()
        self._create_docs_folder()
        if not self.minimal:
            self._create_doc_templates()
        self._update_gitignore()

        # Print summary
        self._print_summary()

        return len(self.errors) == 0

    def _check_write_permissions(self) -> bool:
        """Check if we can write to the project directory."""
        try:
            test_file = self.project_dir / '.cursor_setup_test'
            test_file.touch()
            test_file.unlink()
            return True
        except (PermissionError, OSError):
            return False

    def _create_cursor_rules(self):
        """Create .cursor/rules directory and guardrails.md."""
        rules_dir = self.project_dir / '.cursor' / 'rules'
        guardrails_file = rules_dir / 'guardrails.md'

        try:
            # Create directory
            rules_dir.mkdir(parents=True, exist_ok=True)
            if not (rules_dir / 'guardrails.md').exists():
                self.created.append(str(rules_dir))

            # Create guardrails.md
            if guardrails_file.exists() and not self.force:
                self.skipped.append(str(guardrails_file))
            else:
                guardrails_file.write_text(GUARDRAILS_TEMPLATE, encoding='utf-8')
                if guardrails_file.exists():
                    self.created.append(str(guardrails_file))
        except Exception as e:
            self.errors.append(f"Error creating cursor rules: {e}")

    def _create_docs_folder(self):
        """Create docs directory."""
        docs_dir = self.project_dir / 'docs'

        try:
            if not docs_dir.exists():
                docs_dir.mkdir(parents=True, exist_ok=True)
                self.created.append(str(docs_dir))
        except Exception as e:
            self.errors.append(f"Error creating docs folder: {e}")

    def _create_doc_templates(self):
        """Create template files in docs/."""
        templates = {
            'CONTEXT.md': CONTEXT_TEMPLATE,
            'TASKS.md': TASKS_TEMPLATE,
            'DECISIONS.md': DECISIONS_TEMPLATE,
        }

        for filename, content in templates.items():
            filepath = self.project_dir / 'docs' / filename
            try:
                if filepath.exists() and not self.force:
                    self.skipped.append(str(filepath))
                else:
                    filepath.write_text(content, encoding='utf-8')
                    self.created.append(str(filepath))
            except Exception as e:
                self.errors.append(f"Error creating {filename}: {e}")

    def _update_gitignore(self):
        """Create or update .gitignore file."""
        gitignore_file = self.project_dir / '.gitignore'

        try:
            # Read existing content
            existing_lines: Set[str] = set()
            if gitignore_file.exists():
                existing_content = gitignore_file.read_text(encoding='utf-8')
                existing_lines = set(line.strip() for line in existing_content.splitlines())
            else:
                existing_content = ""

            # Determine what to add
            new_sections = []
            for section_name, section_content in GITIGNORE_SECTIONS.items():
                # Check if section already exists
                section_lines = set(line.strip() for line in section_content.splitlines() if line.strip())
                if not section_lines.issubset(existing_lines):
                    new_sections.append(section_content)

            # Write updated content
            if new_sections or not gitignore_file.exists():
                # Add new sections
                if existing_content and not existing_content.endswith('\n'):
                    existing_content += '\n'
                if new_sections:
                    existing_content += '\n'.join(new_sections)
                    if not existing_content.endswith('\n'):
                        existing_content += '\n'

                gitignore_file.write_text(existing_content, encoding='utf-8')
                if gitignore_file.exists():
                    self.updated.append(str(gitignore_file))
            else:
                self.skipped.append(str(gitignore_file))
        except Exception as e:
            self.errors.append(f"Error updating .gitignore: {e}")

    def _print_summary(self):
        """Print summary of actions taken."""
        print("=" * 60)
        print("Setup Summary")
        print("=" * 60)

        if self.created:
            print(f"\n✓ Created ({len(self.created)}):")
            for item in self.created:
                print(f"  - {item}")

        if self.updated:
            print(f"\n✓ Updated ({len(self.updated)}):")
            for item in self.updated:
                print(f"  - {item}")

        if self.skipped:
            print(f"\n⊘ Skipped ({len(self.skipped)}):")
            for item in self.skipped:
                print(f"  - {item}")
            if not self.force:
                print("  (Use --force to overwrite existing files)")

        if self.errors:
            print(f"\n✗ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")

        print()
        if not self.errors:
            print("✅ Setup completed successfully!")
        else:
            print("⚠️  Setup completed with errors.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Setup Cursor project structure (cursor rules, docs, .gitignore)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup in current directory
  python setup-cursor-project.py

  # Setup in specific directory
  python setup-cursor-project.py --project-dir /path/to/project

  # Force overwrite existing files
  python setup-cursor-project.py --force

  # Minimal setup (just folders and guardrails, no doc templates)
  python setup-cursor-project.py --minimal
        """
    )

    parser.add_argument(
        '--project-dir',
        type=str,
        default='.',
        help='Project directory path (default: current directory)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing files (default: skip if exists)'
    )
    parser.add_argument(
        '--minimal',
        action='store_true',
        help='Minimal setup: only create folders and guardrails.md, skip doc templates'
    )

    args = parser.parse_args()

    # Convert to Path object
    project_dir = Path(args.project_dir).resolve()

    # Validate Python version
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required")
        print(f"Current version: {sys.version}")
        return 1

    # Run setup
    setup = SetupScript(project_dir, force=args.force, minimal=args.minimal)
    success = setup.run()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
