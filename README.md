# opencode-linear-skill

An [OpenCode](https://opencode.ai) skill that integrates Linear issue tracking into your AI coding workflow.

Say **"add to Linear"** during any task, and the AI will create a well-structured Linear issue with context, requirements, and acceptance criteria. When work is done, it updates the issue with what was changed and how it was tested.

## Installation

### 1. Get a Linear token

**If your workspace supports personal API keys:**
Generate one at `https://linear.app/settings/account/api`.

**If your workspace uses OAuth only:**
```bash
python3 setup-oauth.py <CLIENT_ID> <CLIENT_SECRET>
```
This opens your browser, completes the OAuth flow, and prints the token.

### 2. Configure credentials

Create `~/.config/opencode/.linear-skill.env`:

```bash
LINEAR_API_KEY=your_token_here
LINEAR_DEFAULT_ASSIGNEE_ID=your_user_id_here
```

To find your user ID:
```bash
curl https://api.linear.app/graphql \
  -H "Authorization: YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ users { nodes { id name } } }"}'
```

### 3. Install the skill

Symlink the repo to your global skills directory:

```bash
ln -s /path/to/opencode-linear-skill ~/.config/opencode/skills/linear
```

Or copy the files:
```bash
mkdir -p ~/.config/opencode/skills/linear
cp SKILL.md linear_api.py ~/.config/opencode/skills/linear/
```

### 4. Restart OpenCode

The skill will be available in all projects.

## Usage

During any conversation:

- **"Add to Linear"** — creates an issue from the current task context
- **"Track in Linear"** — same as above
- **"Update the Linear issue"** — adds completion notes after work is done
- **"Show open issues for [project]"** — lists all open issues for a project

The skill auto-populates title, description, priority, and acceptance criteria from conversation context.

## How it works

No MCP server needed. The skill uses `linear_api.py` — a self-contained Python script that calls the Linear GraphQL API directly. Credentials are stored in `~/.config/opencode/.linear-skill.env`.

## Configuration

Edit `~/.config/opencode/.linear-skill.env` to change:
- `LINEAR_API_KEY` — your Linear API token
- `LINEAR_DEFAULT_ASSIGNEE_ID` — default assignee for new issues

## License

MIT
