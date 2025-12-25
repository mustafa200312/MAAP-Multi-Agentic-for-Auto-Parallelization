"""
C AST Utilities for detecting parallelizable loops using pycparser.
This module provides static analysis for C code to identify for-loops
that can potentially be parallelized using OpenMP.
"""

import re
from pycparser import c_parser, c_ast, c_generator


def preprocess_c_code(source_code: str) -> str:
    """
    Preprocesses C code for pycparser by:
    1. Removing single-line comments (//)
    2. Removing multi-line comments (/* */)
    3. Removing #include directives
    4. Keeping #define and other preprocessor directives as-is
    """
    # Remove single-line comments
    code = re.sub(r'//.*?$', '', source_code, flags=re.MULTILINE)
    
    # Remove multi-line comments
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    
    # Simple macro expansion for object-like macros: #define KEY VALUE
    # This is a heuristic to handle simple constants like SIZE
    macros = {}
    macro_pattern = r'^\s*#define\s+(\w+)\s+(.+?)\s*$'
    for match in re.finditer(macro_pattern, code, flags=re.MULTILINE):
        name, value = match.groups()
        # Avoid function-like macros
        if '(' not in name:
            macros[name] = value.strip()
            
    # Apply macros (descending length order to avoid substring issues)
    # This is very basic and doesn't handle scope or complex things, but helps with simple loops
    for name in sorted(macros.keys(), key=len, reverse=True):
        # Use word boundaries to replace
        code = re.sub(r'\b' + re.escape(name) + r'\b', macros[name], code)

    # Remove #include and other preprocessor directives (pycparser can't handle them)
    # Remove any line starting with #
    code = re.sub(r'^\s*#.*?$', '', code, flags=re.MULTILINE)
    
    return code


class CLoopVisitor(c_ast.NodeVisitor):
    """
    AST Visitor that traverses C code to find for-loops and analyze
    their parallelization potential.
    """
    
    def __init__(self):
        self.loops = []
        self.current_depth = 0
        self.variables_read = set()
        self.variables_written = set()
    
    def visit_For(self, node):
        """Visit a for-loop node and extract parallelization-relevant info."""
        loop_info = {
            "type": "for_loop",
            "start_line": node.coord.line if node.coord else "unknown",
            "is_nested": self.current_depth > 0,
            "depth": self.current_depth,
            "init_var": None,
            "condition": None,
            "increment": None,
            "potential_reductions": [],
            "potential_private_vars": [],
            "potential_shared_vars": [],
        }
        
        # Extract initialization variable
        if node.init:
            loop_info["init_var"] = self._extract_init_var(node.init)
        
        # Extract condition
        if node.cond:
            loop_info["condition"] = self._node_to_string(node.cond)
        
        # Extract increment
        if node.next:
            loop_info["increment"] = self._node_to_string(node.next)
        
        # Analyze loop body for variable usage
        if node.stmt:
            body_analyzer = CLoopBodyAnalyzer()
            body_analyzer.visit(node.stmt)
            loop_info["potential_reductions"] = list(body_analyzer.potential_reductions)
            loop_info["potential_private_vars"] = list(body_analyzer.local_vars)
            loop_info["potential_shared_vars"] = list(body_analyzer.shared_vars)
            loop_info["has_function_calls"] = body_analyzer.has_function_calls
            loop_info["has_array_access"] = body_analyzer.has_array_access
        
        self.loops.append(loop_info)
        
        # Visit nested loops
        self.current_depth += 1
        self.generic_visit(node)
        self.current_depth -= 1
    
    def _extract_init_var(self, init_node):
        """Extract the loop iteration variable from initialization."""
        if isinstance(init_node, c_ast.Assignment):
            if isinstance(init_node.lvalue, c_ast.ID):
                return init_node.lvalue.name
        elif isinstance(init_node, c_ast.DeclList):
            if init_node.decls and len(init_node.decls) > 0:
                return init_node.decls[0].name
        elif isinstance(init_node, c_ast.Decl):
            return init_node.name
        return None
    
    def _node_to_string(self, node):
        """Convert an AST node back to C code string."""
        generator = c_generator.CGenerator()
        try:
            return generator.visit(node)
        except Exception:
            return "complex_expression"


class CLoopBodyAnalyzer(c_ast.NodeVisitor):
    """
    Analyzes the body of a loop to detect:
    - Potential reduction operations (e.g., sum += x)
    - Local/private variables
    - Shared variables
    - Function calls (which may have side effects)
    - Array accesses
    """
    
    def __init__(self):
        self.potential_reductions = set()
        self.local_vars = set()
        self.shared_vars = set()
        self.all_vars_read = set()
        self.all_vars_written = set()
        self.has_function_calls = False
        self.has_array_access = False
    
    def visit_Assignment(self, node):
        """Detect assignments and potential reductions."""
        if isinstance(node.lvalue, c_ast.ID):
            var_name = node.lvalue.name
            self.all_vars_written.add(var_name)
            
            # Check for reduction patterns: var += expr, var -= expr, etc.
            if node.op in ['+=', '-=', '*=', '|=', '&=', '^=']:
                self.potential_reductions.add((var_name, node.op))
            elif node.op == '=' and isinstance(node.rvalue, c_ast.BinaryOp):
                # Check for var = var + expr pattern
                if isinstance(node.rvalue.left, c_ast.ID):
                    if node.rvalue.left.name == var_name:
                        self.potential_reductions.add((var_name, node.rvalue.op))
        
        self.generic_visit(node)
    
    def visit_Decl(self, node):
        """Track local variable declarations."""
        if node.name:
            self.local_vars.add(node.name)
        self.generic_visit(node)
    
    def visit_ID(self, node):
        """Track variable reads."""
        self.all_vars_read.add(node.name)
        # If read but not declared locally, it's potentially shared
        if node.name not in self.local_vars:
            self.shared_vars.add(node.name)
    
    def visit_FuncCall(self, node):
        """Detect function calls which may have side effects."""
        self.has_function_calls = True
        self.generic_visit(node)
    
    def visit_ArrayRef(self, node):
        """Detect array accesses."""
        self.has_array_access = True
        self.generic_visit(node)


def analyze_c_code_ast(source_code: str) -> str:
    """
    Parses C source code and returns a detailed report of potential
    parallelizable loops with OpenMP-relevant information.
    
    Args:
        source_code: The C source code to analyze
        
    Returns:
        A string report describing found loops and parallelization opportunities
    """
    # Preprocess to remove comments and #include directives
    preprocessed_code = preprocess_c_code(source_code)
    
    parser = c_parser.CParser()
    
    try:
        ast = parser.parse(preprocessed_code, filename='<input>')
    except Exception as e:
        return f"C Parsing Error: {e}\n\nNote: pycparser requires preprocessed C code. " \
               f"Please ensure #include directives are resolved or removed for analysis."
    
    visitor = CLoopVisitor()
    visitor.visit(ast)
    
    section_visitor = SectionVisitor()
    section_visitor.visit(ast)
    
    if not visitor.loops and not section_visitor.sections:
        return "No parallelizable loops or sections found."
    
    report = "=== C AST Static Analysis Report ===\n\n"
    
    if visitor.loops:
        report += f"Found {len(visitor.loops)} for-loop(s):\n\n"
    
    for i, loop in enumerate(visitor.loops, 1):
        report += f"--- Loop {i} ---\n"
        report += f"  Line: {loop['start_line']}\n"
        report += f"  Iterator Variable: {loop['init_var'] or 'unknown'}\n"
        report += f"  Condition: {loop['condition'] or 'unknown'}\n"
        report += f"  Increment: {loop['increment'] or 'unknown'}\n"
        report += f"  Nested: {'Yes (depth ' + str(loop['depth']) + ')' if loop['is_nested'] else 'No'}\n"
        
        # Parallelization hints
        report += "\n  Parallelization Analysis:\n"
        
        if loop.get('potential_reductions'):
            report += "    Potential Reductions:\n"
            for var, op in loop['potential_reductions']:
                report += f"      - {var} (operator: {op})\n"
        
        if loop.get('potential_private_vars'):
            report += f"    Potential Private Variables: {', '.join(loop['potential_private_vars'])}\n"
        
        if loop.get('potential_shared_vars'):
            shared = [v for v in loop['potential_shared_vars'] 
                     if v not in (loop['init_var'] or '') 
                     and v not in loop.get('potential_private_vars', [])]
            if shared:
                report += f"    Potential Shared Variables: {', '.join(shared)}\n"
        
        if loop.get('has_function_calls'):
            report += "    WARNING: Contains function calls (check for side effects)\n"
        
        if loop.get('has_array_access'):
            report += "    NOTE: Contains array accesses (verify no data races)\n"
        
        # OpenMP suggestion
        report += "\n  Suggested OpenMP pragma:\n"
        pragma = "    #pragma omp parallel for"
        
        if loop.get('potential_reductions'):
            reductions = [f"reduction({op.replace('=', '')}:{var})" 
                         for var, op in loop['potential_reductions']]
            pragma += " " + " ".join(reductions)
        
        if loop.get('potential_private_vars'):
            pragma += f" private({', '.join(loop['potential_private_vars'])})"
        
        report += pragma + "\n\n"
        
    if section_visitor.sections:
        report += f"Found {len(section_visitor.sections)} potential Parallel Sections:\n\n"
        for i, sec in enumerate(section_visitor.sections, 1):
             report += f"--- Section Group {i} ---\n"
             report += f"  Lines: {sec['start_line']} to {sec['end_line']}\n"
             report += f"  Independent Statements: {sec['count']}\n"
             report += "  Suggested OpenMP pragma:\n"
             report += "    #pragma omp parallel sections\n"
             report += "    {\n"
             report += "        #pragma omp section\n"
             report += "        ...\n"
             report += "    }\n\n"
    
    return report

class VariableUsageVisitor(c_ast.NodeVisitor):
    """
    Analyzes variable usage in a code block/statement.
    """
    def __init__(self):
        self.read = set()
        self.written = set()
        self.func_calls = set()
        
    def visit_Assignment(self, node):
        # LHS is written
        self._analyze_lvalue(node.lvalue)
        # RHS is read
        self.visit(node.rvalue)
        
    def visit_UnaryOp(self, node):
        # Handle ++ and --
        if node.op in ['p++', 'p--', '++p', '--p']:
            self._analyze_lvalue(node.expr)
            self.visit(node.expr) # It is also read
        else:
            self.generic_visit(node)

    def _analyze_lvalue(self, node):
        if isinstance(node, c_ast.ID):
            self.written.add(node.name)
        elif isinstance(node, c_ast.ArrayRef):
            self.visit(node.subscript) # Index is read
            self.visit(node.name) # Array ptr is read 
            # Treat array as written
            if isinstance(node.name, c_ast.ID):
                 self.written.add(node.name.name)
        elif isinstance(node, c_ast.StructRef):
            self.visit(node.name)
            # Struct field write? Treat struct as written for safety
            
    def visit_ID(self, node):
        self.read.add(node.name)
        
    def visit_FuncCall(self, node):
        if isinstance(node.name, c_ast.ID):
            self.func_calls.add(node.name.name)
        if node.args:
            self.visit(node.args)

class SectionVisitor(c_ast.NodeVisitor):
    """
    Finds sequences of independent statements (candidate for OpenMP Sections).
    """
    def __init__(self):
        self.sections = [] # List of {start_line, end_line, statements}
        
    def visit_Compound(self, node):
        # A Compound block (like { ... }) contains a list of statements
        if not node.block_items:
            return

        current_batch = []
        
        for stmt in node.block_items:
            usage = VariableUsageVisitor()
            usage.visit(stmt)
            
            stmt_info = {
                'stmt': stmt,
                'read': usage.read,
                'written': usage.written,
                'calls': usage.func_calls,
                'line': stmt.coord.line if stmt.coord else -1
            }
            current_batch.append(stmt_info)
            
        # Analyze current_batch for independent groups
        # We look for adjacent statements that are independent.
        # Simple heuristic: If S1 and S2 are independent, group them.
        
        i = 0
        while i < len(current_batch) - 1:
            # Try to find a group starting at i
            group = [current_batch[i]]
            combined_read = set(current_batch[i]['read'])
            combined_written = set(current_batch[i]['written'])
            
            j = i + 1
            while j < len(current_batch):
                next_stmt = current_batch[j]
                
                # Check dependency with ALL statements currently in the group
                # Actually, for Sections, we want:
                #    #pragma omp parallel sections
                #    {
                #       #pragma omp section
                #       stmt1;
                #       #pragma omp section
                #       stmt2;
                #    }
                # This requires stmt1 and stmt2 to be independent.
                # If we have stmt1, stmt2, stmt3...
                # We need ANY pair (stmt_a, stmt_b) in different sections to be independent?
                # No, standard OpenMP sections run concurrently. So ALL sections must be independent of EACH OTHER.
                
                # Check if next_stmt is independent of everything in the current group
                is_independent = True
                
                # RAW: Write in Group -> Read in Next
                if not combined_written.isdisjoint(next_stmt['read']):
                    is_independent = False
                # WAR: Read in Group -> Write in Next
                elif not combined_read.isdisjoint(next_stmt['written']):
                    is_independent = False
                # WAW: Write in Group -> Write in Next
                elif not combined_written.isdisjoint(next_stmt['written']):
                    is_independent = False
                    
                if is_independent:
                    group.append(next_stmt)
                    combined_read.update(next_stmt['read'])
                    combined_written.update(next_stmt['written'])
                    j += 1
                else:
                    break
            
            if len(group) > 1:
                # Found a potential parallel section group!
                # Filter trivial statements (like just 'int i;') if needed, but for now keep all.
                # Only keep if they involve some computation (writes or func calls)
                meaningful = [s for s in group if s['written'] or s['calls']]
                if len(meaningful) > 1:
                    self.sections.append({
                        'start_line': group[0]['line'],
                        'end_line': group[-1]['line'],
                        'count': len(group)
                    })
                i = j 
            else:
                i += 1
                
        self.generic_visit(node)
