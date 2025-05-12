import ast

def extract_dag_dependencies_dynamic(target_dag_obj, repo_files_list):
    dag_code = target_dag_obj.FileContent

    # Step 1: Extract all gm.function_name() calls
    class GMCallVisitor(ast.NodeVisitor):
        def __init__(self):
            self.methods = set()

        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "gm":
                    self.methods.add(node.func.attr)
            self.generic_visit(node)

    dag_tree = ast.parse(dag_code)
    gm_visitor = GMCallVisitor()
    gm_visitor.visit(dag_tree)
    called_methods = gm_visitor.methods

    # Step 2: Find and parse the generic_method.py class (AirflowGen)
    airflowgen_file = next((obj for obj in repo_files_list if "class AirflowGen" in obj.FileContent), None)
    if not airflowgen_file:
        raise ValueError("AirflowGen class not found in any file.")

    airflowgen_code = airflowgen_file.FileContent
    airflowgen_ast = ast.parse(airflowgen_code)

    # Step 3: Extract __init__ variable values: self.var = 'script_path'
    init_var_values = {}

    class InitVarExtractor(ast.NodeVisitor):
        def __init__(self):
            self.mapping = {}

        def visit_Assign(self, node):
            if (len(node.targets) == 1 and isinstance(node.targets[0], ast.Attribute)
                and isinstance(node.targets[0].value, ast.Name)
                and node.targets[0].value.id == "self"
                and isinstance(node.value, ast.Str)):
                self.mapping[node.targets[0].attr] = node.value.s
            self.generic_visit(node)

    # Step 4: Map method -> variable (from gm.method -> uses self.variable internally)
    method_to_variable = {}

    class MethodToVarMapper(ast.NodeVisitor):
        def __init__(self):
            self.mapping = {}

        def visit_FunctionDef(self, node):
            method_name = node.name
            for sub in ast.walk(node):
                if isinstance(sub, ast.Attribute):
                    if isinstance(sub.value, ast.Name) and sub.value.id == "self":
                        self.mapping[method_name] = sub.attr  # method uses this variable
                        break
            self.generic_visit(node)

    for node in airflowgen_ast.body:
        if isinstance(node, ast.ClassDef) and node.name == "AirflowGen":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    init_extractor = InitVarExtractor()
                    init_extractor.visit(item)
                    init_var_values = init_extractor.mapping
                elif isinstance(item, ast.FunctionDef):
                    mapper = MethodToVarMapper()
                    mapper.visit(item)
                    method_to_variable.update(mapper.mapping)

    # Step 5: Build dependency list
    dependencies = []
    for method in called_methods:
        var_used = method_to_variable.get(method)
        if var_used and var_used in init_var_values:
            dependencies.append(init_var_values[var_used])

    return dependencies
