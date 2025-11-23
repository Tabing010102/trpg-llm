"""Safe script execution sandbox"""

import ast
import operator
from typing import Dict, Any, Optional


class ScriptSandbox:
    """
    Sandbox for executing custom game scripts safely.
    Uses AST parsing and restricted execution environment.
    """
    
    # Allowed operators
    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.And: operator.and_,
        ast.Or: operator.or_,
        ast.Not: operator.not_,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    # Allowed built-in functions
    ALLOWED_BUILTINS = {
        'abs': abs,
        'min': min,
        'max': max,
        'len': len,
        'int': int,
        'float': float,
        'str': str,
        'bool': bool,
        'list': list,
        'dict': dict,
        'range': range,
        'sum': sum,
    }
    
    def __init__(self):
        self.globals = {
            '__builtins__': self.ALLOWED_BUILTINS,
        }
    
    def execute(
        self,
        script: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Execute a script in the sandbox with given context.
        
        Args:
            script: Python script to execute
            context: Variables available to the script
        
        Returns:
            Result of the script execution
        """
        # Merge context into globals
        execution_globals = self.globals.copy()
        if context:
            execution_globals.update(context)
        
        try:
            # Parse the script
            tree = ast.parse(script, mode='eval')
            
            # Validate the AST
            self._validate_ast(tree)
            
            # Compile and execute
            code = compile(tree, '<sandbox>', 'eval')
            result = eval(code, execution_globals, {})
            
            return result
        except Exception as e:
            raise RuntimeError(f"Script execution failed: {str(e)}")
    
    def _validate_ast(self, node: ast.AST) -> None:
        """
        Validate that the AST only contains allowed operations.
        Raises ValueError if disallowed operations are found.
        """
        for child in ast.walk(node):
            # Check for dangerous operations
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                raise ValueError("Import statements are not allowed")
            
            if isinstance(child, ast.Call):
                # Only allow calls to allowed functions
                if isinstance(child.func, ast.Name):
                    if child.func.id not in self.ALLOWED_BUILTINS:
                        raise ValueError(f"Function '{child.func.id}' is not allowed")
            
            if isinstance(child, (ast.Attribute, ast.Subscript)):
                # Allow attribute access and subscripting
                pass
            
            if isinstance(child, ast.BinOp):
                if type(child.op) not in self.ALLOWED_OPERATORS:
                    raise ValueError(f"Operator {type(child.op).__name__} is not allowed")
            
            if isinstance(child, ast.UnaryOp):
                if type(child.op) not in self.ALLOWED_OPERATORS:
                    raise ValueError(f"Operator {type(child.op).__name__} is not allowed")
    
    def execute_statement(
        self,
        script: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a script as statements (not just expressions).
        Returns the updated context.
        """
        # Merge context into locals
        execution_locals = context.copy() if context else {}
        execution_globals = self.globals.copy()
        
        try:
            # Parse the script
            tree = ast.parse(script, mode='exec')
            
            # Validate the AST
            self._validate_ast(tree)
            
            # Compile and execute
            code = compile(tree, '<sandbox>', 'exec')
            exec(code, execution_globals, execution_locals)
            
            return execution_locals
        except Exception as e:
            raise RuntimeError(f"Script execution failed: {str(e)}")
