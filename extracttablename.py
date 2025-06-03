import os
import re
import csv
import shutil
from pathlib import Path

def extract_sql_blocks(content):
    sql_blocks = []

    # Look for SQL string assignments (e.g., sql = """ SELECT * FROM ... """)
    string_sql_blocks = re.findall(r'(?:sql|query)\s*=\s*[rRuU]?("""|\'\'\'|["\'])(.*?)(\1)', content, re.DOTALL)
    for _, block, _ in string_sql_blocks:
        if 'SELECT' in block.upper() or 'INSERT' in block.upper() or 'CREATE' in block.upper():
            sql_blocks.append(block)

    return sql_blocks

def extract_tables_from_sql(sql_text, input_pattern, output_pattern):
    input_tables = input_pattern.findall(sql_text)
    output_tables = output_pattern.findall(sql_text)
    return input_tables, output_tables

def extract_sql_table_info(repo_path, output_file):
    input_pattern = re.compile(r'\b(?:FROM|JOIN)\s+([a-zA-Z0-9_.`"]+)', re.IGNORECASE)
    output_pattern = re.compile(r'\b(?:INSERT\s+INTO|CREATE\s+TABLE|MERGE\s+INTO|REPLACE\s+TABLE)\s+([a-zA-Z0-9_.`"]+)', re.IGNORECASE)

    table_data = []

    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()
            relative_path = os.path.relpath(file_path, repo_path)

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                    sql_blocks = [content] if file_ext == ".sql" else extract_sql_blocks(content)
                    found_match = False

                    for sql in sql_blocks:
                        input_tables, output_tables = extract_tables_from_sql(sql, input_pattern, output_pattern)

                        for table in input_tables:
                            table_data.append([relative_path, file_ext, file, table, 'Input'])
                            found_match = True

                        for table in output_tables:
                            table_data.append([relative_path, file_ext, file, table, 'Output'])
                            found_match = True

                    if not found_match:
                        table_data.append([relative_path, file_ext, file, "N/A", "No Matches"])
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['FilePath', 'FileType', 'FileName', 'Table_Name', 'Type of Table'])
        writer.writerows(table_data)

# Example usage
if __name__ == "__main__":
    git_repo_path = Path("/path/to/your/cloned/git/repo")  # Replace this with your actual path
    output_csv = git_repo_path / "table_names.csv"

    if output_csv.exists():
        output_csv.unlink()

    extract_sql_table_info(git_repo_path, output_csv)
    print(f"Extracted table names written to {output_csv}")



























import os
import re

# Detect SQL blocks within files (only .sql, or SQL-looking strings in .py/.txt/.ipynb/.yaml)
SQL_LIKE_EXTENSIONS = ['.sql', '.py', '.ipynb', '.txt', '.yaml', '.yml']

# Patterns to find SQL blocks in Python-like code
SQL_STRING_PATTERN = re.compile(r'(?:cursor\.execute|query\s*=|sql\s*=)\s*[rRuU]?("""|\'\'\'|["\'])(.*?)(\1)', re.DOTALL)

# Input/output table regex patterns
INPUT_PATTERN = re.compile(r'\b(?:FROM|JOIN)\s+([^\s;()]+)', re.IGNORECASE)
OUTPUT_PATTERN = re.compile(r'\b(?:INSERT\s+INTO|CREATE\s+TABLE|MERGE\s+INTO|REPLACE\s+TABLE)\s+([^\s(;]+)', re.IGNORECASE)

def extract_sql_blocks(content):
    sql_blocks = []

    # Look for SQL string assignments (e.g., sql = """ SELECT * FROM ... """)
    for match in SQL_STRING_PATTERN.findall(content):
        sql = match[1]
        if len(sql.split()) > 3 and any(keyword in sql.upper() for keyword in ['SELECT', 'INSERT', 'CREATE', 'MERGE', 'UPDATE']):
            sql_blocks.append(sql)

    # Also include full file content if it's an actual .sql file
    return sql_blocks

def extract_tables_from_sql(sql_text):
    input_tables = set()
    output_tables = set()

    for match in INPUT_PATTERN.findall(sql_text):
        table = match.strip().strip(',').strip('"').strip("'")
        if table:
            input_tables.add(table)

    for match in OUTPUT_PATTERN.findall(sql_text):
        table = match.strip().strip(',').strip('"').strip("'")
        if table:
            output_tables.add(table)

    return input_tables, output_tables

def scan_repo_for_sql_tables(repo_path):
    all_input_tables = set()
    all_output_tables = set()

    for root, _, files in os.walk(repo_path):
        for file in files:
            if any(file.endswith(ext) for ext in SQL_LIKE_EXTENSIONS):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        sql_blocks = extract_sql_blocks(content) if not file.endswith('.sql') else [content]

                        for sql in sql_blocks:
                            input_tables, output_tables = extract_tables_from_sql(sql)
                            all_input_tables.update(input_tables)
                            all_output_tables.update(output_tables)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    continue

    return all_input_tables, all_output_tables

# --------------------
# Main Execution
# --------------------
if __name__ == "__main__":
    repo_path = "."  # or specify the repo path
    inputs, outputs = scan_repo_for_sql_tables(repo_path)

    print("\n=== Input Tables ===")
    for table in sorted(inputs):
        print(f"- {table}")

    print("\n=== Output Tables ===")
    for table in sorted(outputs):
        print(f"- {table}")
