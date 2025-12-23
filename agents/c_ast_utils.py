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
    
    # Remove #include directives (pycparser can't handle these)
    code = re.sub(r'^\s*#include\s*[<"].*?[>"]\s*$', '', code, flags=re.MULTILINE)
    
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
    
    if not visitor.loops:
        return "No 'for' loops found in the C code by static analysis."
    
    report = "=== C AST Static Analysis Report ===\n\n"
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
    
    return report
