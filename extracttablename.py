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
