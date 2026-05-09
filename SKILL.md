---
name: linear
description: "Create and manage Linear issues. Use when the user says 'add to Linear', 'track in Linear', 'create Linear issue', or explicitly asks to log work in Linear. Team: SA. Also: when working on a task related to a known Linear issue, read it before work and update it during work."
---

# Linear Issue Management

Uses the Linear MCP server via `mcp-remote` proxy (configured in `opencode.json`). All operations go through `linear_*` MCP tools.

**Known bug:** OpenCode's MCP client double-dispatches `tools/call` for create operations (confirmed via mcp-remote debug log: two `[Local→Remote] tools/call` messages with different JSON-RPC IDs, 140ms apart, identical arguments). Every `linear_save_issue` without an `id` fires twice, creating duplicate issues. Updates (with `id`) are safe because the second call targets the same resource. The verify+cancel workflow below is the mandatory defense.

## Mandatory: Read Before Work, Update During Work

Whenever you know (from context) that a task relates to a Linear issue — whether the user mentioned the ID, named a project, or the work clearly maps to an existing issue — you MUST:

1. **Read the issue first** — before writing any code, fetch the issue to understand its description, requirements, and acceptance criteria.
2. **Set status to "In Progress"** — do this whenever you start working on an issue:
   - If you just created the issue and are starting work immediately, set it right after creation
   - If you're picking up an existing issue, set it before writing any code
3. **Comment on progress** after significant milestones or at end of session.
4. **Move to "In Review" when implementation is complete** — after finishing the work and the user has reviewed the summary, move the issue to "In Review" to signal it's ready for their final review. This is the expected terminal state for the AI's workflow.
5. **Only close to "Done" when explicitly asked** — the user may ask you to close a ticket. In that case, look up the "Done" state and update.

This applies even if the user didn't explicitly say "add to Linear" — if you can connect the work to an issue, do it.

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
- **Auth**: OAuth via `mcp-remote` — no API key required

## Workflow: Creating an Issue

When the user asks to add something to Linear:

### Step 0 — Duplicate Detection (MANDATORY)

Before creating, search for existing issues that may already cover this work:

1. Search by title keywords using `linear_list_issues` with the `query` parameter
2. Also search by project if known: `linear_list_issues` with `project` parameter
3. Check both open AND recently completed/canceled issues

If a matching issue exists:
- **Same scope, open**: inform the user and do NOT create. Link to the existing issue.
- **Same scope, completed**: inform the user it was already done. Do NOT create.
- **Similar but different scope**: confirm with the user before proceeding.

### Step 1 — Gather Info

- `title`: concise summary (imperative mood, e.g. "Add dark mode toggle to settings")
- `description`: markdown body with:
  - **Context**: why this is needed (1-2 sentences)
  - **Requirements**: bullet list of what needs to happen
  - **Acceptance Criteria**: how to verify it's done
- `priority`: infer from urgency (1=urgent, 2=high, 3=medium, 4=low). Default to 4 (low) if unclear.
- `team`: "SA"
- `project`: look up using `linear_list_projects` and match by name
- `assignee`: read from `~/.config/opencode/.linear-skill.env` (`LINEAR_DEFAULT_ASSIGNEE_ID`). If unset, leave unassigned.

### Step 2 — Create

Use `linear_save_issue` without an `id` parameter.

### Step 3 — Verify (MANDATORY)

After creating, immediately verify by searching for the exact title with `linear_list_issues`. If more than one issue exists with the same title, cancel the extras by setting state to "Canceled" via `linear_save_issue`. Keep the oldest (first created).

### Step 4 — Report

Show the user the surviving issue identifier (e.g. `SA-123`) and URL.

## Workflow: Updating After Completion

When you complete a task that has an associated Linear issue:

1. **Add a comment** to the issue with:
   - What was done (summary of changes)
   - Files modified
   - How it was tested / verified
2. **Move to "In Review"** — this signals the implementation is done and ready for the user to review. Do NOT move to "Done" or any final state; only the user can close an issue.

## Workflow: Marking an Issue as Duplicate

When an issue is identified as a duplicate of another:

1. **Find the "Duplicate" state** using `linear_list_issue_statuses` — it's a `canceled`-type state
2. **Update the issue** to the Duplicate state using `linear_save_issue`
3. **Optionally add a comment** linking to the parent issue

## Workflow: Searching / Listing Issues

If the user asks about existing Linear issues or wants to see open issues for a project:

1. **Find the project** using `linear_list_projects`, match by name
2. **List open issues** using `linear_list_issues` with the project parameter
3. **Present results** as a table with ID, title, priority, status, assignee

## Available Tools

| Category | Tools |
|----------|-------|
| Issues | `linear_get_issue`, `linear_list_issues`, `linear_save_issue` |
| Comments | `linear_list_comments`, `linear_save_comment`, `linear_delete_comment` |
| Projects | `linear_list_projects`, `linear_get_project`, `linear_save_project` |
| Teams | `linear_list_teams`, `linear_get_team` |
| Users | `linear_list_users`, `linear_get_user` |
| Statuses | `linear_list_issue_statuses`, `linear_get_issue_status` |
| Labels | `linear_list_issue_labels`, `linear_create_issue_label` |
| Documents | `linear_list_documents`, `linear_get_document`, `linear_save_document` |
| Milestones | `linear_list_milestones`, `linear_get_milestone`, `linear_save_milestone` |
| Cycles | `linear_list_cycles` |
| Attachments | `linear_get_attachment`, `linear_create_attachment`, `linear_delete_attachment` |
| Diffs/Reviews | `linear_list_diffs`, `linear_get_diff`, `linear_get_diff_threads` |
| Status Updates | `linear_get_status_updates`, `linear_save_status_update`, `linear_delete_status_update` |

## Notes

- Always confirm the issue was created successfully before reporting to the user
- Default assignee is read from `~/.config/opencode/.linear-skill.env` (`LINEAR_DEFAULT_ASSIGNEE_ID`)
- Never store Linear tokens in code or commit them
- State names are case-sensitive — use exact names from `linear_list_issue_statuses`
- No delete-issue tool — use `linear_save_issue` to set state to "Canceled" instead
