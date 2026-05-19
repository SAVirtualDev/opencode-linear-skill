# opencode-linear-skill

An [OpenCode](https://opencode.ai) skill that integrates Linear issue tracking into your AI coding workflow via the Linear MCP server.

Say **"add to Linear"** during any task and the AI will create a well-structured Linear issue with context, requirements, and acceptance criteria. When work is done, it updates the issue with what was changed and how it was tested.

## Installation

### 1. Configure credentials

Create `~/.config/opencode/.linear-skill.env`:

```env
LINEAR_DEFAULT_ASSIGNEE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

To find your user ID, use the `linear_get_user` MCP tool after setup, or call `linear_list_users`.

### 2. Install the skill

Clone the skill into your global skills directory:

```bash
git clone https://github.com/SAVirtualDev/opencode-linear-skill.git ~/.config/opencode/skills/linear
```

### 3. Add the Linear MCP to opencode.json

Add the following to `~/.config/opencode/opencode.json` under `"mcp"`:

```json
"linear": {
  "type": "local",
  "command": ["npx", "-y", "mcp-remote", "https://mcp.linear.app/sse"],
  "enabled": true,
  "timeout": 30000
}
```

### 4. Restart OpenCode

On first use, `mcp-remote` will open a browser window to complete the OAuth flow. The token is cached locally — no further auth needed.

## Usage

During any conversation:

- **"Add to Linear"** — creates a structured issue from the current task context
- **"Track in Linear"** — same as above
- **"Update the Linear issue"** — adds completion notes and moves to "In Review"
- **"Show open issues for [project]"** — lists all open issues for a project

The skill auto-populates title, description, priority, and acceptance criteria from conversation context.

## How it works

The skill uses the **Linear MCP server** (`https://mcp.linear.app/sse`) via `mcp-remote`, which proxies SSE to the local stdio transport that OpenCode expects. All operations go through `linear_*` MCP tools — no direct API calls.

Authentication is handled via OAuth. On first use, `mcp-remote` opens your browser to authorise the connection. The token is cached in `~/.mcp-auth/` for subsequent sessions.

## Troubleshooting

### OAuth tokens expired / "Cannot login to Linear"

Linear OAuth tokens expire. The access token lasts ~24 hours. The refresh token also has a finite lifetime — once it expires, `mcp-remote` cannot silently refresh and must do a full interactive re-auth. However, **OpenCode redirects MCP server stderr to `/dev/null`**, so the authorization URL that `mcp-remote` prints is invisible to you. The MCP tools will appear to hang or time out.

**To fix:**

1. **Kill the stale mcp-remote process:**
   ```bash
   pkill -f "mcp-remote https://mcp.linear.app"
   ```

2. **Clear cached auth state:**
   ```bash
   rm -rf ~/.mcp-auth
   ```

3. **Run mcp-remote manually in your terminal** to complete the OAuth flow interactively:
   ```bash
   npx -y mcp-remote https://mcp.linear.app/mcp --debug
   ```
   This will print an authorization URL. Open it in your browser, authorize the app, and the tokens will be saved to `~/.mcp-auth/`.

4. **Stop the manual process** (Ctrl+C) once you see `Authorization completed successfully` and `Proxy established successfully`.

5. **Restart OpenCode** — it will spawn a fresh `mcp-remote` that picks up the saved tokens.

### Why this happens

- `mcp-remote` stores OAuth tokens in `~/.mcp-auth/mcp-remote-0.1.37/*_tokens.json`
- Access tokens expire after ~24 hours; refresh tokens may also expire
- When tokens are missing or expired, `mcp-remote` starts an OAuth callback server on port `22227` and prints an authorization URL to stderr
- OpenCode suppresses MCP server stderr, so the URL is never shown
- The callback server runs but nobody visits the URL → auth never completes → tools time out

### Debug mode

Add `--debug` to the mcp-remote command in `opencode.json` to get verbose logs written to `~/.mcp-auth/*_debug.log`:

```json
"linear": {
  "type": "local",
  "command": ["npx", "-y", "mcp-remote", "https://mcp.linear.app/mcp", "--debug"]
}
```

## License

MIT License

Copyright (c) 2025 SAVirtualDev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
