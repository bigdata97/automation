import os
import re
import csv
from pathlib import Path

def extract_sql_blocks(content):
    # Extract all triple-quoted string blocks assuming they may contain SQL
    sql_blocks = []
    string_sql_blocks = re.findall(
        r"[rRfF]?[\"']{3}([\s\S]+?)[\"']{3}", content, re.DOTALL)
    for block in string_sql_blocks:
        if any(kw in block.upper() for kw in ["SELECT", "INSERT", "CREATE", "MERGE", "UPDATE", "DELETE", "TRUNCATE"]):
            sql_blocks.append(block)
    return sql_blocks

def extract_tables_from_sql(sql, input_pattern, output_pattern):
    input_tables = input_pattern.findall(sql)
    output_tables = output_pattern.findall(sql)
    return input_tables, output_tables

def extract_sql_table_info(repo_path, output_file):
    input_pattern = re.compile(r"(?:FROM|JOIN)\s+[`'\"]?([\w\.]+)[`'\"]?", re.IGNORECASE)
    output_pattern = re.compile(
        r"(?:INTO|OVERWRITE\s+TABLE|INSERT\s+INTO|REPLACE\s+INTO|TABLE|CREATE\s+TABLE|MERGE\s+INTO|UPDATE|DELETE\s+FROM|TRUNCATE\s+TABLE)\s+[`'\"]?([\w\.]+)[`'\"]?",
        re.IGNORECASE
    )

    table_data = []

    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()

            # Optional: Skip unwanted file types
            if file_ext not in [".py", ".sql", ".ipynb"]:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

            sql_blocks = extract_sql_blocks(content)

            for sql in sql_blocks:
                input_tables, output_tables = extract_tables_from_sql(sql, input_pattern, output_pattern)

                for table in input_tables:
                    table_data.append([file_path, file_ext, file, table, "Input"])
                for table in output_tables:
                    table_data.append([file_path, file_ext, file, table, "Output"])

    unique_rows = list({tuple(row) for row in table_data})

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Filepath", "Filetype", "Filename", "TableName", "TypeOfTable"])
        writer.writerows(unique_rows)

    print(f"✅ Extraction complete. Found {len(unique_rows)} table references.")
