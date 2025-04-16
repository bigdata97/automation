import tokenize
import io

def remove_comments_and_multiline_docstrings(code):
    """
    Removes:
    - Single-line comments
    - Docstrings (only if they appear as the first expression inside functions/classes/modules)
    Preserves:
    - Triple-quoted strings used in actual code
    """
    output = []
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0

    tokgen = tokenize.generate_tokens(io.StringIO(code).readline)

    for tok_type, tok_string, start, end, line in tokgen:
        start_line, start_col = start
        end_line, end_col = end

        if tok_type == tokenize.COMMENT:
            continue
        if tok_type == tokenize.STRING:
            if prev_toktype == tokenize.INDENT:
                continue  # Likely a docstring
        output.append((tok_type, tok_string))
        prev_toktype = tok_type

    return tokenize.untokenize(output)
