# Quick Start: Using AI Assistants in VS Code/Cursor Terminal

## 🚀 No API Keys Required - Use Built-in Features

### Method 1: Using Cursor's Built-in AI (Recommended)

Since you're using **Cursor**, you already have AI assistance built-in! Here's how to use it:

#### In the Editor:
- **Chat**: `Cmd+L` (Mac) or `Ctrl+L` (Windows/Linux) to open AI chat
- **Composer**: `Cmd+I` (Mac) or `Ctrl+I` to open Composer for multi-file edits
- **Inline Edit**: Select code and press `Cmd+K` (Mac) or `Ctrl+K` to edit inline

#### In the Terminal:
1. **Open Terminal**: Press `` Cmd+` `` (backtick) in Cursor
2. **Use Cursor Chat**: While in terminal, you can still use `Cmd+L` to ask questions about terminal output
3. **Copy Terminal Output**: Select terminal text and use `Cmd+K` to ask Cursor about it

#### Terminal Workflow:
```bash
# Run your code
python -m app.main --status

# Select the output in terminal, then:
# - Press Cmd+K to ask Cursor about the output
# - Or press Cmd+L to open chat and paste the output
```

### Method 2: VS Code Extensions (No API Keys)

#### GitHub Copilot (if you have subscription):
- Install "GitHub Copilot" extension
- Works directly in terminal via `copilot` command (if enabled)
- No separate API keys needed if you have Copilot subscription

#### Other Free Options:
- **Codeium**: Free AI coding assistant extension
- **Tabnine**: Free tier available
- **Continue**: Open-source AI coding assistant


## 📝 Common Use Cases with Cursor

### Explain Code
1. Open a file (e.g., `src/strategies.py`)
2. Press `Cmd+L` to open chat
3. Ask: "explain how this strategy works"

### Generate Code
1. Open the file where you want to add code
2. Press `Cmd+I` to open Composer
3. Ask: "write a function to detect market regimes using SMA"
4. Cursor will show you the changes before applying

### Code Review
1. Run `git diff` in terminal
2. Select the output
3. Press `Cmd+K` or `Cmd+L` to ask Cursor to review

### Debug Help
1. Run your code and see an error
2. Select the error message in terminal
3. Press `Cmd+K` to ask Cursor about the error
4. Or press `Cmd+L` and paste the error

### Review Trading Logs
1. Check log files in `logs/` directory
2. Open a log file (e.g., `logs/trading_20250101.log`)
3. Select error or relevant section
4. Press `Cmd+K` or `Cmd+L` to ask Cursor to analyze the log entry

### Terminal-Specific Workflow
```bash
# 1. Run command
python -m app.main --status

# 2. Select output in terminal
# 3. Press Cmd+K to ask about it
# 4. Or copy output and use Cmd+L to chat

# Debugging trading application:
python -m app.main --once
# Select output, then use Cmd+K to ask Cursor about the signal/trade
```

## ⌨️ Cursor Keyboard Shortcuts

- **`Cmd+L`**: Open AI chat
- **`Cmd+I`**: Open Composer (multi-file edits)
- **`Cmd+K`**: Inline edit selected code
- **`Cmd+Shift+L`**: Chat with selected code
- **`` Cmd+` ``**: Open/close terminal

## 💡 Pro Tips

1. **Terminal + Chat**: Keep terminal open and use `Cmd+L` to ask questions about output
2. **Multi-file Context**: Use Composer (`Cmd+I`) when you need to edit multiple files
3. **Code Selection**: Select code in terminal or editor, then use `Cmd+K` for quick edits
4. **Error Debugging**: Always select the full error message for better context

## 📚 Full Documentation

See [AI_TERMINAL_USAGE.md](./AI_TERMINAL_USAGE.md) for more details and examples.

