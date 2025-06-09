import re
import pandas as pd
import ace_tools as tools

# Load file content
with open("/mnt/data/test11.py", "r", encoding="utf-8") as f:
    content = f.read()

# Improved patterns to capture more scenarios
input_keywords = [
    r"FROM", r"JOIN", r"WITH\s+\w+\s+AS\s*\(", r"DELETE\s+FROM", r"MERGE\s+INTO", r"UPDATE", r"DROP\s+TABLE"
]
output_keywords = [
    r"INTO", r"OVERWRITE\s+TABLE", r"INSERT\s+INTO", r"REPLACE\s+INTO",
    r"TABLE", r"CREATE\s+TABLE", r"DROP\s+TABLE", r"DELETE\s+FROM", r"TRUNCATE\s+TABLE"
]

# Compile regex with grouping for table names after keywords
input_pattern = re.compile(r"(?:%s)\s+[`']?([\w\.\-\{\}]+)[`']?" % "|".join(input_keywords), re.IGNORECASE)
output_pattern = re.compile(r"(?:%s)\s+[`']?([\w\.\-\{\}]+)[`']?" % "|".join(output_keywords), re.IGNORECASE)

def extract_tables(sql: str, input_pat, output_pat):
    input_tables = input_pat.findall(sql)
    output_tables = output_pat.findall(sql)
    return input_tables, output_tables

# Extract
input_tables, output_tables = extract_tables(content, input_pattern, output_pattern)

# Remove any known false positives
filtered_inputs = [t for t in input_tables if t.upper() not in ("FROM",)]
filtered_outputs = [t for t in output_tables if t.upper() not in ("FROM",)]

# Deduplicate
unique_tables = list(set(filtered_inputs + filtered_outputs))
df = pd.DataFrame({
    "Table Name": unique_tables,
    "Type": ["Input" if t in filtered_inputs else "Output" for t in unique_tables]
})

tools.display_dataframe_to_user(name="Improved Extracted Table Names", dataframe=df)
