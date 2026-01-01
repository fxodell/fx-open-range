# Exporting Workflow to Other Projects

This guide explains how to copy your Cursor + AI workflow configuration to other projects.

## What Gets Exported

### Required Files
- **`.cursor/rules/guardrails.md`** - Cursor-specific agent rules
- **`docs/` folder** - Complete workflow documentation

### Optional Project Structure
- `scratch/` - For temporary experiments (gitignored)
- `sandbox/` - For safe testing (gitignored)

---

## Quick Export (Copy-Paste Method)

### Step 1: Copy Cursor Configuration

Copy the `.cursor` folder to your new project:

```bash
# From your current project
cp -r .cursor /path/to/new-project/

# Or create it manually:
mkdir -p new-project/.cursor/rules
cp .cursor/rules/guardrails.md new-project/.cursor/rules/guardrails.md
```

### Step 2: Copy Documentation

Copy the entire `docs/` folder:

```bash
# Copy entire docs folder
cp -r docs/ /path/to/new-project/

# Or selectively copy essential files:
mkdir -p new-project/docs
cp docs/AGENT_CONTRACT.md new-project/docs/
cp docs/CLEAN_PROJECT_WORKFLOW.md new-project/docs/
cp docs/CONTEXT.md new-project/docs/
cp docs/DECISIONS.md new-project/docs/
cp docs/TASKS.md new-project/docs/
cp docs/CLEANUP.md new-project/docs/
cp docs/AI_QUICK_START.md new-project/docs/
cp docs/AI_TERMINAL_USAGE.md new-project/docs/
```

### Step 3: Update Project-Specific Content

After copying, update these files with your new project's details:

1. **`docs/CONTEXT.md`**
   - Update "What we're building" section
   - Update architecture snapshot
   - Update how to run instructions
   - Update constraints

2. **`docs/DECISIONS.md`**
   - Remove project-specific ADRs (ADR-001 through ADR-007)
   - Keep the template structure for new decisions

3. **`docs/TASKS.md`**
   - Clear out current/completed tasks
   - Keep the structure for new tasks

4. **`.cursor/rules/guardrails.md`**
   - Usually works as-is, but may need minor adjustments

### Step 4: Create Project Structure (Optional)

If you want the same folder structure:

```bash
cd new-project
mkdir -p scratch sandbox scripts tests
```

Add to `.gitignore`:
```
scratch/
sandbox/
logs/
*.pyc
__pycache__/
```

---

## Automated Export Script

A ready-to-use script is included in the project root: `export-workflow.sh`

**The script automatically detects its own location**, so it works whether you run it from the project root or from anywhere else.

### Usage:
```bash
# From the project root (recommended)
./export-workflow.sh /path/to/new-project

# Or from anywhere (script finds its own location)
/path/to/fx-open-range-project/export-workflow.sh /path/to/new-project
```

### What the Script Does:
1. ✓ Copies `.cursor/rules/guardrails.md` to the new project
2. ✓ Copies entire `docs/` folder to the new project
3. ✓ Creates `scratch/`, `sandbox/`, `scripts/`, `tests/` folders
4. ✓ Updates or creates `.gitignore` with workflow folders

### Note:
The script is located in the project root. You can view its contents or modify it if needed. The script uses absolute paths, so it works regardless of your current directory.

Make it executable:
```bash
chmod +x export-workflow.sh
```

Usage:
```bash
./export-workflow.sh /path/to/new-project
```

---

## Manual Setup (Step-by-Step)

If you prefer manual setup:

### 1. Create Cursor Rules Directory
```bash
mkdir -p new-project/.cursor/rules
```

### 2. Create guardrails.md
```bash
cat > new-project/.cursor/rules/guardrails.md << 'EOF'
Always read docs/CONTEXT.md and docs/TASKS.md before editing.
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
EOF
```

### 3. Create docs/ Directory Structure
```bash
mkdir -p new-project/docs
```

Then copy or recreate the essential documentation files:
- `AGENT_CONTRACT.md`
- `CLEAN_PROJECT_WORKFLOW.md`
- `CONTEXT.md` (customize for your project)
- `DECISIONS.md` (template, remove project-specific ADRs)
- `TASKS.md` (template, clear tasks)
- `CLEANUP.md`
- `AI_QUICK_START.md`
- `AI_TERMINAL_USAGE.md`

### 4. Create Project Folders
```bash
cd new-project
mkdir -p scratch sandbox scripts tests logs
```

### 5. Update .gitignore
Add to your `.gitignore`:
```
scratch/
sandbox/
logs/
```

---

## Essential Files Checklist

When exporting, make sure you have:

- [ ] `.cursor/rules/guardrails.md` - Cursor agent rules
- [ ] `docs/AGENT_CONTRACT.md` - Agent behavioral rules
- [ ] `docs/CLEAN_PROJECT_WORKFLOW.md` - Workflow guidelines
- [ ] `docs/CONTEXT.md` - Project context (customize!)
- [ ] `docs/DECISIONS.md` - ADR template (remove old decisions)
- [ ] `docs/TASKS.md` - Task tracking (clear old tasks)
- [ ] `docs/CLEANUP.md` - Cleanup checklist
- [ ] `docs/AI_QUICK_START.md` - AI usage guide
- [ ] `docs/AI_TERMINAL_USAGE.md` - Terminal AI guide

---

## Customization After Export

### Must Customize:
1. **`docs/CONTEXT.md`** - Replace with your project's context
2. **`docs/DECISIONS.md`** - Remove old ADRs, keep template
3. **`docs/TASKS.md`** - Clear old tasks, add new ones

### May Need Customization:
1. **`.cursor/rules/guardrails.md`** - Adjust rules if needed
2. **`docs/CLEAN_PROJECT_WORKFLOW.md`** - Update if your project structure differs
3. **`docs/AGENT_CONTRACT.md`** - Adjust if project has specific requirements

### Usually Work As-Is:
- `docs/CLEANUP.md` - Generic cleanup checklist
- `docs/AI_QUICK_START.md` - Generic AI usage
- `docs/AI_TERMINAL_USAGE.md` - Generic terminal AI guide

---

## Verifying Export

After exporting, verify:

```bash
cd new-project

# Check Cursor rules exist
ls -la .cursor/rules/guardrails.md

# Check docs exist
ls -la docs/

# Check project structure
ls -d scratch sandbox scripts tests 2>/dev/null

# Test that Cursor recognizes the rules
# (Cursor should automatically load .cursor/rules/guardrails.md)
```

---

## Troubleshooting

### Cursor not picking up rules
- Make sure `.cursor/rules/guardrails.md` exists
- Restart Cursor
- Check that the file has the `alwaysApply: true` flag

### Documentation not found
- Verify `docs/` folder exists in project root
- Check that files have proper `.md` extensions
- Ensure files are readable

### Git ignoring workflow folders
- Check `.gitignore` includes `scratch/`, `sandbox/`, `logs/`
- Run `git status` to verify they're ignored

---

## Tips

1. **Create a Template Project**: Set up one "template" project with everything configured, then copy from there
2. **Version Control**: Commit the workflow files to git so they're preserved
3. **Share with Team**: These workflow files are meant to be shared - commit them!
4. **Customize Gradually**: Start with the essentials, customize as you learn what works

---

## Next Steps After Export

1. ✅ Update `docs/CONTEXT.md` with your project details
2. ✅ Review and customize `.cursor/rules/guardrails.md` if needed
3. ✅ Clear old tasks from `docs/TASKS.md`
4. ✅ Remove project-specific ADRs from `docs/DECISIONS.md`
5. ✅ Test that Cursor recognizes the rules
6. ✅ Start using the workflow!

---

## Sharing Across Projects

If you want to keep workflows synchronized:

### Option 1: Git Subtree (Advanced)
Keep workflow files in a separate repo and use git subtree to include them.

### Option 2: Manual Sync
Use the export script periodically to sync updates.

### Option 3: Template Repository
Create a "project-template" repository and start new projects by cloning it.

---

Your workflow is now portable and can be used across all your projects! 🚀

