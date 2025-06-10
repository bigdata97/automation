This code will work on two diff files and produce below output:

                                      Table Name               Type
0  CORE_SPECIALTY.COMMON_SPECIALTY.T_SPCLT_PHMCY              Input
1   CORE_SPECIALTY.COMMOM_SPECIALTY.T_SPCLT_PROD              Input
2             AA_SPLTY_PR_SEM.V_SPCLT_PROD_CTGRY              Input
3           <VAR_AA_DB_SEM_SCHEMA>.<VAR_SRC_TBL>   input-unresolved
4         AA_SPLTY_PR_CUR.T_CMN_SPCLT_ORDR_STG_1             Output
5           <VAR_AA_DB_SEM_SCHEMA>.<VAR_TGT_TBL>  output-unresolved
6                                      CTE_PHMCY             Output
7                                       CTE_PROD             Output

drive/notebooks
                                      Table Name    Type
0  CORE_SPECIALTY.COMMON_SPECIALTY.T_SPCLT_PHMCY   Input
1   CORE_SPECIALTY.COMMOM_SPECIALTY.T_SPCLT_PROD   Input
2             AA_SPLTY_PR_SEM.V_SPCLT_PROD_CTGRY   Input
3         AA_SPLTY_PR_CUR.T_CMN_SPCLT_ORDR_STG_1  Output
4                                      CTE_PHMCY  Output
5                                       CTE_PROD  Output

import re
import pandas as pd
import os
print(os.getcwd())

# Show full content in each cell and wider output
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', 0)
pd.set_option('display.max_columns', None)

# with open("test11.py", "r", encoding="utf-8") as f:
with open("test7.sql", "r", encoding="utf-8") as f:    
    content = f.read()


# Check if table name is parameterized
def is_parameterized(table_name):
    return any(sym in table_name for sym in ['<', '>', '#', '{', '}'])
################################################################################################
#CONSOLIDATED UNIFIED REGEXs
input_pattern = re.compile(
    r'\b(?:FROM|JOIN)\s+[`"\']?([a-zA-Z0-9_\-\.<>{}\[\]#"]+)[`"\']?',
    re.IGNORECASE
)

output_pattern = re.compile(
    r'\b(?:INSERT\s+INTO|CREATE\s+TABLE|CREATE\s+OR\s+REPLACE\s+TABLE|'
    r'CREATE\s+OR\s+REPLACE\s+VIEW|MERGE\s+INTO|REPLACE\s+TABLE|'
    r'DROP\s+TABLE(?:\s+IF\s+EXISTS)?)\s+[`"\']?([a-zA-Z0-9_\-\.<>{}\[\]#"]+)[`"\']?',
    re.IGNORECASE
)

################################################################################################
# Extract all table references from SQL
def extract_tables_from_sql(sql_text, input_pattern, output_pattern):
    input_tables = []
    output_tables = []
    cte_names = set()

    # Output: CREATE/INSERT/REPLACE/DROP
    for match in output_pattern.findall(sql_text):
        table = match.strip()
        tag = 'output-unresolved' if is_parameterized(table) else 'Output'
        output_tables.append((table, tag))

    # DELETE/DROP (additional fallback)
    # drop_delete_matches = re.findall(
    #     r'\b(?:DROP\s+TABLE(?:\s+IF\s+EXISTS)?|DELETE\s+FROM)\s+[`"\']?([a-zA-Z0-9_\-\.<>]+)[`"\']?',
    #     sql_text, re.IGNORECASE)
    # for match in drop_delete_matches:
    #     table = match.strip()
    #     tag = 'output-unresolved' if is_parameterized(table) else 'Output'
    #     output_tables.append((table, tag))

# NEWLY ADDED    
    drop_delete_matches = re.findall(
        r'\b(?:DROP\s+TABLE(?:\s+IF\s+EXISTS)?|DELETE\s+FROM)\s+[`"]?([a-zA-Z0-9_\-\.{}]+)[`"]?',
        sql_text, re.IGNORECASE)
    for match in drop_delete_matches:
        table = match.strip()
        tag = 'output-unresolved' if is_parameterized(table) else 'Output'
        output_tables.append((table, tag))

        

    # WITH clause (CTEs and their internal FROMs)
    cte_blocks = re.findall(
        r'(\w+)\s+AS\s*\(\s*SELECT.*?FROM\s+([a-zA-Z0-9_\-\.<>]+)',
        sql_text, re.IGNORECASE | re.DOTALL)
    for cte_name, source_table in cte_blocks:
        cte_name = cte_name.strip()
        source_table = source_table.strip()
        cte_names.add(cte_name)
        tag = 'input-unresolved' if is_parameterized(source_table) else 'Input'
        input_tables.append((source_table, tag))
        output_tables.append((cte_name, 'Output'))

    # General input tables (FROM, JOIN)
    for match in input_pattern.findall(sql_text):
        table = match.strip()
        if table not in cte_names:
            tag = 'input-unresolved' if is_parameterized(table) else 'Input'
            input_tables.append((table, tag))

    return input_tables, output_tables

# Run the extraction
input_tables, output_tables = extract_tables_from_sql(content, input_pattern, output_pattern)

# Combine, deduplicate and format results
seen = set()
table_data = []
for table, tag in input_tables + output_tables:
    if (table, tag) not in seen:
        seen.add((table, tag))
        table_data.append(["test7.sql", ".sql", "test7.sql", table, tag])

if not table_data:
    table_data.append(["test7.sql", ".sql", "test7.sql", "N/A", "No Matches"])

# Display the result
df = pd.DataFrame(table_data, columns=["FilePath", "FileType", "FileName", "Table Name", "Type"])

df = df[["Table Name", "Type"]]
print(df.head(20))
