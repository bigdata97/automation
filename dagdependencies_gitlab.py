import ast
import os

class RecursiveDependencyExtractor(ast.NodeVisitor):
    def __init__(self, file_lookup_map):
        self.file_lookup_map = file_lookup_map
        self.visited = set()
        self.dependencies = set()
        self.variable_map = {}
        self.current_file = None

    def parse_and_visit(self, file_path):
        if file_path in self.visited or file_path not in self.file_lookup_map:
            return
        self.visited.add(file_path)
        content = self.file_lookup_map[file_path]
        try:
            tree = ast.parse(content)
        except Exception as e:
            print(f"Skipping {file_path} due to parse error: {e}")
            return

        self.variable_map = {}
        self.current_file = file_path
        self.visit(tree)

    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_Import(self, node):
        for alias in node.names:
            self.resolve_and_visit_import(alias.name)

    def visit_ImportFrom(self, node):
        if node.module:
            self.resolve_and_visit_import(node.module)

    def resolve_and_visit_import(self, module_name):
        mod_path = self.resolve_module_to_path(module_name)
        if mod_path:
            self.parse_and_visit(mod_path)

    def visit_ClassDef(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_FunctionDef(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            value = self.resolve_node_to_string(node.value)
            if value:
                self.variable_map[var_name] = value
        self.generic_visit(node)

    def visit_Call(self, node):
        for arg in node.args:
            value = self.resolve_node_to_string(arg)
            if value and self._is_valid_dependency(value):
                self.dependencies.add(value)
        self.generic_visit(node)

    def resolve_node_to_string(self, node):
        if isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.JoinedStr):
            return self.resolve_f_string(node)
        elif isinstance(node, ast.Name):
            return self.variable_map.get(node.id)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'join':
                return self.resolve_os_path_join(node)
        return None

    def resolve_os_path_join(self, call_node):
        parts = []
        for arg in call_node.args:
            if isinstance(arg, ast.Str):
                parts.append(arg.s)
            elif isinstance(arg, ast.Name) and arg.id in self.variable_map:
                parts.append(self.variable_map[arg.id])
        return os.path.join(*parts) if parts else None

    def resolve_f_string(self, node):
        if isinstance(node, ast.JoinedStr):
            parts = []
            for value in node.values:
                if isinstance(value, ast.Str):
                    parts.append(value.s)
                elif isinstance(value, ast.FormattedValue):
                    parts.append("{var}")
            return "".join(parts)
        return ""

    def _is_valid_dependency(self, value):
        return any(value.endswith(ext) for ext in ['.sql', '.txt', '.py', '.json', '.yaml', '.yml'])

    def resolve_module_to_path(self, module_name):
        module_parts = module_name.split('.')
        for path in self.file_lookup_map:
            if path.endswith('.py') and all(part in path for part in module_parts):
                return path
        return None

    def get_all_dependencies(self):
        return sorted(list(self.dependencies | self.visited))

def extract_dependencies_recursive(dag_file_path, all_files_objects):
    file_lookup_map = {
        fobj['full_path']: fobj['content']
        for fobj in all_files_objects
    }
    extractor = RecursiveDependencyExtractor(file_lookup_map)
    extractor.parse_and_visit(dag_file_path)
    return extractor.get_all_dependencies()
