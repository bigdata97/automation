import re
import importlib.util
import pandas as pd
import os
import sys

print(os.getcwd())

pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', 0)
pd.set_option('display.max_columns', None)

# ---- Step 1: Read full file ----
input_file = "test11.py"
with open(input_file, "r", encoding="utf-8") as f:
    content = f.read()

# ---- Step 2: Find import statements ----
imported_modules = {}   # e.g., { 'config_file': 'config_file' }
from_imports = {}       # e.g., { 'config_file': 'config.config_file' }

# Match: import config_file
for match in re.findall(r'^\s*import\s+([\w_]+)', content, re.MULTILINE):
    imported_modules[match] = match

# Match: from config import config_file
for match in re.findall(r'^\s*from\s+([\w_\.]+)\s+import\s+([\w_]+)', content, re.MULTILINE):
    full_module, alias = match
    from_imports[alias] = f"{full_module}.{alias}"

all_imports = {**imported_modules, **from_imports}

# ---- Step 3: Load all imported modules ----
loaded_modules = {}
for alias, module_path in all_imports.items():
    try:
        spec = importlib.util.find_spec(module_path)
        if spec and spec.origin:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            loaded_modules[alias] = module
    except Exception as e:
        print(f"Warning: Could not load module '{module_path}': {e}")

# ---- Step 4: Extract assignments like VAR = module.ATTR ----
assignments = re.findall(r'^\s*(\w+)\s*=\s*([\w_]+)\.(\w+)', content, re.MULTILINE)
# e.g., [('VAR', 'config_file', 'ATTR')]

# ---- Step 5: Extract local literal assignments like VAR = "value" or VAR = 123 ----
local_assignments = re.findall(r'^\s*(\w+)\s*=\s*([\'"]?[\w\./\- ]+[\'"]?)', content, re.MULTILINE)
# Caution: regex won't handle complex values or multi-line strings

# ---- Step 6: Build variable map ----
variable_map = {}

# Assignments from modules
for var, module_alias, attr in assignments:
    module = loaded_modules.get(module_alias)
    if module and hasattr(module, attr):
        variable_map[var] = getattr(module, attr)

# Local literals
for var, val in local_assignments:
    if var not in variable_map:
        cleaned = val.strip('\'"')  # remove quotes if any
        variable_map[var] = cleaned

# ---- Step 7: Show resolved vars ----
for var, value in variable_map.items():
    print(f"*** {var = } AND {value = }")

# ---- Step 8: Replace placeholders ----
def resolve_table_name(table_name):
    for var, value in variable_map.items():
        table_name = table_name.replace(f"{{{var}}}", value)
    return table_name

# ---- Example usage ----
tablelist = [
    "{BQ_DATASET}.T_340B_DIR_CLMS_CORAM_WP",
    "{BQ_DATASET}.T_340B_PHCY_BLOCK_LIST",
    "{BQ_DATASET_DR}.T_340B_CORAM_CLAIMS_ALL_DATA_tmp"
]

print("\n")
for table in tablelist:
    t = resolve_table_name(table)
    print(f"{table=} ---> {t=}")





import re
import importlib.util
import sys
import os

def resolve_module_from_sys_path(content, module_name):
    # 1. Extract all sys.path.append() values
    path_append_matches = re.findall(r'sys\.path\.append\((["\'])(.*?)\1\)', content)

    for _, raw_path in path_append_matches:
        # Convert to absolute path
        abs_path = os.path.abspath(raw_path)
        if abs_path not in sys.path:
            sys.path.append(abs_path)

        # 2. Try to locate the module in that path
        candidate_path = os.path.join(abs_path, f"{module_name}.py")
        if os.path.exists(candidate_path):
            spec = importlib.util.spec_from_file_location(module_name, candidate_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

        # 3. If it's part of a package (i.e., subfolder/module)
        pkg_path = os.path.join(abs_path, module_name, "__init__.py")
        if os.path.exists(pkg_path):
            spec = importlib.util.spec_from_file_location(module_name, pkg_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

    # 4. Fallback to global importlib (may work if path is already in sys.path)
    try:
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    except Exception:
        pass

    # If not found
    raise ImportError(f"Unable to locate or load module '{module_name}'")

# ✅ Example usage:

# Read your input file
with open("test11.py", "r", encoding="utf-8") as f:
    content = f.read()

# Try to resolve config_file dynamically
try:
    config_file = resolve_module_from_sys_path(content, "config_file")
except ImportError as e:
    print(f"Error: {e}")



