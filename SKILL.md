---
name: linear
description: "Create and manage Linear issues. Use when the user says 'add to Linear', 'track in Linear', 'create Linear issue', or explicitly asks to log work in Linear. Team: SA. Also: when working on a task related to a known Linear issue, read it before work and update it during work."
---

# Linear Issue Management

## Mandatory: Read Before Work, Update During Work

Whenever you know (from context) that a task relates to a Linear issue — whether the user mentioned the ID, named a project, or the work clearly maps to an existing issue — you MUST:

1. **Read the issue first** — before writing any code, fetch the issue to understand its description, requirements, and acceptance criteria:
   ```bash
   python3 linear_api.py get-issue <issue_id>
   ```
2. **Set status to "In Progress"** — do this whenever you start working on an issue:
   - If you just created the issue and are starting work immediately, set it right after creation
   - If you're picking up an existing issue, set it before writing any code
   ```bash
   python3 linear_api.py update-issue <issue_id> stateId=<in_progress_state_id>
   ```
3. **Comment on progress** after significant milestones or at end of session:
   ```bash
   python3 linear_api.py add-comment <issue_id> "<what was done, files changed, how tested>"
   ```
4. **Move to "In Review" when implementation is complete** — after finishing the work and the user has reviewed the summary, move the issue to "In Review" to signal it's ready for their final review. This is the expected terminal state for the AI's workflow.
   ```bash
   python3 linear_api.py update-issue <issue_id> stateId=<in_review_state_id>
   ```
5. **Only close to "Done" when explicitly asked** — the user may ask you to close a ticket. In that case, first look up the "Done" state ID using `list-states`, then update:
   ```bash
   python3 linear_api.py list-states <team_id>
   python3 linear_api.py update-issue <issue_id> stateId=<done_state_id>
   ```

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
- **API**: use `linear_api.py` (located alongside this SKILL.md) via bash

## Workflow: Creating an Issue

When the user asks to add something to Linear:

0. **Check for duplicates first** — before creating, search existing open issues for the same or similar title:
   ```bash
   python3 linear_api.py list-project-issues <project_id>
   ```
   Scan the results. If an open issue already covers the same scope, inform the user and do NOT create a duplicate. If the user confirms it's genuinely different, proceed.

1. **Gather info from context** — use the current task/conversation to populate:
   - `title`: concise summary (imperative mood, e.g. "Add dark mode toggle to settings")
   - `description`: markdown body with:
     - **Context**: why this is needed (1-2 sentences)
     - **Requirements**: bullet list of what needs to happen
     - **Acceptance Criteria**: how to verify it's done
   - `priority`: infer from urgency (1=urgent, 2=high, 3=medium, 4=low). Default to 4 (low) if unclear.
   - `teamId`: look up the SA team ID using `python3 linear_api.py list-teams`
   - `projectId`: look up using `python3 linear_api.py list-projects` and match by name
   - `assigneeId`: read from `~/.config/opencode/.linear-skill.env` (`LINEAR_DEFAULT_ASSIGNEE_ID`). If unset, leave unassigned.

2. **Create the issue** using:
   ```bash
   python3 linear_api.py create-issue <team_id> "<title>" "<description>" <priority> <project_id> <assignee_id>
   ```
   The description should be a single string — use `\n` for newlines or pass it as a single-quoted multiline string.

3. **Report back** — show the user the issue identifier (e.g. `SA-123`)

## Workflow: Updating After Completion

When you complete a task that has an associated Linear issue:

1. **Add a comment** to the issue with:
   - What was done (summary of changes)
   - Files modified
   - How it was tested / verified
   ```bash
   python3 linear_api.py add-comment <issue_id> "<comment body>"
   ```
2. **Move to "In Review"** — this signals the implementation is done and ready for the user to review. Do NOT move to "Done" or any final state; only the user can close an issue.
   ```bash
   python3 linear_api.py update-issue <issue_id> stateId=<in_review_state_id>
   ```

## Workflow: Marking an Issue as Duplicate

When an issue is identified as a duplicate of another:

1. **Find the "Duplicate" state ID** — it's a `canceled`-type state, not `completed`:
   ```bash
   python3 linear_api.py list-states <team_id>
   ```
   Look for the state named "Duplicate" (type: canceled).

2. **Update the issue** using `stateId=` (not `state=`):
   ```bash
   python3 linear_api.py update-issue <issue_id> stateId=<duplicate_state_id>
   ```

3. **Optionally add a comment** linking to the parent issue:
   ```bash
   python3 linear_api.py add-comment <issue_id> "Duplicate of <parent_issue_id>"
   ```

Note: The field is `stateId` (not `state`), and the value is a UUID, not a string name. Always use `list-states` to look it up.

## Workflow: Searching / Listing Issues

If the user asks about existing Linear issues or wants to see open issues for a project:

1. **Find the project** — `python3 linear_api.py list-projects`, match by name
2. **List open issues** — `python3 linear_api.py list-project-issues <project_id>`
3. **Present results** as a table with ID, title, priority, status, assignee

## Tool Reference

Use `linear_api.py` (located alongside this SKILL.md) via bash:

| Command | Purpose |
|---------|---------|
| `python3 linear_api.py list-teams` | List all teams |
| `python3 linear_api.py list-projects` | List all projects |
| `python3 linear_api.py list-users` | List all users |
| `python3 linear_api.py list-states <team_id>` | List workflow states (get stateId for status updates) |
| `python3 linear_api.py list-project-issues <project_id>` | List open issues for a project |
| `python3 linear_api.py get-issue <issue_id>` | Get full issue details + comments |
| `python3 linear_api.py create-issue <team_id> "<title>" "<desc>" <priority> [project_id] [assignee_id]` | Create an issue |
| `python3 linear_api.py update-issue <issue_id> field=value...` | Update issue fields |
| `python3 linear_api.py add-comment <issue_id> "<body>"` | Add a comment |
| `python3 linear_api.py delete-issue <issue_id>` | Delete an issue |

## Notes

- Always confirm the issue was created successfully before reporting to the user
- Config is read from `~/.config/opencode/.linear-skill.env` — both `LINEAR_API_KEY` and `LINEAR_DEFAULT_ASSIGNEE_ID`
- Never store Linear tokens in code or commit them
