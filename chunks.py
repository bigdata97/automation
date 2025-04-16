import ast
import textwrap

def split_ast_code_blocks(code: str, max_chars: int = 1500):
    """
    Splits a Python file into chunks based on AST nodes,
    ensuring each chunk is <= max_chars and syntactically valid.
    """
    chunks = []
    current_chunk = ""
    current_length = 0

    tree = ast.parse(code)
    for node in tree.body:
        # Extract the exact source code for the node
        block = ast.get_source_segment(code, node)
        if not block:
            continue

        block = textwrap.dedent(block).strip()  # Remove extra indentation
        block_with_space = block + "\n\n"       # Add spacing between blocks

        if current_length + len(block_with_space) > max_chars:
            # Start a new chunk
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = block_with_space
            current_length = len(block_with_space)
        else:
            current_chunk += block_with_space
            current_length += len(block_with_space)

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

chunks = split_ast_code_blocks(code)

for i, chunk in enumerate(chunks, 1):
    chunk_name = f"chunk_{i}"
    print(f"*****************CHUNK_NAME={chunk_name} AND CHUNK_LENGTH={len(chunk)}")
    print(chunk)

print(f"*******************DONE************************")
