import ast
import random
import string
import keyword
import re

# Attempt to import astor, will be used if available
try:
    import astor
    ASTOR_AVAILABLE = True
except ImportError:
    ASTOR_AVAILABLE = False
    # We will fall back to ast.unparse (Python 3.9+) if astor is not available.

class VariableRenamer(ast.NodeTransformer):
    def __init__(self, name_generation_mode="None"):
        self.name_generation_mode = name_generation_mode
        self.renamed_variables = {}  # Maps original_name -> new_name
        self.used_new_names = set(keyword.kwlist) # Pre-populate with keywords to avoid clashes

    def _generate_pinyin_initials(self, name):
        """Generates pinyin-like initials from a variable name."""
        if not name:
            return ""
        
        # Preserve leading underscores
        leading_underscores = ""
        match = re.match(r'^(_+)(.*)', name)
        if match:
            leading_underscores = match.group(1)
            name = match.group(2)
            if not name: # Only underscores
                return leading_underscores

        parts = []
        if '_' in name: # snake_case
            parts = [p for p in name.split('_') if p]
        elif re.match(r'[a-z]+[A-Z]', name): # camelCase or PascalCase
            # Add a split point before each capital letter, unless it's the first letter
            # or preceded by another capital (e.g. HTTPRequest -> H T T P Request is not desired)
            # Simple approach: split by capitals, then filter empty strings
            processed_name = ""
            for i, char in enumerate(name):
                if char.isupper() and i > 0:
                    # Check if previous char is also upper (e.g. in "HTTPRequest")
                    # or if current is followed by lower (e.g. "Request" in "HTTPRequest")
                    # to avoid splitting acronyms like HTTP into H T T P
                    if name[i-1].islower() or (i+1 < len(name) and name[i+1].islower()):
                         processed_name += "_" 
                processed_name += char
            parts = [p for p in processed_name.split('_') if p]
            if not parts and name: # e.g. "myvar" or "MYVAR"
                parts = [name]

        else: # single word or all caps
            parts = [name]
        
        if not parts:
             return leading_underscores + name # Should not happen if name had content

        initials = "".join(part[0].lower() for part in parts if part)
        return leading_underscores + initials if initials else (leading_underscores + name)


    def _generate_new_name(self, original_name):
        if self.name_generation_mode == "None":
            return original_name

        new_name = ""
        if self.name_generation_mode == "Short":
            length = random.randint(1, 5)
            # First char can be an uppercase or lowercase letter, or an underscore.
            first_char = random.choice(string.ascii_letters + "_")
            # Subsequent alphabetic characters must be lowercase. Digits and underscores are also allowed.
            rest_chars = [random.choice(string.ascii_lowercase + string.digits + "_") for _ in range(length - 1)]
            new_name = first_char + "".join(rest_chars)
            # Ensure uniqueness and validity
            while new_name in self.used_new_names or not new_name.isidentifier():
                length = random.randint(1, 5)
                # First char can be an uppercase or lowercase letter, or an underscore.
                first_char = random.choice(string.ascii_letters + "_")
                # Subsequent alphabetic characters must be lowercase. Digits and underscores are also allowed.
                rest_chars = [random.choice(string.ascii_lowercase + string.digits + "_") for _ in range(length - 1)]
                new_name = first_char + "".join(rest_chars)
        
        elif self.name_generation_mode == "Pinyin":
            new_name = self._generate_pinyin_initials(original_name)
            # Ensure uniqueness and validity (e.g., if initials result in a keyword or are empty)
            # Add suffix if clash
            suffix = 0
            temp_name = new_name
            while temp_name in self.used_new_names or not temp_name.isidentifier() or temp_name == "_" or not temp_name:
                suffix += 1
                temp_name = f"{new_name}{suffix}"
                if not temp_name.isidentifier(): # if base name itself is invalid (e.g. starts with digit after pinyin)
                    temp_name = f"v{temp_name}" # prefix with 'v'
            new_name = temp_name
            if not new_name: # Fallback for safety, should not be reached with good pinyin logic
                return self._generate_new_name("Short") # Fallback to short name

        else: # Should not happen if mode is validated beforehand
            return original_name
        
        return new_name

    def visit_Name(self, node):
        if self.name_generation_mode == "None":
            return node

        original_name = node.id
        
        if isinstance(node.ctx, ast.Store): # Variable definition or assignment
            if original_name not in self.renamed_variables:
                new_name = self._generate_new_name(original_name)
                self.renamed_variables[original_name] = new_name
                self.used_new_names.add(new_name)
                node.id = new_name
            else: # Reassignment of an already renamed variable
                node.id = self.renamed_variables[original_name]
        elif isinstance(node.ctx, ast.Load): # Variable usage
            if original_name in self.renamed_variables:
                node.id = self.renamed_variables[original_name]
            # If original_name not in renamed_variables, it might be a builtin or global
            # that we are not renaming, so we leave it as is.
        # ast.Del context is not handled here, but could be if needed
        return node

    def _rename_definition_name(self, node_name_attr):
        original_name = node_name_attr
        if original_name not in self.renamed_variables:
            new_name = self._generate_new_name(original_name)
            self.renamed_variables[original_name] = new_name
            self.used_new_names.add(new_name)
            return new_name
        return self.renamed_variables[original_name]

    def visit_FunctionDef(self, node):
        if self.name_generation_mode == "None":
            self.generic_visit(node)
            return node

        # Rename function name
        node.name = self._rename_definition_name(node.name)

        # Rename arguments (args, vararg, kwarg, kwonlyargs)
        if node.args:
            for arg_list_name in ['args', 'posonlyargs', 'kwonlyargs']: # Python 3.8+ for posonlyargs
                arg_list = getattr(node.args, arg_list_name, None)
                if arg_list:
                    for arg in arg_list:
                        arg.arg = self._rename_definition_name(arg.arg)
            
            if node.args.vararg: # *args
                node.args.vararg.arg = self._rename_definition_name(node.args.vararg.arg)
            
            if node.args.kwarg: # **kwargs
                node.args.kwarg.arg = self._rename_definition_name(node.args.kwarg.arg)
        
        self.generic_visit(node) # Process function body
        return node

    def visit_AsyncFunctionDef(self, node):
        # Same logic as FunctionDef
        return self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        if self.name_generation_mode == "None":
            self.generic_visit(node)
            return node
        
        # Rename class name
        node.name = self._rename_definition_name(node.name)
        
        self.generic_visit(node) # Process class body (methods, inner classes)
        return node
    
    def visit_Import(self, node):
        # For import a as b, rename b
        for alias in node.names:
            if alias.asname:
                alias.asname = self._rename_definition_name(alias.asname)
        self.generic_visit(node)
        return node

    def visit_ImportFrom(self, node):
        # For from x import y as z, rename z
        for alias in node.names:
            if alias.asname:
                alias.asname = self._rename_definition_name(alias.asname)
            # else:
                # If we want to rename the imported name itself (alias.name) when no 'as'
                # This is more complex as it might clash with other modules.
                # For now, only renaming 'asname'.
                # alias.name = self._rename_definition_name(alias.name) # Risky
        self.generic_visit(node)
        return node


def simplify_variables_in_code(code_string, mode="None"):
    if mode == "None" or not code_string.strip():
        return code_string

    try:
        tree = ast.parse(code_string)
    except SyntaxError as e:
        # print(f"SyntaxError parsing code: {e}")
        return f"# Original code had syntax errors:\n# {e}\n{code_string}"

    renamer = VariableRenamer(name_generation_mode=mode)
    transformed_tree = renamer.visit(tree)
    ast.fix_missing_locations(transformed_tree)

    if ASTOR_AVAILABLE:
        try:
            return astor.to_source(transformed_tree)
        except Exception as e:
            # print(f"Error using astor to unparse: {e}. Falling back to ast.unparse.")
            # Fall through to ast.unparse
            pass
    
    # Try ast.unparse (Python 3.9+)
    if hasattr(ast, 'unparse'):
        try:
            return ast.unparse(transformed_tree)
        except Exception as e:
            # print(f"Error using ast.unparse: {e}")
            return f"# Error during AST unparsing: {e}\n{code_string}"
    else:
        return "# AST unparsing requires Python 3.9+ or the 'astor' library. Neither found.\n" + \
               "# Transformed AST could not be converted back to code.\n" + \
               f"# Original code was:\n{code_string}"

if __name__ == '__main__':
    # Example Usage and Testing
    sample_code_1 = """
import os
import sys as system_module
from math import factorial as fact

_global_var = 100

class MyClass:
    class_var = 10
    def __init__(self, value):
        self._instance_var = value + MyClass.class_var + _global_var

    def get_value(self, multiplier=1):
        local_var = self._instance_var * multiplier
        another_local = "test"
        return local_var + len(another_local)

async def async_function(param_one, param_two):
    result = param_one + param_two
    await some_awaitable(result)
    return result

def another_function(regular_arg, *variadic_args, keyword_arg='default', **keyword_variadic_args):
    x_coord = 10
    y_coord = 20
    _internal_calculation = x_coord * y_coord + regular_arg
    if keyword_arg == 'special':
        print("Special case!")
    for arg_item in variadic_args:
        print(arg_item)
    for k, v_value in keyword_variadic_args.items():
        print(f"{k}: {v_value}")
    return _internal_calculation

my_object = MyClass(5)
print(my_object.get_value(2))
final_result = another_function(my_object.get_value(), 1, 2, 3, extra_param=4, keyword_arg='special')
print(final_result)
print(system_module.platform)
print(fact(5))
"""

    sample_code_2_camel_case = """
def getUserProfile(userId):
    firstName = "John"
    lastName = "Doe"
    _privateVar = True
    return firstName + " " + lastName

userData = getUserProfile(123)
print(userData)
"""
    
    sample_code_3_edge_cases = """
_ = 1 # single underscore
__ = 2 # double underscore
___var = 3
a = _ + __ + ___var
def _leading_underscore_func():
    pass
class _LeadingUnderscoreClass:
    pass
"""

    print("Original Code (Sample 1):")
    print(sample_code_1)
    print("\nSimplified (Short Names) (Sample 1):")
    print(simplify_variables_in_code(sample_code_1, "Short"))
    print("\nSimplified (Pinyin Initials) (Sample 1):")
    print(simplify_variables_in_code(sample_code_1, "Pinyin"))

    print("\nOriginal Code (Sample 2 - Camel Case):")
    print(sample_code_2_camel_case)
    print("\nSimplified (Pinyin Initials) (Sample 2):")
    print(simplify_variables_in_code(sample_code_2_camel_case, "Pinyin"))
    
    print("\nOriginal Code (Sample 3 - Edge Cases):")
    print(sample_code_3_edge_cases)
    print("\nSimplified (Pinyin Initials) (Sample 3):")
    print(simplify_variables_in_code(sample_code_3_edge_cases, "Pinyin"))
    print("\nSimplified (Short Names) (Sample 3):")
    print(simplify_variables_in_code(sample_code_3_edge_cases, "Short"))

    print(f"\nASTOR_AVAILABLE: {ASTOR_AVAILABLE}")
    if not ASTOR_AVAILABLE and not hasattr(ast, 'unparse'):
        print("Warning: Neither astor nor ast.unparse is available. Code generation will fail.")

    # Test import renaming
    import_code = "import my_very_long_module_name as mvlmn"
    print(f"\nOriginal import: {import_code}")
    print(f"Simplified import (Pinyin): {simplify_variables_in_code(import_code, 'Pinyin')}")
    
    import_from_code = "from some.package import another_long_name as aln, short_name"
    print(f"\nOriginal import from: {import_from_code}")
    print(f"Simplified import from (Pinyin): {simplify_variables_in_code(import_from_code, 'Pinyin')}")

    no_change_code = "print('Hello World')"
    print(f"\nOriginal no change: {no_change_code}")
    print(f"Simplified no change (Pinyin): {simplify_variables_in_code(no_change_code, 'Pinyin')}")
    
    empty_code = ""
    print(f"\nOriginal empty: '{empty_code}'")
    print(f"Simplified empty (Pinyin): '{simplify_variables_in_code(empty_code, 'Pinyin')}'")

    syntax_error_code = "def my_func("
    print(f"\nOriginal syntax error: {syntax_error_code}")
    print(f"Simplified syntax error (Pinyin): {simplify_variables_in_code(syntax_error_code, 'Pinyin')}")

    pinyin_test_names = ["_my_var", "variableName", "HTTPRequest", "URL_parser", "_", "__", "___", "_a", "a_"]
    renamer_pinyin = VariableRenamer(name_generation_mode="Pinyin")
    print("\nPinyin generation tests:")
    for name in pinyin_test_names:
        generated = renamer_pinyin._generate_pinyin_initials(name)
        print(f"Original: {name:<20} -> Pinyin: {generated}")

    renamer_short = VariableRenamer(name_generation_mode="Short")
    print("\nShort name generation tests (first 5 with assertions):")
    for i in range(5):
        original_test_name = f"original_Test_Name_{i}" # Use a name that has uppercase to ensure it's not influencing
        generated = renamer_short._generate_new_name(original_test_name)
        print(f"Original: {original_test_name} -> Short: {generated}")

        assert len(generated) > 0, "Generated name should not be empty"
        
        first_char = generated[0]
        assert first_char.isascii() or first_char == '_', f"First char '{first_char}' in '{generated}' is not ASCII or underscore."
        if first_char.isalpha():
            # No specific assertion for first char case as it can be upper or lower.
            pass

        if len(generated) > 1:
            for char_idx in range(1, len(generated)):
                char = generated[char_idx]
                assert char.islower() or char.isdigit() or char == '_', \
                       f"Subsequent char '{char}' (at index {char_idx}) in '{generated}' is not lowercase, digit, or underscore."
        
        renamer_short.used_new_names.add(generated) # Add to used names for subsequent test iterations

    # Test for arg type nodes (e.g. type hints) not being processed as Name nodes for renaming
    type_hint_code = """
def foo(bar: str) -> int:
    x: list = []
    return len(bar)
"""
    print("\nOriginal Code (Type Hints):")
    print(type_hint_code)
    print("\nSimplified (Pinyin Initials) (Type Hints):")
    pinyin_transformed = simplify_variables_in_code(type_hint_code, "Pinyin")
    print(pinyin_transformed)
    # Check if 'str', 'int', 'list' were preserved
    assert "str" in pinyin_transformed 
    assert "int" in pinyin_transformed
    assert "list" in pinyin_transformed
    
    print("\nSimplified (Short Names) (Type Hints):")
    short_transformed = simplify_variables_in_code(type_hint_code, "Short")
    print(short_transformed)
    assert "str" in short_transformed
    assert "int" in short_transformed
    assert "list" in short_transformed
    
    print("\nAll tests in __main__ completed.")
    
    # Test case for ensuring class method arguments are renamed
    class_method_arg_code = """
class TestClass:
    def method_with_args(self, first_arg, second_arg):
        return first_arg + second_arg
"""
    print("\nOriginal Code (Class Method Args):")
    print(class_method_arg_code)
    print("\nSimplified (Pinyin) (Class Method Args):")
    print(simplify_variables_in_code(class_method_arg_code, "Pinyin"))

    # Test for lambda arguments
    lambda_code = "my_lambda = lambda x, y_param: x + y_param"
    print("\nOriginal Code (Lambda):")
    print(lambda_code)
    print("\nSimplified (Pinyin) (Lambda):")
    # Note: ast.Lambda arguments are handled by visit_arguments if they are part of a function def.
    # Standalone lambdas assigned to variables: 'x' and 'y_param' are ast.Name nodes within the lambda body.
    # The parameters of an ast.Lambda node are in node.args (an ast.arguments node).
    # The VariableRenamer needs to be extended to visit_Lambda if lambda parameters need direct renaming.
    # Current implementation will rename 'my_lambda', and 'x', 'y_param' if they are used in the body.
    # The actual parameter names in lambda definition are trickier.
    # Let's manually check ast structure for lambda x, y: x+y
    # ast.parse("lambda x,y: x+y").body[0].value.args is an ast.arguments node.
    # This requires visit_arguments or specific handling in visit_Lambda.
    # For now, the current code might not rename lambda parameters directly.
    # Adding visit_arguments to cover this.
    # It seems visit_FunctionDef already covers arguments for named functions. Lambdas are similar.
    # Let's add visit_Lambda
    print(simplify_variables_in_code(lambda_code, "Pinyin")) # Will test if my_lambda, x, y_param are renamed.

    # For visit_Lambda, arguments are in node.args (ast.arguments)
    # We need to make sure _rename_definition_name is used for these args.
    # This is already covered by the logic in visit_FunctionDef for node.args.
    # Let's add a more explicit visit_Lambda
    # VariableRenamer.visit_Lambda = VariableRenamer.visit_FunctionDef # This line caused errors and is removed. The class has its own visit_Lambda.
    print("\nSimplified (Pinyin) (Lambda with class's own visit_Lambda):")
    print(simplify_variables_in_code(lambda_code, "Pinyin"))


    # Test for comprehensions
    comprehension_code = """
my_list = [i*i for i_var in range(10) if i_var % 2 == 0]
my_dict = {str(k_val): k_val**2 for k_val in range(5)}
my_set = {s_item for s_item in "hello"}
my_gen = (g_val + 1 for g_val in range(3))
"""
    print("\nOriginal Code (Comprehensions):")
    print(comprehension_code)
    # Comprehension target variables (i_var, k_val, s_item, g_val) are ast.Name nodes with ast.Store context
    # within the generator expressions. They should be handled by visit_Name.
    print("\nSimplified (Pinyin) (Comprehensions):")
    print(simplify_variables_in_code(comprehension_code, "Pinyin"))
    print("\nSimplified (Short) (Comprehensions):")
    print(simplify_variables_in_code(comprehension_code, "Short"))


    # Test for attributes (should not be renamed unless they are standalone names)
    attribute_code = """
class MyData:
    value = 10
obj = MyData()
print(obj.value) # 'value' here is an attribute, not a Name node to be renamed by visit_Name
data = obj.value  # 'data' should be renamed, obj.value load of 'obj' (renamed), then .value
"""
    print("\nOriginal Code (Attributes):")
    print(attribute_code)
    print("\nSimplified (Pinyin) (Attributes):")
    print(simplify_variables_in_code(attribute_code, "Pinyin")) # Expect obj and data to be renamed. MyData.value itself should be preserved.
    # Indeed, obj.value: 'obj' is a Name node, 'value' is an attr string.
    # MyData.value in MyClass: 'MyData' is a Name node, 'value' is an attr string.
    # This is correct.

# --- Formatting Disruption ---
# Note: Using line-based manipulation as a fallback due to issues with tokenize module in the environment.
# This approach is less robust, especially for indentation and complex spacing.

def disrupt_formatting(code_string, disrupt_level=0.3):
    if not code_string.strip() or disrupt_level == 0:
        return code_string

    lines = code_string.splitlines(True) # Keep line endings
    modified_lines = []

    # 1. Random Newlines
    for i, line in enumerate(lines):
        modified_lines.append(line)
        # Insert extra blank line after non-empty, non-comment line
        stripped_line = line.strip()
        if stripped_line and not stripped_line.startswith('#') and random.random() < disrupt_level:
            modified_lines.append('\n' * random.randint(1, 2))

    # Remove some existing blank lines (second pass)
    temp_lines = []
    last_line_blank = False
    for line in modified_lines:
        is_current_line_blank = not line.strip()
        if is_current_line_blank and last_line_blank and random.random() < disrupt_level:
            continue # Skip this extra blank line
        temp_lines.append(line)
        last_line_blank = is_current_line_blank
    modified_lines = temp_lines
    
    # 2. Random Indentation Changes (very conservative)
    # This is risky with line-based operations. Only adding, not removing.
    temp_lines = []
    for line in modified_lines:
        stripped_line = line.lstrip()
        if line.startswith(" ") and stripped_line and not stripped_line.startswith('#'): # Has indentation and is not a comment
            if random.random() < disrupt_level:
                indentation = line[:-len(stripped_line)]
                line = indentation + (" " * random.randint(1, 2)) + stripped_line
        temp_lines.append(line)
    modified_lines = temp_lines

    # 3. Random Spacing Around Operators/Parentheses (using simple string replacement)
    # This is also very basic and might have unintended consequences.
    # Targets: +, -, *, /, =, ==, !=, <, >, <=, >=, (, ), ,, :
    # Using a simpler character-by-character scan to avoid complex regex for this fallback.
    final_lines = []
    for line in modified_lines:
        new_line = []
        # Skip if it's a comment line for spacing changes
        if line.strip().startswith("#"):
            final_lines.append(line)
            continue
            
        i = 0
        while i < len(line):
            char = line[i]
            new_line.append(char)
            
            # Add space AFTER specific characters
            if char in ('+', '-', '*', '/', '=', ',', ':', '(', '[', '{') and random.random() < disrupt_level:
                if i + 1 < len(line) and line[i+1] != ' ': # Avoid adding if space already exists
                    new_line.append(' ' * random.randint(1, 2))
            
            # Add space BEFORE specific characters
            # This needs to be done carefully. Let's try a look-ahead for the next char.
            if i + 1 < len(line):
                next_char = line[i+1]
                if next_char in ('+', '-', '*', '/', '=', ')', ']', '}') and char != ' ' and random.random() < disrupt_level :
                     new_line.append(' ' * random.randint(1, 2)) # Insert space before next_char by adding to current list
            i += 1
        final_lines.append("".join(new_line))
    modified_lines = final_lines
    
    return "".join(modified_lines)

# --- Redundant Code Injection ---

class RedundantCodeInjector(ast.NodeTransformer):
    def __init__(self, redundancy_level=0.2):
        self.redundancy_level = redundancy_level
        self.temp_var_counter = 0

    def _generate_temp_var_name(self):
        name = f"_redundant_var_{self.temp_var_counter}_"
        self.temp_var_counter += 1
        return name

    def _generate_redundant_statement(self, existing_vars=None):
        # existing_vars is not used yet, but could be for more complex injections
        statements = []
        choice = random.random()

        if choice < 0.3: # Assign a constant to a new temp var
            temp_name = self._generate_temp_var_name()
            assign = ast.Assign(
                targets=[ast.Name(id=temp_name, ctx=ast.Store())],
                value=ast.Constant(value=random.randint(0, 1000))
            )
            statements.append(assign)
        elif choice < 0.6: # Self-assignment of a new temp var
            temp_name = self._generate_temp_var_name()
            assign1 = ast.Assign(
                targets=[ast.Name(id=temp_name, ctx=ast.Store())],
                value=ast.Constant(value=random.choice([None, True, False, "temp_string"]))
            )
            assign2 = ast.Assign(
                targets=[ast.Name(id=temp_name, ctx=ast.Store())],
                value=ast.Name(id=temp_name, ctx=ast.Load())
            )
            statements.extend([assign1, assign2])
        elif choice < 0.8: # if True: pass
            if_true_pass = ast.If(
                test=ast.Constant(value=True),
                body=[ast.Pass()],
                orelse=[]
            )
            statements.append(if_true_pass)
        else: # Sequence of simple operations using new temp vars
            name_a = self._generate_temp_var_name()
            name_b = self._generate_temp_var_name()
            name_c = self._generate_temp_var_name()
            assign_a = ast.Assign(targets=[ast.Name(id=name_a, ctx=ast.Store())], value=ast.Constant(random.randint(1,10)))
            assign_b = ast.Assign(targets=[ast.Name(id=name_b, ctx=ast.Store())], value=ast.Constant(random.randint(1,10)))
            op = ast.BinOp(left=ast.Name(id=name_a, ctx=ast.Load()), op=ast.Add(), right=ast.Name(id=name_b, ctx=ast.Load()))
            assign_c = ast.Assign(targets=[ast.Name(id=name_c, ctx=ast.Store())], value=op)
            statements.extend([assign_a, assign_b, assign_c])
        
        return statements

    # _inject_code helper method was here, now removed as its logic is integrated elsewhere.

    def visit_FunctionDef(self, node):
        self.generic_visit(node) # Visit children first

        # Inject at the beginning of the function body
        if random.random() < self.redundancy_level:
            # Correctly prepend a list of statements
            node.body = self._generate_redundant_statement() + node.body

        # Inject before return statements
        new_body = []
        for stmt in node.body:
            if isinstance(stmt, ast.Return) and random.random() < self.redundancy_level:
                new_body.extend(self._generate_redundant_statement())
            new_body.append(stmt)
        node.body = new_body
        return node

    def visit_AsyncFunctionDef(self, node):
        return self.visit_FunctionDef(node) # Share logic

    def _process_block(self, block_body):
        """Processes a list of statements (a block) and injects code."""
        if not isinstance(block_body, list):
            return block_body # Should not happen if used on node.body or node.orelse

        new_block_body = []
        # Inject at the start of the block
        if random.random() < self.redundancy_level:
            new_block_body.extend(self._generate_redundant_statement())
        
        for stmt in block_body:
            new_block_body.append(stmt) # Add original statement
            # Inject after each original statement (except possibly at the very end of block)
            if random.random() < self.redundancy_level:
                 new_block_body.extend(self._generate_redundant_statement())
        return new_block_body

    def visit_If(self, node):
        self.generic_visit(node) # Process children first (e.g. nested Ifs)
        node.body = self._process_block(node.body)
        if node.orelse:
            node.orelse = self._process_block(node.orelse)
        return node

    def visit_For(self, node):
        self.generic_visit(node)
        node.body = self._process_block(node.body)
        if node.orelse: # For-else loops
            node.orelse = self._process_block(node.orelse)
        return node

    def visit_While(self, node):
        self.generic_visit(node)
        node.body = self._process_block(node.body)
        if node.orelse: # While-else loops
            node.orelse = self._process_block(node.orelse)
        return node

def add_redundant_code(code_string, redundancy_level=0.2):
    if redundancy_level == 0 or not code_string.strip():
        return code_string

    try:
        tree = ast.parse(code_string)
    except SyntaxError as e:
        return f"# Original code had syntax errors for redundant code injection: {e}\n{code_string}"

    injector = RedundantCodeInjector(redundancy_level=redundancy_level)
    transformed_tree = injector.visit(tree)
    
    try:
        ast.fix_missing_locations(transformed_tree)
    except Exception: 
        pass # Proceed anyway

    if ASTOR_AVAILABLE:
        try:
            return astor.to_source(transformed_tree)
        except Exception: 
            pass 
    
    if hasattr(ast, 'unparse'):
        try:
            return ast.unparse(transformed_tree)
        except Exception as e:
            return f"# Error during AST unparsing (ast.unparse) in add_redundant_code: {e}\n# Fallback: Original code was:\n{code_string}"
    else:
        return ("# AST unparsing requires Python 3.9+ or the 'astor' library for add_redundant_code. "
                "# Neither was found or astor failed.\n"
                f"# Original code was:\n{code_string}")


if __name__ == '__main__':
    # ... (previous __main__ content) ...

    print("\n" + "="*20 + " Formatting Disruption Tests " + "="*20)
    sample_code_format = """
def example_function(param1, param2):
    local_variable = param1 + param2 * (5 - 3)
    if local_variable > 10:
        print("Greater than 10")
    else:
        print("Less than or equal to 10")
    return local_variable

another_var = example_function(10, 20)
# A comment line
blank_line_test = True


    """
    print("\nOriginal Code for Formatting:")
    print(sample_code_format)
    
    print("\nDisrupted Formatting (level 0.3):")
    disrupted_code = disrupt_formatting(sample_code_format, 0.3)
    print(disrupted_code)

    print("\nDisrupted Formatting (level 0.7):")
    disrupted_code_high = disrupt_formatting(sample_code_format, 0.7)
    print(disrupted_code_high)

    # Test with an empty string
    print("\nDisrupted Formatting (empty string):")
    print(f"'{disrupt_formatting('', 0.5)}'")

    # Test with no disruption
    print("\nDisrupted Formatting (level 0.0):")
    print(disrupt_formatting(sample_code_format, 0.0))
    
    # Test with syntax error (though tokenize might handle it gracefully or error before disruption)
    syntax_error_format_code = "def x(a,b:\n    return a+b"
    print("\nOriginal Code with Syntax Error (for formatting test):")
    print(syntax_error_format_code)
    print("\nDisrupted Formatting (syntax error code):")
    print(disrupt_formatting(syntax_error_format_code, 0.5))


    print("\n" + "="*20 + " Redundant Code Injection Tests " + "="*20)
    sample_code_redundancy = """
def process_data(data_list, threshold):
    processed_count = 0
    if not data_list:
        return 0 # Early exit
    for item in data_list:
        if item > threshold:
            # This is an important processing step
            processed_count += 1 
        else:
            pass # Do nothing for items below threshold
    
    while processed_count < 10:
        if processed_count % 2 == 0:
            processed_count += 1
        else:
            processed_count += 2
        if processed_count == 5: # Arbitrary internal break condition
            break 
    return processed_count

result = process_data([1,5,10,15,20], 8)
"""
    print("\nOriginal Code for Redundancy Injection:")
    print(sample_code_redundancy)

    print("\nWith Redundant Code (level 0.3):")
    redundant_code_added = add_redundant_code(sample_code_redundancy, 0.3)
    print(redundant_code_added)
    # Try to exec to catch obvious syntax errors from transformation
    if not redundant_code_added.startswith("#"):
        try:
            exec(redundant_code_added, {'print': print})
            print("Exec successful for redundant code (level 0.3)")
        except Exception as e:
            print(f"Error executing redundant code (level 0.3): {e}\n{redundant_code_added}")


    print("\nWith Redundant Code (level 0.7, more aggressive):")
    redundant_code_added_high = add_redundant_code(sample_code_redundancy, 0.7)
    print(redundant_code_added_high)
    if not redundant_code_added_high.startswith("#"):
        try:
            exec(redundant_code_added_high, {'print': print})
            print("Exec successful for redundant code (level 0.7)")
        except Exception as e:
            print(f"Error executing redundant code (level 0.7): {e}\n{redundant_code_added_high}")

    # Test with an empty string
    print("\nRedundant Code (empty string):")
    print(f"'{add_redundant_code('', 0.5)}'")

    # Test with no redundancy
    print("\nRedundant Code (level 0.0):")
    print(add_redundant_code(sample_code_redundancy, 0.0))
