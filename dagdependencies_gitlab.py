import ast
import os

class GeneralDependencyExtractor(ast.NodeVisitor):
    def __init__(self, file_lookup_map):
        self.file_lookup_map = file_lookup_map
        self.visited_files = set()
        self.dependencies = set()
        self.variable_map = {}
        self.generic_class_files = set()  # files where class methods should be traced
        self.class_method_map = {}  # {class_name: set(methods_called)}
        self.class_instances = {}  # {variable_name: class_name}

    def parse_and_visit(self, file_path):
        if file_path in self.visited_files or file_path not in self.file_lookup_map:
            return
        self.visited_files.add(file_path)
        content = self.file_lookup_map[file_path]
        try:
            tree = ast.parse(content)
        except Exception as e:
            print(f"Skipping {file_path} due to parse error: {e}")
            return
        self.current_file = file_path
        self.visit(tree)

    def visit_ImportFrom(self, node):
        self._maybe_mark_generic_module(node.module)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self._maybe_mark_generic_module(alias.name)
        self.generic_visit(node)

    def _maybe_mark_generic_module(self, module_name):
        mod_path = self.resolve_module_to_path(module_name)
        if mod_path:
            self.generic_class_files.add(mod_path)

    def visit_Assign(self, node):
        # Look for gm = generic_method.AirflowGen(...)
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
            class_name = node.value.func.attr
            if isinstance(node.targets[0], ast.Name):
                instance_var = node.targets[0].id
                self.class_instances[instance_var] = class_name
        self.generic_visit(node)

    def visit_Call(self, node):
        for arg in node.args:
            value = self.resolve_node_to_string(arg)
            if value and self._is_valid_dependency(value):
                self.dependencies.add(value)

        if isinstance(node.func, ast.Attribute):
            caller = getattr(node.func.value, 'id', None)
            method = node.func.attr
            class_name = self.class_instances.get(caller)
            if class_name:
                if class_name not in self.class_method_map:
                    self.class_method_map[class_name] = set()
                self.class_method_map[class_name].add(method)
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
        return "".join([
            val.s if isinstance(val, ast.Str) else "{var}"
            for val in node.values
        ])

    def _is_valid_dependency(self, value):
        return any(value.endswith(ext) for ext in ['.sql', '.txt', '.py', '.json', '.yaml', '.yml'])

    def resolve_module_to_path(self, module_name):
        module_parts = module_name.split('.')
        for path in self.file_lookup_map:
            if path.endswith('.py') and all(part in path for part in module_parts):
                return path
        return None

    def trace_class_methods(self):
        for filepath in self.generic_class_files:
            content = self.file_lookup_map.get(filepath)
            if not content:
                continue
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name in self.class_method_map:
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and item.name in self.class_method_map[node.name]:
                                for stmt in item.body:
                                    self.visit(stmt)
            except Exception as e:
                print(f"Failed to parse {filepath} for class methods: {e}")

    def get_all_dependencies(self):
        return sorted(list(self.dependencies | self.visited_files))

def extract_dependencies_recursive(dag_file_path, all_files_objects):
    file_lookup_map = {
        fobj['full_path']: fobj['content']
        for fobj in all_files_objects
    }

    extractor = GeneralDependencyExtractor(file_lookup_map)
    extractor.parse_and_visit(dag_file_path)
    extractor.trace_class_methods()
    return extractor.get_all_dependencies()
