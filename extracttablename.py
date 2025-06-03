import os
import re
import csv
from pathlib import Path

def extract_sql_blocks(content):
    sql_blocks = []

    # Look for multiline or inline SQL query definitions
    string_sql_blocks = re.findall(r'(?:sql|query)\\s*=\\s*[rRuU]?(\"\"\"|\\'\\'\\'|[\"\\'])(.*?)(\\1)', content, re.DOTALL)
    for _, block, _ in string_sql_blocks:
        if 'SELECT' in block.upper() or 'INSERT' in block.upper() or 'CREATE' in block.upper():
            sql_blocks.append(block)

    return sql_blocks

def extract_tables_from_sql(sql_text, input_pattern, output_pattern):
    input_tables = set()
    output_tables = set()
    cte_names = set()

    # Extract output tables like CREATE TABLE, INSERT INTO, etc.
    for match in output_pattern.findall(sql_text):
        output_tables.add(match.strip())

    # Correctly extract all CTEs and their SQL blocks
    cte_blocks = re.findall(r'(\\w+)\\s+AS\\s*\\((.*?)\\)\\s*(?:,|$)', sql_text, re.IGNORECASE | re.DOTALL)
    for cte_name, cte_sql in cte_blocks:
        cte_name = cte_name.strip()
        cte_names.add(cte_name)
        for match in input_pattern.findall(cte_sql):
            table = match.strip().strip(',').strip('\"').strip(\"'\")
            if table:
                input_tables.add(table)

    # Exclude CTEs when identifying general input tables
    for match in input_pattern.findall(sql_text):
        table = match.strip().strip(',').strip('\"').strip(\"'\")
        if table and table not in cte_names:
            input_tables.add(table)

    # Include all CTEs as internal output tables
    output_tables.update(cte_names)

    return list(input_tables), list(output_tables)

def extract_sql_table_info(repo_path, output_file):
    input_pattern = re.compile(r'\\b(?:FROM|JOIN)\\s+([a-zA-Z0-9_.`\\"]+)', re.IGNORECASE)
    output_pattern = re.compile(
        r'\\b(?:INSERT\\s+INTO|CREATE\\s+TABLE|CREATE\\s+OR\\s+REPLACE\\s+TABLE|CREATE\\s+OR\\s+REPLACE\\s+VIEW|MERGE\\s+INTO|REPLACE\\s+TABLE)\\s+([a-zA-Z0-9_.`\\"]+)',
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
