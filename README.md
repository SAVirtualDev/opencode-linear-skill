# opencode-linear-skill

An [OpenCode](https://opencode.ai) skill that integrates Linear issue tracking into your AI coding workflow.

Say **"add to Linear"** during any task, and the AI will create a well-structured Linear issue with context, requirements, and acceptance criteria. When work is done, it updates the issue with what was changed and how it was tested.

## Installation

### 1. Set up the Linear MCP server

Add to your `~/.config/opencode/opencode.json`:

```json
{
  "mcp": {
    "linear": {
      "type": "local",
      "command": ["npx", "-y", "linear-mcp"],
      "env": {
        "LINEAR_API_KEY": "your_linear_token_here"
      }
    }
  }
}
```

### 2. Get a Linear token

If your workspace uses OAuth (no personal API keys):

```bash
python3 setup-oauth.py <CLIENT_ID> <CLIENT_SECRET>
```

This opens your browser, completes the OAuth flow, and saves the token to `~/.config/opencode/.env.linear`.

If your workspace supports personal API keys, generate one at `https://linear.app/settings/account/api` and use it directly.

### 3. Install the skill

Copy or symlink `SKILL.md` to your global skills directory:

```bash
mkdir -p ~/.config/opencode/skills/linear
cp SKILL.md ~/.config/opencode/skills/linear/SKILL.md
```

Or symlink from your clone:

```bash
ln -s "$(pwd)/SKILL.md" ~/.config/opencode/skills/linear/SKILL.md
```

### 4. Restart OpenCode

The skill and MCP server will be available in all projects.

## Usage

During any conversation:

- **"Add to Linear"** — creates an issue from the current task context
- **"Track in Linear"** — same as above
- **"Update the Linear issue"** — adds completion notes after work is done

The skill auto-populates title, description, priority, and acceptance criteria from conversation context.

## Configuration

Edit `SKILL.md` to change:
- Default team (currently `SA`)
- Priority defaults
- Description template

## License

MIT
