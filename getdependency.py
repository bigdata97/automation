import ast
import os
import sys
import pkgutil

# Detect standard modules (only once)
STANDARD_MODULES = set([name for _, name, _ in pkgutil.iter_modules()] + list(sys.builtin_module_names))

def is_project_module(module_name):
    return module_name.split('.')[0] not in STANDARD_MODULES

def extract_imports_from_code(content: str):
    tree = ast.parse(content)
    imported_modules = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if is_project_module(alias.name):
                    imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and is_project_module(node.module):
                imported_modules.add(node.module)

    return list(imported_modules)

def list_all_python_files(repo_path):
    python_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)
                python_files.append(rel_path)
    return python_files

def find_matching_files(imports, repo_path):
    all_files = list_all_python_files(repo_path)
    import_to_file = {}

    for module in imports:
        expected_path = os.path.join(*module.split(".")) + ".py"
        for f in all_files:
            if f.endswith(expected_path):
                import_to_file[module] = f
                break
    return list(import_to_file.values())

# === Main function you will call for each DAG file ===
def get_dependent_files_for_dag(dag_file_path: str, repo_path: str, git_url: str, repo_name: str, org_name: str, git_token: str) -> list:
    """
    Returns a list of dependent Python file paths used in the given DAG file.
    """
    try:
        with open(dag_file_path, "r") as f:
            dag_content = f.read()
    except Exception as e:
        print(f"Failed to read DAG file {dag_file_path}: {e}")
        return []

    imported_modules = extract_imports_from_code(dag_content)
    matched_files = find_matching_files(imported_modules, repo_path)
    
    print(f"[INFO] DAG: {dag_file_path}")
    print(f"[INFO] Found {len(matched_files)} dependent files:")
    for f in matched_files:
        print("    -", f)
    
    return matched_files
