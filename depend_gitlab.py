import ast

def extract_dag_dependencies_precise(target_dag_obj, repo_files_list):
    dag_code = target_dag_obj.FileContent

    # Step 1: Get gm.function() calls from DAG
    class GMCallVisitor(ast.NodeVisitor):
        def __init__(self):
            self.methods = set()

        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "gm":
                    self.methods.add(node.func.attr)
            self.generic_visit(node)

    dag_ast = ast.parse(dag_code)
    call_visitor = GMCallVisitor()
    call_visitor.visit(dag_ast)
    called_methods = call_visitor.methods

    # Step 2: Locate generic_method.py (AirflowGen class)
    generic_file_obj = next((obj for obj in repo_files_list if "class AirflowGen" in obj.FileContent), None)
    if not generic_file_obj:
        raise ValueError("Could not find AirflowGen class in provided files.")

    generic_code = generic_file_obj.FileContent
    generic_ast = ast.parse(generic_code)

    # Step 3: Extract self.variable = 'path' from __init__
    class InitVarExtractor(ast.NodeVisitor):
        def __init__(self):
            self.var_to_path = {}

        def visit_Assign(self, node):
            if (
                isinstance(node.targets[0], ast.Attribute)
                and isinstance(node.targets[0].value, ast.Name)
                and node.targets[0].value.id == "self"
                and isinstance(node.value, ast.Str)
            ):
                self.var_to_path[node.targets[0].attr] = node.value.s
            self.generic_visit(node)

    init_var_mapping = {}
    method_to_var = {}

    for node in generic_ast.body:
        if isinstance(node, ast.ClassDef) and node.name == "AirflowGen":
            for sub_node in node.body:
                if isinstance(sub_node, ast.FunctionDef):
                    if sub_node.name == "__init__":
                        init_extractor = InitVarExtractor()
                        init_extractor.visit(sub_node)
                        init_var_mapping = init_extractor.var_to_path
                    elif sub_node.name in called_methods:
                        # Step 4: Find cmds = ['python', self.xyz, ...]
                        for stmt in sub_node.body:
                            if isinstance(stmt, ast.Assign):
                                if isinstance(stmt.targets[0], ast.Name) and stmt.targets[0].id == "cmds":
                                    if isinstance(stmt.value, ast.List):
                                        elements = stmt.value.elts
                                        for i in range(len(elements) - 1):
                                            if (
                                                isinstance(elements[i], ast.Str)
                                                and elements[i].s == "python"
                                                and isinstance(elements[i+1], ast.Attribute)
                                                and isinstance(elements[i+1].value, ast.Name)
                                                and elements[i+1].value.id == "self"
                                            ):
                                                method_to_var[sub_node.name] = elements[i+1].attr
                                                break

    # Step 5: Map method → variable → script path
    dependencies = []
    for method in called_methods:
        var_name = method_to_var.get(method)
        if var_name and var_name in init_var_mapping:
            dependencies.append(init_var_mapping[var_name])

    # Step 6: Return unique, sorted list
    return sorted(set(dependencies))
