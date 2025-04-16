import re
import tokenize
import io

def clean_and_split_multi_dag_file(full_code: str):
    """
    - Splits a large Python file into multiple DAG sections based on header markers
    - Removes comment blocks, docstrings, empty lines, and trailing spaces
    - Returns a list of cleaned code blocks (one per DAG) with proper indentation
    """

    def working_clean_py_code(code: str) -> str:
        output_tokens = []
        prev_toktype = tokenize.INDENT
        last_lineno = -1
        last_col = 0

        tokgen = tokenize.generate_tokens(io.StringIO(code).readline)

        for tok in tokgen:
            token_type = tok.type
            token_string = tok.string
            start_line, start_col = tok.start

            if token_type == tokenize.COMMENT:
                continue  # Remove single-line comments
            elif token_type == tokenize.STRING:
                if prev_toktype == tokenize.INDENT:
                    continue  # Likely a docstring
                elif prev_toktype == tokenize.NEWLINE and token_string.startswith(("'''", '\"\"\"')):
                    continue  # Likely a block comment
            output_tokens.append(tok)
            prev_toktype = token_type
            last_lineno, last_col = tok.end

        # Reconstruct cleaned code with original spacing
        cleaned_code = tokenize.untokenize(output_tokens)

        # Remove empty lines and trim trailing spaces
        cleaned_lines = [
            line.rstrip() for line in cleaned_code.splitlines() if line.strip()
        ]
        return '\n'.join(cleaned_lines)

    # Step 1: Split the file based on section headers
    dag_blocks = re.split(r"={5,}\s*\n\s*File:.*?\n\s*={5,}", full_code)

    cleaned_dags = []

    for block in dag_blocks:
        if not block.strip():
            continue

        # Remove up to 3 lines of potential section headers
        lines = block.strip().splitlines()
        lines_to_skip = 0
        for i in range(min(3, len(lines))):
            if 'File:' in lines[i] or re.match(r"=+", lines[i]):
                lines_to_skip += 1
        cleaned_block = '\n'.join(lines[lines_to_skip:])

        # Clean the DAG code block and preserve indentation
        final_cleaned = working_clean_py_code(cleaned_block)
        cleaned_dags.append(final_cleaned)

    return cleaned_dags
