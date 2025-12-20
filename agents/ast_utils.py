import ast

class LoopVisitor(ast.NodeVisitor):
    def __init__(self):
        self.loops = []

    def visit_For(self, node):
        # We found a loop!
        # Extract loop variable
        if isinstance(node.target, ast.Name):
            target_var = node.target.id
        elif isinstance(node.target, ast.Tuple):
            target_var = ", ".join([elt.id for elt in node.target.elts if isinstance(elt, ast.Name)])
        else:
            target_var = "complex_target"
            
        # Get line range
        start_line = node.lineno
        end_line = getattr(node, 'end_lineno', 'unknown')
        
        self.loops.append({
            "type": "for_loop",
            "target_var": target_var,
            "start_line": start_line,
            "end_line": end_line,
            "is_nested": False # Simplification for now, could track depth
        })
        
        # Continue visiting children to find nested loops
        self.generic_visit(node)

def analyze_code_ast(source_code: str):
    """
    Parses source code and returns a list of potential parallelizable loops.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return f"Syntax Error during AST parsing: {e}"
        
    visitor = LoopVisitor()
    visitor.visit(tree)
    
    if not visitor.loops:
        return "No explicit 'for' loops found by static analysis."
        
    report = "AST Static Analysis found the following loops:\n"
    for loop in visitor.loops:
        report += f"- Loop at line {loop['start_line']} to {loop['end_line']} (iterating over '{loop['target_var']}')\n"
    
    return report
