import os
from dotenv import load_dotenv
import requests

load_dotenv()

GITHUB_API = "https://api.github.com"
GITHUB_GRAPHQL = "https://api.github.com/graphql"
SRC_REPO = os.getenv('SRC_REPO')
DEST_REPO = os.getenv('DEST_REPO')
TOKEN = os.getenv('GH_TOKEN')
PROJECT_NODE_ID = os.getenv('PROJECT_NODE_ID')
STATUS_FIELD_ID = os.getenv('STATUS_FIELD_ID')
TODO_OPTION_ID = os.getenv('TODO_OPTION_ID')

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_issues(repo):
    url = f"{GITHUB_API}/repos/{repo}/issues?state=open"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return [i for i in resp.json() if 'pull_request' not in i]

def create_issue(repo, issue):
    url = f"{GITHUB_API}/repos/{repo}/issues"
    data = {
        "title": issue['title'],
        "body": issue.get('body', ''),
        "labels": [l['name'] for l in issue.get('labels', [])]
    }
    resp = requests.post(url, headers=HEADERS, json=data)
    resp.raise_for_status()
    return resp.json()

def add_issue_to_project(issue_node_id):
    query = """
    mutation($project:ID!, $content:ID!) {
      addProjectV2ItemById(input: {projectId: $project, contentId: $content}) {
        item {
          id
        }
      }
    }
    """
    variables = {
        "project": PROJECT_NODE_ID,
        "content": issue_node_id
    }
    resp = requests.post(GITHUB_GRAPHQL, headers=HEADERS, json={"query": query, "variables": variables})
    resp.raise_for_status()
    data = resp.json()
    item_id = data["data"]["addProjectV2ItemById"]["item"]["id"]
    return item_id

def set_item_status(item_id):
    query = """
    mutation($project:ID!, $item:ID!, $field:ID!, $option:ID!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $project,
        itemId: $item,
        fieldId: $field,
        value: { singleSelectOptionId: $option }
      }) {
        projectV2Item {
          id
        }
      }
    }
    """
    variables = {
        "project": PROJECT_NODE_ID,
        "item": item_id,
        "field": STATUS_FIELD_ID,
        "option": TODO_OPTION_ID
    }
    resp = requests.post(GITHUB_GRAPHQL, headers=HEADERS, json={"query": query, "variables": variables})
    resp.raise_for_status()
    return resp.json()

def main():
    print(f"Copying issues from {SRC_REPO} to {DEST_REPO}")
    issues = get_issues(SRC_REPO)
    for issue in issues:
        new_issue = create_issue(DEST_REPO, issue)
        print(f"Created issue #{new_issue['number']}: {new_issue['title']}")
        issue_node_id = new_issue["node_id"]
        item_id = add_issue_to_project(issue_node_id)
        print(f"Added to Projects Beta board as item {item_id}")
        set_item_status(item_id)
        print("Set Kanban status to '📋 Backlog'.")

if __name__ == "__main__":
    main()
