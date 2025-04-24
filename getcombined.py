import ast
import csv
import re
import requests

# --- Step 1: Extract table names from DAG content ---
def extract_table_names_from_content(file_path, file_name, file_extension, content):
    table_data = []
    input_pattern = re.compile(r'\bFROM\s+([a-zA-Z0-9_\.]+)', re.IGNORECASE)
    output_pattern = re.compile(r'\b(?:INSERT\s+INTO|CREATE\s+TABLE)\s+([a-zA-Z0-9_\.]+)', re.IGNORECASE)

    input_matches = input_pattern.findall(content)
    for table in input_matches:
        table_data.append((file_path, file_name, file_extension, table, "Input"))

    output_matches = output_pattern.findall(content)
    for table in output_matches:
        table_data.append((file_path, file_name, file_extension, table, "Output"))

    if not input_matches and not output_matches:
        table_data.append((file_path, file_name, file_extension, "No Matches", "N/A"))

    return table_data

# --- Step 2: Extract imports from DAG code ---
STANDARD_MODULES = set(["os", "re", "csv", "sys", "time", "datetime"])

def extract_imports_from_code(content: str):
    imported_modules = set()
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)

    return list(imported_modules)

# --- Step 3: List all .py files via GitHub API ---
def list_all_python_files(git_base_url, org_name, repo_name, git_token):
    headers = {
        "Authorization": f"token {git_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(f"{git_base_url}/repos/{org_name}/{repo_name}", headers=headers)
    default_branch = response.json().get("default_branch") if response.status_code == 200 else "main"

    all_files = []
    def traverse(path=""):
        url = f"{git_base_url}/repos/{org_name}/{repo_name}/git/trees/{default_branch}?recursive=1"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to access {url}: {response.status_code}")
            return

        for item in response.json().get("tree", []):
            if item["type"] == "blob" and item["path"].endswith(".py"):
                all_files.append(item["path"])

    traverse()
    return all_files

# --- Step 4: Process each file and extract table data ---
def process_files(git_base_url, org_name, repo_name, git_token, output_csv):
    all_py_files = list_all_python_files(git_base_url, org_name, repo_name, git_token)
    headers = {
        "Authorization": f"token {git_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    all_table_data = []

    for file_path in all_py_files:
        raw_url = f"https://raw.githubusercontent.com/{org_name}/{repo_name}/main/{file_path}"
        response = requests.get(raw_url, headers=headers)
        if response.status_code != 200:
            continue

        content = response.text
        file_name = file_path.split("/")[-1]
        file_extension = file_name.split(".")[-1]

        table_rows = extract_table_names_from_content(file_path, file_name, file_extension, content)
        all_table_data.extend(table_rows)

    with open(output_csv, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["FilePath", "FileName", "FileType", "Table Name", "Type of Table"])
        writer.writerows(all_table_data)

# --- Usage ---
# process_files("https://api.github.com", "your_org", "your_repo", "your_token", "output_tables.csv")
