import os
import io
import zipfile
import shutil
import re
import requests
from base64 import b64decode

def process_git_repo(provider, base_url, org_name, repo_name, token, search_file, mode='filename', branch='main'):
    """
    Downloads and processes a GitHub/GitLab repo. 
    Returns a list of matching files with content.
    """
    if provider.lower() == 'github':
        api_url = f"{base_url}/repos/{org_name}/{repo_name}/zipball/{branch}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    elif provider.lower() == 'gitlab':
        encoded_project = f"{org_name}/{repo_name}".replace("/", "%2F")
        api_url = f"{base_url}/api/v4/projects/{encoded_project}/repository/archive.zip?sha={branch}"
        headers = {
            "PRIVATE-TOKEN": token
        }
    else:
        raise ValueError("Unsupported provider. Use 'github' or 'gitlab'.")

    # Step 1: Download ZIP
    print(f"Downloading {provider} repo '{repo_name}' from {api_url}")
    response = requests.get(api_url, headers=headers, stream=True)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch zip: {response.status_code} {response.text}")

    # Step 2: Extract to temp folder
    temp_root = os.path.join(os.getcwd(), f"temp_{repo_name}")
    if os.path.exists(temp_root):
        shutil.rmtree(temp_root)

    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        zip_ref.extractall(temp_root)

    extracted_dir = os.path.join(temp_root, os.listdir(temp_root)[0])  # first extracted folder
    dag_files = []
    dag_num = 1

    # Step 3: Walk and search files
    for root, _, files in os.walk(extracted_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if mode.strip().lower() == 'filename' and re.search(search_file, file, re.IGNORECASE):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                dag_files.append({
                    "dag_num": dag_num,
                    "filename": file,
                    "content": content
                })
                dag_num += 1

    # Step 4: Cleanup temp folder
    shutil.rmtree(temp_root)
    return dag_files
