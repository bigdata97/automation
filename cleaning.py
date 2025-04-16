import re

# Reuse your existing working clean py code
from tokenize import generate_tokens, INDENT, NEWLINE, COMMENT, STRING
import io

def working_clean_py_code(code: str) -> str:
    output = []
    prev_toktype = INDENT
    last_lineno = -1
    last_col = 0

    tokgen = generate_tokens(io.StringIO(code).readline)

    for tok in tokgen:
        token_type = tok.type
        token_string = tok.string
        start_line, start_col = tok.start

        if start_line > last_lineno:
            last_col = 0
        if start_col > last_col:
            output.append(" " * (start_col - last_col))

        if token_type == COMMENT:
            pass
        elif token_type == STRING:
            if prev_toktype == INDENT:
                pass
            elif prev_toktype == NEWLINE and token_string.startswith(("'''", '"""')):
                pass
            else:
                output.append(token_string)
        else:
            output.append(token_string)

        prev_toktype = token_type
        last_lineno, last_col = tok.end

    raw_cleaned = ''.join(output)
    final_lines = [line.rstrip() for line in raw_cleaned.splitlines() if line.strip()]
    return '\n'.join(final_lines)

def split_and_clean_dag_blocks(full_code: str):
    # Split based on the "==== File: ..." header
    dag_blocks = re.split(r"={5,}\s*\n\s*File:.*?\n\s*={5,}", full_code)

    cleaned_dags = []

    for block in dag_blocks:
        if not block.strip():
            continue

        # Remove any leading file header lines (max 3)
        lines = block.strip().splitlines()
        lines_to_skip = 0
        for i in range(min(3, len(lines))):
            if 'File:' in lines[i] or re.match(r"=+", lines[i]):
                lines_to_skip += 1
        cleaned_block = '\n'.join(lines[lines_to_skip:])

        # Apply your working clean py code
        final_cleaned = working_clean_py_code(cleaned_block)
        cleaned_dags.append(final_cleaned)

    return cleaned_dags
