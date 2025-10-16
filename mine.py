import requests
import json

def get_github_pull_requests(owner, repo, token, page=1):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    params = {
        "state": "closed",
        "page": page,
        "per_page": 100
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()  # Raise an exception for bad status codes
    return response.json()


def get_all_pages(owner, repo, token):
    all_prs = []
    page = 1
    while True:
        prs = get_github_pull_requests(owner, repo, token, page)
        print(page)
        if not prs:
            break
        all_prs.extend(prs)
        page += 1
    return all_prs


def write_to_json_file(data, filename):
    with open(filename, 'w') as f:
        f.write(json.dumps(data, indent=4))

def get_useful_info(pr):
    return {
        "id": pr["id"],
        "title": pr["title"],
        "created_at": pr["created_at"],
        "closed_at": pr["closed_at"],
        "merged_at": pr.get("merged_at"),
    }

def move_through_prs(prs):
    useful_prs = [get_useful_info(pr) for pr in prs]
    return useful_prs


files_names = {
    "curl": "curl",
}
for name in files_names.keys():
    data = get_all_pages(name, files_names[name], "YOUR_GITHUB_TOKEN_HERE")
    print(len(data))
    useful_data = move_through_prs(data)
    file_name = name + ".json"
    write_to_json_file(useful_data, file_name)