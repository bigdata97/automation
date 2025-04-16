

import tokenize
import io

def remove_comments_and_docstrings(code):
    """
    Removes:
    - Single-line comments
    - Top-level and nested docstrings ('''...''' or """...""")
    Preserves:
    - Indentation
    - String literals used in assignments, expressions, etc.
    """
    output = []
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0

    tokgen = tokenize.generate_tokens(io.StringIO(code).readline)

    for tok in tokgen:
        token_type = tok.type
        token_string = tok.string
        start_line, start_col = tok.start

        # Maintain indentation/newlines
        if start_line > last_lineno:
            last_col = 0
        if start_col > last_col:
            output.append((" " * (start_col - last_col)))

        if token_type == tokenize.COMMENT:
            # Skip single-line comments
            pass
        elif token_type == tokenize.STRING:
            if prev_toktype == tokenize.INDENT:
                # Skip likely docstrings
                pass
            elif prev_toktype == tokenize.NEWLINE:
                # Top-level triple-quoted strings used as block comments
                if token_string.startswith(("'''", '"""')):
                    pass
                else:
                    output.append(token_string)
            else:
                output.append(token_string)
        else:
            output.append(token_string)

        prev_toktype = token_type
        last_lineno, last_col = tok.end

    return ''.join(output)

