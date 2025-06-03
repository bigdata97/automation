import os
import re
import csv
from pathlib import Path

def extract_sql_blocks(content):
    sql_blocks = []

    # Look for multiline or inline SQL query definitions
    string_sql_blocks = re.findall(r'(?:sql|query)\s*=\s*[rRuU]?("""|\'\'\'|["\'])(.*?)(\1)', content, re.DOTALL)
    for _, block, _ in string_sql_blocks:
        if 'SELECT' in block.upper() or 'INSERT' in block.upper() or 'CREATE' in block.upper():
            sql_blocks.append(block)

    return sql_blocks

def extract_tables_from_sql(sql_text, input_pattern, output_pattern):
    input_tables = set()
    output_tables = set()

    # Capture output tables (create, insert, etc.)
    for match in output_pattern.findall(sql_text):
        table = match.strip().strip(',').strip('"').strip("'")
        if table:
            output_tables.add(table)

    # Capture subqueries inside WITH clause
    with_clause_match = re.search(r'\bWITH\b\s+(.*?)(\bSELECT\b|\Z)', sql_text, re.IGNORECASE | re.DOTALL)
    if with_clause_match:
        with_clause_sql = with_clause_match.group(1)
        cte_queries = re.findall(r'AS\s*\((.*?)\)', with_clause_sql, re.IGNORECASE | re.DOTALL)
        for cte_sql in cte_queries:
            for match in input_pattern.findall(cte_sql):
                table = match.strip().strip(',').strip('"').strip("'")
                if table:
                    input_tables.add(table)

    # Capture main query input tables
    for match in input_pattern.findall(sql_text):
        table = match.strip().strip(',').strip('"').strip("'")
        if table:
            input_tables.add(table)

    return list(input_tables), list(output_tables)

def extract_sql_table_info(repo_path, output_file):
    input_pattern = re.compile(r'\b(?:FROM|JOIN)\s+([a-zA-Z0-9_.`"]+)', re.IGNORECASE)
    output_pattern = re.compile(
        r'\b(?:INSERT\s+INTO|CREATE\s+TABLE|CREATE\s+OR\s+REPLACE\s+TABLE|CREATE\s+OR\s+REPLACE\s+VIEW|MERGE\s+INTO|REPLACE\s+TABLE)\s+([a-zA-Z0-9_.`"]+)',
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

# Example usage
if __name__ == "__main__":
    git_repo_path = Path("/path/to/your/cloned/git/repo")  # 🔁 Update this path
    output_csv = git_repo_path / "table_names.csv"

    if output_csv.exists():
        output_csv.unlink()

    extract_sql_table_info(git_repo_path, output_csv)
    print(f"✅ Extracted table names written to: {output_csv}")
