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










import ast
import tokenize
import io

def remove_comments_and_docstrings(source):
    # Step 1: Remove single-line comments and preserve indentation
    io_obj = io.StringIO(source)
    out = []
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0

    for tok in tokenize.generate_tokens(io_obj.readline):
        token_type, token_string, (start_line, start_col), _, _ = tok
        if start_line > last_lineno:
            last_col = 0
        if start_col > last_col:
            out.append(" " * (start_col - last_col))
        if token_type == tokenize.COMMENT:
            pass  # skip
        elif token_type == tokenize.STRING and prev_toktype == tokenize.INDENT:
            pass  # skip likely docstring
        else:
            out.append(token_string)
        prev_toktype = token_type
        last_lineno = start_line
        last_col = start_col + len(token_string)

    code_no_comments = "".join(out)

    # Step 2: Remove top-level/function/class/module docstrings via AST
    class DocstringRemover(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            self.generic_visit(node)
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Str)):
                node.body = node.body[1:]
            return node

        def visit_ClassDef(self, node):
            self.generic_visit(node)
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Str)):
                node.body = node.body[1:]
            return node

        def visit_Module(self, node):
            self.generic_visit(node)
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Str)):
                node.body = node.body[1:]
            return node

    tree = ast.parse(code_no_comments)
    tree = DocstringRemover().visit(tree)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)




