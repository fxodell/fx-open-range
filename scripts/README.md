# Scripts

This directory contains utility scripts for project setup and maintenance.

## setup-cursor-project.py

Cross-platform Python script to initialize or update Cursor project structure. Works on Mac, Linux, and Windows.

### What It Does

The script creates/updates:

1. **`.cursor/rules/guardrails.md`** - Cursor AI rules file with project-specific guidelines
2. **`docs/` folder** - Documentation directory with template files:
   - `CONTEXT.md` - Project context template
   - `TASKS.md` - Task tracking template
   - `DECISIONS.md` - Architecture decision records template
3. **`.gitignore`** - Standard entries for Python, IDEs, OS files, logs, etc. (merges with existing)

### Requirements

- Python 3.6 or higher
- No external dependencies (uses standard library only)

### Usage

#### Basic Usage

Setup in current directory:
```bash
python scripts/setup-cursor-project.py
```

Setup in specific directory:
```bash
python scripts/setup-cursor-project.py --project-dir /path/to/project
```

#### Options

- `--project-dir PATH` - Specify project directory (default: current directory)
- `--force` - Overwrite existing files (default: skip if exists)
- `--minimal` - Only create folders and `guardrails.md`, skip doc templates

#### Examples

**New Project Setup:**
```bash
# Create new project directory
mkdir my-new-project
cd my-new-project

# Initialize with full setup
python ../scripts/setup-cursor-project.py
```

**Existing Project:**
```bash
# Add Cursor structure to existing project
cd existing-project
python ../scripts/setup-cursor-project.py
```

**Minimal Setup (just rules, no doc templates):**
```bash
python scripts/setup-cursor-project.py --minimal
```

**Force Overwrite Existing Files:**
```bash
python scripts/setup-cursor-project.py --force
```

**Setup Another Project:**
```bash
python scripts/setup-cursor-project.py --project-dir /path/to/other/project
```

### Behavior

- **Idempotent**: Safe to run multiple times on the same project
- **Non-destructive**: Won't overwrite existing files unless `--force` is used
- **Merge-friendly**: `.gitignore` entries are merged intelligently (won't duplicate)
- **Cross-platform**: Uses `pathlib` for proper path handling on all platforms

### What Gets Created

#### `.cursor/rules/guardrails.md`
Contains basic rules for AI agents working on the project, including:
- Read context first
- Keep changes minimal
- Prefer incremental commits
- Put experiments in scratch/sandbox
- Always-apply flag for Cursor

#### `docs/` Templates
Template files with placeholders for:
- Project context and current status
- Task tracking (high/medium/low priority)
- Architecture decision records (ADR format)

#### `.gitignore` Sections
Standard entries for:
- Python artifacts (`__pycache__/`, `*.pyc`, etc.)
- IDEs (`.vscode/`, `.idea/`, etc.)
- OS files (`.DS_Store`, `Thumbs.db`, etc.)
- Logs (`logs/`, `*.log`)
- Environment files (`.env`, `.env.local`)
- Experiment folders (`scratch/`, `sandbox/`, `tmp/`)
- AI tool files (`.cursor/`, `.claude/`)
- Testing artifacts (`pytest_cache/`, `.coverage`, etc.)
- Jupyter notebooks (`.ipynb_checkpoints`)

### Platform Support

- ✅ **macOS** - Tested and working
- ✅ **Linux** - Tested and working
- ✅ **Windows** - Works with Python 3.6+ (tested with Git Bash, WSL, and native Python)

### Troubleshooting

**Permission Errors:**
- Ensure you have write permissions in the project directory
- On Unix systems, you may need to use `sudo` (though not recommended)

**Python Version:**
- Requires Python 3.6+
- Check version: `python --version` or `python3 --version`
- Use `python3` instead of `python` if needed

**Path Issues on Windows:**
- Use forward slashes or double backslashes: `--project-dir C:/path/to/project`
- Or use relative paths: `--project-dir ..\\other-project`

### Making Script Executable (Unix/macOS)

To make the script directly executable:
```bash
chmod +x scripts/setup-cursor-project.py
```

Then run it directly:
```bash
./scripts/setup-cursor-project.py
```

Or add to PATH and run from anywhere:
```bash
export PATH="$PATH:/path/to/project/scripts"
setup-cursor-project.py
```

### Integration with Other Projects

This script can be used to quickly initialize new projects with Cursor best practices:

1. Copy `setup-cursor-project.py` to your project or keep it in a shared scripts directory
2. Run it in any project directory to add Cursor structure
3. Customize the generated templates for your specific project needs

### See Also

- [Cursor Best Practices](../../docs/CURSOR_BEST_PRACTICES.md) (when created)
- [AI Quick Start](../../docs/AI_QUICK_START.md)
- [Agent Contract](../../docs/AGENT_CONTRACT.md)
