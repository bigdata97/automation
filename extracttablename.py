import os
import re
import csv
from pathlib import Path

def extract_sql_blocks(content):
    sql_blocks = []

    string_sql_blocks = re.findall(r'(?:sql|query)\s*=\s*[rRuU]?(?:"""|\'\'\'|"|\')(.*?)(?:"""|\'\'\'|"|\')', content, re.DOTALL)
    for block in string_sql_blocks:
        if 'SELECT' in block.upper() or 'INSERT' in block.upper() or 'CREATE' in block.upper():
            sql_blocks.append(block)

    return sql_blocks

def is_parameterized(table_name):
    return any(sym in table_name for sym in ['<', '>', '#'])

def extract_tables_from_sql(sql_text, input_pattern, output_pattern):
    input_tables = []
    output_tables = []
    cte_names = set()

    # Output tables from CREATE/INSERT/etc.
    for match in output_pattern.findall(sql_text):
        table = match.strip()
        tag = 'output-unresolved' if is_parameterized(table) else 'Output'
        output_tables.append((table, tag))

    # DROP/DELETE tables
    drop_delete_matches = re.findall(r'\b(?:DROP\s+TABLE(?:\s+IF\s+EXISTS)?|DELETE\s+FROM)\s+([a-zA-Z0-9_.<>\[\]#"]+)', sql_text, re.IGNORECASE)
    for match in drop_delete_matches:
        table = match.strip()
        tag = 'output-unresolved'
        output_tables.append((table, tag))

    # Parameterized CREATE TABLEs
    param_matches = re.findall(r'CREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+([<>\w.#]+)', sql_text, re.IGNORECASE)
    for match in param_matches:
        table = match.strip()
        if is_parameterized(table):
            output_tables.append((table, 'output-unresolved'))

    # CTEs
    cte_blocks = re.findall(r'(\w+)\s+AS\s*\((.*?)\)\s*(?:,|$)', sql_text, re.IGNORECASE | re.DOTALL)
    for cte_name, cte_sql in cte_blocks:
        cte_names.add(cte_name.strip())
        for match in input_pattern.findall(cte_sql):
            table = match.strip()
            tag = 'input-unresolved' if is_parameterized(table) else 'Input'
            input_tables.append((table, tag))

    # General input tables (excluding CTEs)
    for match in input_pattern.findall(sql_text):
        table = match.strip()
        if table not in cte_names:
            tag = 'input-unresolved' if is_parameterized(table) else 'Input'
            input_tables.append((table, tag))

    # CTEs are outputs
    for cte in cte_names:
        output_tables.append((cte, 'Output'))

    return input_tables, output_tables

def extract_sql_table_info(repo_path, output_file):
    input_pattern = re.compile(r'\b(?:FROM|JOIN)\s+([a-zA-Z0-9_.<>\[\]#"]+)', re.IGNORECASE)
    output_pattern = re.compile(
        r'\b(?:INSERT\s+INTO|CREATE\s+TABLE|CREATE\s+OR\s+REPLACE\s+TABLE|CREATE\s+OR\s+REPLACE\s+VIEW|MERGE\s+INTO|REPLACE\s+TABLE)\s+([a-zA-Z0-9_.<>\[\]#"]+)',
        re.IGNORECASE
    )

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

                        for table, tag in input_tables:
                            table_data.append([relative_path, file_ext, file, table, tag])
                            found_match = True

                        for table, tag in output_tables:
                            table_data.append([relative_path, file_ext, file, table, tag])
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
