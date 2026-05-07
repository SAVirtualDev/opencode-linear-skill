---
name: linear
description: "Create and manage Linear issues. Use when the user says 'add to Linear', 'track in Linear', 'create Linear issue', or explicitly asks to log work in Linear. Team: SA."
---

# Linear Issue Management

## Trigger

Activate when the user explicitly says any of:
- "add to Linear"
- "track in Linear"
- "create a Linear issue"
- "log this in Linear"

Do NOT auto-create issues. Only create when explicitly requested.

## Default Context

- **Team**: SA
- **Default assignee**: read from `~/.config/opencode/.linear-skill.env` (see `LINEAR_DEFAULT_ASSIGNEE_ID`)
- Use the `linear_mcp` tools provided by the `linear` MCP server

## Workflow: Creating an Issue

When the user asks to add something to Linear:

1. **Gather info from context** — use the current task/conversation to populate:
   - `title`: concise summary (imperative mood, e.g. "Add dark mode toggle to settings")
   - `description`: markdown body with:
     - **Context**: why this is needed (1-2 sentences)
     - **Requirements**: bullet list of what needs to happen
     - **Acceptance Criteria**: how to verify it's done
   - `priority`: infer from urgency (1=urgent, 2=high, 3=medium, 4=low). Default to 4 (low) if unclear.
   - `teamId`: look up the SA team ID using available tools
   - `assigneeId`: read from `~/.config/opencode/.linear-skill.env` (`LINEAR_DEFAULT_ASSIGNEE_ID`). If unset, leave unassigned.

2. **Create the issue** using the Linear MCP tools (e.g. `create_issue` or `linear_create_issue`)

3. **Report back** — show the user the issue identifier (e.g. `SA-123`) and a link

## Workflow: Updating After Completion

When you complete a task that has an associated Linear issue:

1. **Add a comment** to the issue with:
   - What was done (summary of changes)
   - Files modified
   - How it was tested / verified
2. **Update status** if appropriate (move to "Done" or "In Review")

## Workflow: Searching Issues

If the user asks about existing Linear issues:
- Use search/filter tools to find issues
- Present results concisely (ID, title, status, assignee)

## Workflow: List Open Issues by Project

When the user asks to see open issues for a project (e.g. "show me open issues for ArchAngel"):

1. **Find the project** — list projects and match by name
2. **Query open issues** for that project using the Linear API (filter by project ID and non-completed workflow states)
3. **Present results** as a table:
   | ID | Title | Priority | Status | Assignee |
4. Include total count of open issues

## Tool Reference

The `linear` MCP server exposes these tools (names may vary by server version):
- `create_issue` — create a new issue
- `update_issue` — update fields on an existing issue
- `search_issues` — search/filter issues
- `get_issue` — get issue details by ID
- `add_comment` — add a comment to an issue
- `get_teams` — list teams (use to resolve team ID for "SA")

## Notes

- Always confirm the issue was created successfully before reporting to the user
- If the MCP server is unavailable, inform the user and suggest restarting OpenCode
- Never store Linear tokens in code or commit them — they live in the global OpenCode config
