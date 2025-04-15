import ast
import tokenize
import io

MAX_CHARS = 4000  # You can adjust this based on your API limit

def remove_comments_and_docstrings(source):
    """Removes all comments and docstrings but keeps string literals."""
    # Step 1: Remove single-line # comments using tokenize
    io_obj = io.StringIO(source)
    out = []
    prev_toktype = tokenize.INDENT
    for tok in tokenize.generate_tokens(io_obj.readline):
        token_type = tok.type
        token_string = tok.string
        if token_type == tokenize.COMMENT:
            continue  # skip #
        elif token_type == tokenize.STRING:
            if prev_toktype == tokenize.INDENT:
                continue  # likely docstring
        out.append(token_string)
        prev_toktype = token_type

    no_comments = ''.join(out)

    # Step 2: Remove docstrings from AST
    class DocstringRemover(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            self.generic_visit(node)
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
                node.body = node.body[1:]
            return node

        def visit_ClassDef(self, node):
            self.generic_visit(node)
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
                node.body = node.body[1:]
            return node

        def visit_Module(self, node):
            self.generic_visit(node)
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Str):
                node.body = node.body[1:]
            return node

    parsed = ast.parse(no_comments)
    cleaned_ast = DocstringRemover().visit(parsed)
    cleaned_code = ast.unparse(cleaned_ast)

    return cleaned_code

def split_into_chunks(cleaned_code, max_chars=MAX_CHARS):
    """Split the cleaned code into max N character-safe chunks."""
    tokens = list(tokenize.generate_tokens(io.StringIO(cleaned_code).readline))
    chunks, current_tokens = [], []

    for token in tokens:
        test_tokens = current_tokens + [token]
        try:
            test_code = tokenize.untokenize(test_tokens)
        except Exception:
            test_code = ''.join(tok.string for tok in test_tokens)

        if len(test_code) > max_chars:
            try:
                chunk_code = tokenize.untokenize(current_tokens)
            except Exception:
                chunk_code = ''.join(tok.string for tok in current_tokens)
            chunks.append(chunk_code)
            current_tokens = [token]
        else:
            current_tokens.append(token)

    # Add any remaining code
    if current_tokens:
        try:
            chunk_code = tokenize.untokenize(current_tokens)
        except Exception:
            chunk_code = ''.join(tok.string for tok in current_tokens)
        chunks.append(chunk_code)

    return chunks
