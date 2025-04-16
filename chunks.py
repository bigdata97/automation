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


















import ast
import textwrap
import re

def split_by_operator_blocks(code: str, max_chars: int):
    """
    Fallback: Split large DAG block by individual operator blocks.
    """
    chunks = []
    current_chunk = ""
    current_length = 0

    lines = code.splitlines(keepends=True)
    operator_block = []
    inside_operator = False

    def flush_operator_block():
        nonlocal current_chunk, current_length
        block = ''.join(operator_block)
        if current_length + len(block) > max_chars:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = block
            current_length = len(block)
        else:
            current_chunk += block
            current_length += len(block)
        operator_block.clear()

    for line in lines:
        stripped = line.strip()

        # Start of operator/task assignment
        if re.match(r"^\w+\s*=\s*\w*Operator\(", stripped):
            if operator_block:
                flush_operator_block()
            inside_operator = True

        if inside_operator:
            operator_block.append(line)
            if stripped.endswith(")") or stripped.endswith("),"):
                flush_operator_block()
                inside_operator = False
        else:
            if current_length + len(line) > max_chars:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = line
                current_length = len(line)
            else:
                current_chunk += line
                current_length += len(line)

    if operator_block:
        flush_operator_block()

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def split_ast_with_operator_fallback(code: str, max_chars: int = 1200):
    """
    Hybrid splitter:
    - Splits Python code using AST node boundaries.
    - If any AST block (like a DAG) is too large, falls back to splitting by operators.
    """
    chunks = []
    current_chunk = ""
    current_length = 0

    tree = ast.parse(code)
    for node in tree.body:
        block = ast.get_source_segment(code, node)
        if not block:
            continue

        block = textwrap.dedent(block).strip()
        block_with_space = block + "\n\n"

        # Case 1: block is larger than max and needs operator fallback
        if len(block_with_space) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
                current_length = 0

            # Split this long block by operator assignments
            operator_chunks = split_by_operator_blocks(block_with_space, max_chars)
            chunks.extend(operator_chunks)

        # Case 2: fits in current chunk
        elif current_length + len(block_with_space) <= max_chars:
            current_chunk += block_with_space
            current_chunk += "\n\n"
            current_length += len(block_with_space)

        # Case 3: fits in new chunk
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = block_with_space + "\n\n"
            current_length = len(block_with_space)

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


chunks = split_ast_with_operator_fallback(code)

for i, chunk in enumerate(chunks, 1):
    chunk_name = f"chunk_{i}"
    print(f"*****************CHUNK_NAME={chunk_name} AND CHUNK_LENGTH={len(chunk)}")
    print(chunk)

print(f"*******************DONE************************")






