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
    input_tables = set()
    output_tables = set()

    # Extract output tables: INSERT INTO, CREATE TABLE, CREATE OR REPLACE TABLE/VIEW
    for match in output_pattern.findall(sql_text):
        table = match.strip().strip(',').strip('"').strip("'")
        if table:
            output_tables.add(table)

    # Extract input tables from top-level and WITH CTE blocks
    # Capture each CTE if present
    with_ctes = re.findall(r'\bWITH\b\s+(.*?)(?=\bSELECT|\Z)', sql_text, re.IGNORECASE | re.DOTALL)
    if with_ctes:
        for cte_block in with_ctes:
            for match in input_pattern.findall(cte_block):
                table = match.strip().strip(',').strip('"').strip("'")
                if table:
                    input_tables.add(table)

    # Now extract inputs from rest of the query
    for match in input_pattern.findall(sql_text):
        table = match.strip().strip(',').strip('"').strip("'")
        if table:
            input_tables.add(table)

    return list(input_tables), list(output_tables)

def extract_sql_table_info(repo_path, output_file):
    # Enhanced patterns
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
                            table_data.append([rel]()_
