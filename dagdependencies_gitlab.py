import ast
import os

class RecursiveDependencyExtractor(ast.NodeVisitor):
    def __init__(self, file_lookup_map):
        self.file_lookup_map = file_lookup_map
        self.visited = set()
        self.dependencies = set()
        self.imported_files = []
        self.variable_map = {}

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

        self.current_file = file_path
        self.variable_map = {}
        self.visit(tree)

    def visit_Import(self, node):
        for alias in node.names:
            mod_path = self.resolve_module_to_path(alias.name)
            if mod_path:
                self.imported_files.append(mod_path)
                self.parse_and_visit(mod_path)

    def visit_ImportFrom(self, node):
        if node.module:
            mod_path = self.resolve_module_to_path(node.module)
            if mod_path:
                self.imported_files.append(mod_path)
                self.parse_and_visit(mod_path)

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            value = node.value
            if isinstance(value, ast.Str):
                self.variable_map[var_name] = value.s
            elif isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
                if value.func.attr == 'join':
                    joined = self.resolve_os_path_join(value)
                    if joined:
                        self.variable_map[var_name] = joined
            elif isinstance(value, ast.JoinedStr):  # f-strings
                fstring = self.resolve_f_string(value)
                if fstring:
                    self.variable_map[var_name] = fstring
        self.generic_visit(node)

    def visit_Call(self, node):
        for arg in node.args:
            if isinstance(arg, ast.Str):
                if self._is_valid_dependency(arg.s):
                    self.dependencies.add(arg.s)
            elif isinstance(arg, ast.Name):
                var_name = arg.id
                if var_name in self.variable_map:
                    resolved_value = self.variable_map[var_name]
                    if self._is_valid_dependency(resolved_value):
                        self.dependencies.add(resolved_value)
            elif isinstance(arg, ast.JoinedStr):  # direct f-string usage
                fstring = self.resolve_f_string(arg)
                if self._is_valid_dependency(fstring):
                    self.dependencies.add(fstring)
        self.generic_visit(node)

    def resolve_os_path_join(self, call_node):
        if not call_node.args:
            return None
        parts = []
        for arg in call_node.args:
            if isinstance(arg, ast.Str):
                parts.append(arg.s)
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
            if all(part in path for part in module_parts) and path.endswith('.py'):
                return path
        return None

    def get_all_dependencies(self):
        return sorted(list(self.dependencies | self.visited | set(self.imported_files)))

def extract_dependencies_recursive(dag_file_path, all_files_objects):
    file_lookup_map = {
        fobj['full_path']: fobj['content']
        for fobj in all_files_objects
    }

    extractor = RecursiveDependencyExtractor(file_lookup_map)
    extractor.parse_and_visit(dag_file_path)
    return extractor.get_all_dependencies()
