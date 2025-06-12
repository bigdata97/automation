import os
import re
import importlib.util
from pathlib import Path

def resolve_module_by_folder_name(content, module_name, base_file_path):
    """
    - Extracts last folder from sys.path.append(...) (e.g., 'configs')
    - Finds matching folder in repo
    - Loads module (e.g., config_file.py) from that folder
    """
    repo_root = find_repo_root(Path(base_file_path))
    path_append_matches = re.findall(r'sys\.path\.append\((["\'])(.*?)\1\)', content)

    for _, raw_path in path_append_matches:
        last_folder = Path(raw_path).parts[-1]  # e.g., 'configs'
        matching_dirs = list(repo_root.rglob(last_folder))

        for config_dir in matching_dirs:
            if config_dir.is_dir():
                candidate_path = config_dir / f"{module_name}.py"
                if candidate_path.exists():
                    spec = importlib.util.spec_from_file_location(module_name, str(candidate_path))
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    return module

    raise ImportError(f"Could not resolve module '{module_name}' from sys.path.append() folders")


def find_repo_root(start_path: Path) -> Path:
    """Walks upward to find the repo root (where .git or known files exist)."""
    path = start_path.resolve()
    while path != path.parent:
        if (path / ".git").exists() or (path / "README.md").exists():
            return path
        path = path.parent
    raise FileNotFoundError("Could not locate repo root from base path")
