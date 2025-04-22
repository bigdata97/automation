import requests
import ast
import sys
import pkgutil
import base64

# Step 1: Setup standard Python modules
STANDARD_MODULES = set([name for _, name, _ in pkgutil.iter_modules()] + list(sys.builtin_module_names))

def is_project_module(module_name):
    """Filter out standard library modules."""
    return module_name.split('.')[0] not in STANDARD_MODULES

# Step 2: Extract imports from DAG content
def extract_imports_from_code(content: str):
    imported_modules = set()
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if is_project_module(alias.name):
                    imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and is_project_module(node.module):
                imported_modules.add(node.module)

    return list(imported_modules)

# Step 3: List all .py files recursively in GitHub repo via API
def list_all_python_files(api_url, token):
    """Recursively list all .py files in a GitHub repo using GitHub API."""
    headers = {'Authorization': f'token {token}'}
    all_files = []

    def traverse(path=""):
        url = f"{api_url}/contents/{path}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to access {url}: {response.status_code}")
            return

        for item in response.json():
            if item['type'] == 'file' and item['name'].endswith('.py'):
                all_files.append(item['path'])
            elif item['type'] == 'dir':
                traverse(item['path'])

    traverse()
    return all_files

# Step 4: Match imports to repo files
def find_matching_files(imports, all_py_files):
    matched_files = []

    for module in imports:
        expected_path = module.replace(".", "/") + ".py"
        for f in all_py_files:
            if f.endswith(expected_path):
                matched_files.append(f)
                break
    return matched_files

# === FINAL FUNCTION: CALL THIS ===
def get_dependent_files_from_dag_content(dag_content: str, api_url: str, token: str) -> list:
    """
    :param dag_content: string content of the DAG Python file
    :param api_url: GitHub API URL, e.g., https://api.github.com/repos/org/repo
    :param token: GitHub personal access token
    :return: list of dependent .py files used by this DAG
    """
    imports = extract_imports_from_code(dag_content)
    all_py_files = list_all_python_files(api_url, token)
    return find_matching_files(imports, all_py_files)
