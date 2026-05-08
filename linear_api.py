#!/usr/bin/env python3
"""
Linear API helper for OpenCode Linear skill.
Usage: python3 linear_api.py <action> [args...]

Actions:
  list-teams                              List all teams
  list-projects                           List all projects
  list-users                              List all users
  list-project-issues <project_id>        List open issues for a project
  list-states <team_id>                   List workflow states (IDs needed for stateId)
  create-issue <team_id> <title> <desc> <priority> [project_id] [assignee_id]
  update-issue <issue_id> <field=value>...   Update issue fields (title, description, priority, assigneeId, stateId)
  add-comment <issue_id> <body>           Add comment to issue
  delete-issue <issue_id>                 Delete an issue

Config: reads LINEAR_API_KEY and LINEAR_DEFAULT_ASSIGNEE_ID from:
  1. Environment variables
  2. ~/.config/opencode/.linear-skill.env
"""

import json
import os
import sys
import urllib.request

CONFIG_PATH = os.path.expanduser("~/.config/opencode/.linear-skill.env")
API_URL = "https://api.linear.app/graphql"


def load_config():
    """Load config from env file, preferring actual env vars."""
    config = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    config[k.strip()] = v.strip()
    # Env vars override file
    config["LINEAR_API_KEY"] = os.environ.get("LINEAR_API_KEY") or config.get("LINEAR_API_KEY", "")
    config["LINEAR_DEFAULT_ASSIGNEE_ID"] = os.environ.get("LINEAR_DEFAULT_ASSIGNEE_ID") or config.get("LINEAR_DEFAULT_ASSIGNEE_ID", "")
    return config


def api(query, variables=None):
    """Call Linear GraphQL API."""
    config = load_config()
    token = config.get("LINEAR_API_KEY")
    if not token:
        print("ERROR: LINEAR_API_KEY not set. Check ~/.config/opencode/.linear-skill.env")
        sys.exit(1)

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": token,
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"API Error {e.code}: {body}")
        sys.exit(1)


def list_teams():
    result = api("{ teams { nodes { id name key } } }")
    for t in result["data"]["teams"]["nodes"]:
        print(f"{t['id']}  {t['key']}  {t['name']}")


def list_projects():
    result = api("{ projects(first: 50) { nodes { id name } } }")
    for p in result["data"]["projects"]["nodes"]:
        print(f"{p['id']}  {p['name']}")


def list_users():
    result = api("{ users { nodes { id name email } } }")
    for u in result["data"]["users"]["nodes"]:
        if "linear.linear.app" not in u.get("email", ""):
            print(f"{u['id']}  {u['name']}  {u['email']}")


def list_project_issues(project_id):
    q = """query($projectId: String!) {
      project(id: $projectId) {
        name
        issues(first: 50, filter: { completedAt: { null: true } }) {
          nodes {
            identifier
            title
            priority
            state { name }
            assignee { name }
          }
        }
      }
    }"""
    result = api(q, {"projectId": project_id})
    project = result["data"]["project"]
    if not project:
        print(f"Project not found: {project_id}")
        return
    issues = project["issues"]["nodes"]
    print(f"\nOpen issues for {project['name']} ({len(issues)} total):")
    print(f"{'ID':<10} {'Priority':<8} {'Status':<15} {'Assignee':<20} Title")
    print("-" * 80)
    priority_labels = {1: "Urgent", 2: "High", 3: "Medium", 4: "Low", 0: "None"}
    for i in issues:
        pri = priority_labels.get(i["priority"], str(i["priority"]))
        assignee = i["assignee"]["name"] if i.get("assignee") else "Unassigned"
        status = i["state"]["name"] if i.get("state") else "Unknown"
        print(f"{i['identifier']:<10} {pri:<8} {status:<15} {assignee:<20} {i['title']}")


def list_states(team_id):
    """List workflow states for a team (IDs needed for update-issue stateId=)."""
    q = """query($teamId: String!) {
      team(id: $teamId) {
        name
        states { nodes { id name type } }
      }
    }"""
    result = api(q, {"teamId": team_id})
    team = result.get("data", {}).get("team")
    if not team:
        print(f"Team not found: {team_id}")
        return
    print(f"\nWorkflow states for {team['name']}:")
    print(f"{'State ID':<40} {'Name':<20} Type")
    print("-" * 80)
    for s in team["states"]["nodes"]:
        print(f"{s['id']:<40} {s['name']:<20} {s['type']}")


def create_issue(team_id, title, description, priority, project_id=None, assignee_id=None):
    variables = {
        "input": {
            "title": title,
            "description": description,
            "priority": int(priority),
            "teamId": team_id,
        }
    }
    if project_id and project_id != "null":
        variables["input"]["projectId"] = project_id
    if assignee_id and assignee_id != "null":
        variables["input"]["assigneeId"] = assignee_id

    m = """mutation($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue { identifier title project { name } assignee { name } }
      }
    }"""
    result = api(m, variables)
    d = result["data"]["issueCreate"]
    if d["success"]:
        i = d["issue"]
        project = i["project"]["name"] if i.get("project") else "No project"
        assignee = i["assignee"]["name"] if i.get("assignee") else "Unassigned"
        print(f"✓ Created {i['identifier']}: {i['title']} (Project: {project}, Assignee: {assignee})")
    else:
        print("✗ Failed to create issue")
        print(json.dumps(result, indent=2))


def update_issue(issue_id, **fields):
    variables = {"id": issue_id, "input": fields}
    m = """mutation($id: String!, $input: IssueUpdateInput!) {
      issueUpdate(id: $id, input: $input) {
        success
        issue { identifier title }
      }
    }"""
    result = api(m, variables)
    d = result["data"]["issueUpdate"]
    if d["success"]:
        print(f"✓ Updated {d['issue']['identifier']}: {d['issue']['title']}")
    else:
        print("✗ Failed to update issue")


def add_comment(issue_id, body):
    variables = {"input": {"issueId": issue_id, "body": body}}
    m = """mutation($input: CommentCreateInput!) {
      commentCreate(input: $input) {
        success
        comment { id }
      }
    }"""
    result = api(m, variables)
    if result["data"]["commentCreate"]["success"]:
        print(f"✓ Comment added to {issue_id}")
    else:
        print("✗ Failed to add comment")


def delete_issue(issue_id):
    m = """mutation($id: String!) { issueDelete(id: $id) { success } }"""
    result = api(m, {"id": issue_id})
    if result["data"]["issueDelete"]["success"]:
        print(f"✓ Deleted {issue_id}")
    else:
        print("✗ Failed to delete issue")


def get_issue(issue_id):
    q = """query($id: String!) {
      issue(id: $id) {
        identifier
        title
        description
        priority
        state { name }
        assignee { name }
        project { name }
        labels { nodes { name } }
        comments(first: 20) {
          nodes { body user { name } createdAt }
        }
      }
    }"""
    result = api(q, {"id": issue_id})
    issue = result.get("data", {}).get("issue")
    if not issue:
        print(f"Issue not found: {issue_id}")
        return
    priority_labels = {1: "Urgent", 2: "High", 3: "Medium", 4: "Low", 0: "None"}
    print(f"{'='*60}")
    print(f"{issue['identifier']}: {issue['title']}")
    print(f"{'='*60}")
    print(f"Status:   {issue['state']['name'] if issue.get('state') else 'Unknown'}")
    print(f"Priority: {priority_labels.get(issue['priority'], str(issue['priority']))}")
    print(f"Assignee: {issue['assignee']['name'] if issue.get('assignee') else 'Unassigned'}")
    print(f"Project:  {issue['project']['name'] if issue.get('project') else 'None'}")
    labels = [l["name"] for l in issue.get("labels", {}).get("nodes", [])]
    if labels:
        print(f"Labels:   {', '.join(labels)}")
    print()
    if issue.get("description"):
        print("--- Description ---")
        print(issue["description"])
    comments = issue.get("comments", {}).get("nodes", [])
    if comments:
        print(f"\n--- Comments ({len(comments)}) ---")
        for c in comments:
            user = c.get("user", {}).get("name", "Unknown")
            print(f"\n[{user}]")
            print(c["body"])


def get_issue(issue_id):
    q = """query($id: String!) {
      issue(id: $id) {
        identifier
        title
        description
        priority
        state { name }
        assignee { name }
        project { name }
        labels { nodes { name } }
        comments(first: 20) {
          nodes { body user { name } createdAt }
        }
      }
    }"""
    result = api(q, {"id": issue_id})
    issue = result.get("data", {}).get("issue")
    if not issue:
        print(f"Issue not found: {issue_id}")
        return
    priority_labels = {1: "Urgent", 2: "High", 3: "Medium", 4: "Low", 0: "None"}
    print(f"{'='*60}")
    print(f"{issue['identifier']}: {issue['title']}")
    print(f"{'='*60}")
    print(f"Status:   {issue['state']['name'] if issue.get('state') else 'Unknown'}")
    print(f"Priority: {priority_labels.get(issue['priority'], str(issue['priority']))}")
    print(f"Assignee: {issue['assignee']['name'] if issue.get('assignee') else 'Unassigned'}")
    print(f"Project:  {issue['project']['name'] if issue.get('project') else 'None'}")
    labels = [l["name"] for l in issue.get("labels", {}).get("nodes", [])]
    if labels:
        print(f"Labels:   {', '.join(labels)}")
    print()
    if issue.get("description"):
        print("--- Description ---")
        print(issue["description"])
    comments = issue.get("comments", {}).get("nodes", [])
    if comments:
        print(f"\n--- Comments ({len(comments)}) ---")
        for c in comments:
            user_obj = c.get("user")
            user = user_obj.get("name", "Unknown") if user_obj else "System"
            print(f"\n[{user}]")
            print(c["body"])


if __name__ == "__main__":
    cfg = load_config()
    if not cfg.get("LINEAR_API_KEY"):
        print("ERROR: LINEAR_API_KEY not set.")
        print(f"Create {CONFIG_PATH} with:")
        print("  LINEAR_API_KEY=your_token_here")
        sys.exit(1)

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]

    if action == "list-teams":
        list_teams()
    elif action == "list-projects":
        list_projects()
    elif action == "list-users":
        list_users()
    elif action == "list-project-issues" and len(sys.argv) >= 3:
        list_project_issues(sys.argv[2])
    elif action == "list-states" and len(sys.argv) >= 3:
        list_states(sys.argv[2])
    elif action == "create-issue" and len(sys.argv) >= 5:
        team_id = sys.argv[2]
        title = sys.argv[3]
        desc = sys.argv[4]
        priority = sys.argv[5] if len(sys.argv) > 5 else 4
        project_id = sys.argv[6] if len(sys.argv) > 6 else None
        assignee_id = sys.argv[7] if len(sys.argv) > 7 else cfg.get("LINEAR_DEFAULT_ASSIGNEE_ID")
        create_issue(team_id, title, desc, priority, project_id, assignee_id)
    elif action == "update-issue" and len(sys.argv) >= 4:
        issue_id = sys.argv[2]
        fields = {}
        for arg in sys.argv[3:]:
            if "=" in arg:
                k, v = arg.split("=", 1)
                fields[k] = v
        update_issue(issue_id, **fields)
    elif action == "add-comment" and len(sys.argv) >= 4:
        add_comment(sys.argv[2], sys.argv[3])
    elif action == "delete-issue" and len(sys.argv) >= 3:
        delete_issue(sys.argv[2])
    elif action == "get-issue" and len(sys.argv) >= 3:
        get_issue(sys.argv[2])
    else:
        print(f"Unknown action or missing args: {action}")
        print(__doc__)
        sys.exit(1)
