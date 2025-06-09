import re

def is_dag_file_by_tuple_strategy(code: str):
    dag_patterns = {
        "legacy": [
            (r'from\s+airflow\.models\s+import\s+DAG', r'\bDAG\s*\('),
            (r'import\s+airflow\.models\s+as\s+(\w+)', None),  # handled specially below
            (r'from\s+airflow\s+import\s+models', r'models\.DAG\s*\('),
        ],
        "modern": [
            (r'from\s+airflow\s+import\s+DAG', r'with\s+DAG\s*\('),
            (r'import\s+airflow(\s+as\s+(\w+))?', None),  # handled specially
        ],
        "taskflow": [
            (r'from\s+airflow\.decorators\s+import\s+dag', r'@dag\s*\('),
        ]
    }

    for style, patterns in dag_patterns.items():
        for import_pattern, dag_pattern in patterns:
            import_match = re.search(import_pattern, code)
            if not import_match:
                continue

            # If this is an alias (e.g., am.DAG), dynamically build dag_pattern
            if dag_pattern is None:
                if style == "legacy" and 'as' in import_pattern:
                    alias = import_match.group(1)
                    dag_pattern = rf'{alias}\.DAG\s*\('
                elif style == "modern" and 'as' in import_pattern:
                    alias = import_match.group(2) or 'airflow'
                    dag_pattern = rf'{alias}\.DAG\s*\('

            if re.search(dag_pattern, code):
                return f"DAG detected: {style} style"

    return "Not a DAG"
