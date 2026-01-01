# Using AI Assistants in VS Code/Cursor Terminal

This guide shows how to use AI coding assistants from the terminal **without requiring any API keys**.

## Using Cursor's Built-in AI (Recommended)

**Cursor** has AI built-in - no API keys needed!

### Quick Access:
- **Chat**: `Cmd+L` (Mac) or `Ctrl+L` (Windows/Linux)
- **Composer**: `Cmd+I` for multi-file edits
- **Inline Edit**: Select code + `Cmd+K`

### Terminal Workflow:
1. Open terminal in Cursor: `` Cmd+` ``
2. Run commands as normal
3. Select terminal output and press `Cmd+K` to ask about it
4. Or use `Cmd+L` to open chat and paste terminal output

### Example:
```bash
# Run your code
python -m app.main --status

# Select the output, then:
# - Press Cmd+K to ask Cursor about it inline
# - Or press Cmd+L to open chat and discuss
```

## VS Code Extensions (No API Keys)

### GitHub Copilot
- Requires subscription, but no separate API keys
- Install "GitHub Copilot" extension
- May provide `copilot` CLI command if enabled

### Free Alternatives:
- **Codeium**: Free AI coding assistant
- **Tabnine**: Free tier available
- **Continue**: Open-source, self-hosted option

## VS Code Terminal Integration

### Opening Terminal in VS Code/Cursor

1. **Keyboard Shortcut**: `` Ctrl+` `` (backtick) or `` Cmd+` `` on Mac
2. **Menu**: View → Terminal
3. **Command Palette**: `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) → "Terminal: Create New Terminal"

### Using AI Assistants in Integrated Terminal

1. **Open Terminal** (use any method above)
2. **Run your commands** as normal
3. **Select output** and use Cursor's AI features:
   - Press `Cmd+K` for inline help
   - Press `Cmd+L` to open chat
   - Copy output and paste into chat

## Example Workflows

### Code Explanation
1. Open a file in Cursor
2. Press `Cmd+L` to open chat
3. Ask: "explain how this code works"

### Code Review
1. Run `git diff` in terminal
2. Select the output
3. Press `Cmd+K` or `Cmd+L` to ask Cursor to review

### Debug Help
1. Run your code and see an error
2. Select the error message in terminal
3. Press `Cmd+K` to ask Cursor about the error
4. Or press `Cmd+L` and paste the error

### Generate Code
1. Open the file where you want to add code
2. Press `Cmd+I` to open Composer
3. Ask: "write a function to calculate SMA"
4. Cursor will show you the changes before applying

## Keyboard Shortcuts

- **`Cmd+L`**: Open AI chat
- **`Cmd+I`**: Open Composer (multi-file edits)
- **`Cmd+K`**: Inline edit selected code
- **`Cmd+Shift+L`**: Chat with selected code
- **`` Cmd+` ``**: Open/close terminal

## Tips

1. **Terminal + Chat**: Keep terminal open and use `Cmd+L` to ask questions about output
2. **Multi-file Context**: Use Composer (`Cmd+I`) when you need to edit multiple files
3. **Code Selection**: Select code in terminal or editor, then use `Cmd+K` for quick edits
4. **Error Debugging**: Always select the full error message for better context
5. **Combine Features**: Use terminal alongside editor for best experience

## Troubleshooting

- **Command not found**: Make sure you're using Cursor (not plain VS Code) for built-in AI
- **Shortcuts not working**: Check Cursor settings for keyboard shortcuts
- **Terminal not opening**: Try `View → Terminal` from the menu
- **AI not responding**: Check your Cursor subscription/plan status
