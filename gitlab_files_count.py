import requests
from urllib.parse import urlparse, quote_plus

def get_project_path_from_url(gitlab_url):
    parsed = urlparse(gitlab_url)
    return parsed.path.strip("/")

def get_project_info(gitlab_base, project_path, token):
    encoded_path = quote_plus(project_path)
    url = f"{gitlab_base}/api/v4/projects/{encoded_path}"
    headers = {"PRIVATE-TOKEN": token}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting project info for {project_path}: {response.status_code}")
        return None

def get_file_count(gitlab_base, project_id, default_branch, token):
    url = f"{gitlab_base}/api/v4/projects/{project_id}/repository/tree"
    headers = {"PRIVATE-TOKEN": token}
    params = {
        "recursive": True,
        "ref": default_branch,
        "per_page": 100
    }

    file_count = 0
    page = 1
    while True:
        params["page"] = page
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Error fetching files for project {project_id}: {response.status_code}")
            return None
        data = response.json()
        file_count += sum(1 for item in data if item["type"] == "blob")
        if len(data) < 100:
            break  # No more pages
        page += 1

    return file_count

# Input: GitLab URLs
gitlab_urls = [
    "https://gitw.cvshealth.com/pbm/dfm",
    "https://gitw.cvshealth.com/analytics/reporting-engine"
]

gitlab_token = "your_gitlab_token"
gitlab_base = "https://gitw.cvshealth.com"

# Main logic
for url in gitlab_urls:
    project_path = get_project_path_from_url(url)
    project_info = get_project_info(gitlab_base, project_path, gitlab_token)
    
    if project_info:
        project_id = project_info["id"]
        default_branch = project_info.get("default_branch", "main")
        file_count = get_file_count(gitlab_base, project_id, default_branch, gitlab_token)
        
        print(f"Repo: {project_path}")
        print(f"  Project ID     : {project_id}")
        print(f"  Default Branch : {default_branch}")
        print(f"  File Count     : {file_count}")
        print("-" * 40)
