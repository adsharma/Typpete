class Context:
    """Represents types scope in a python program.

    Attributes:
        types_map ({str, Type}): a dict mapping variable names to their inferred types.
    """

    def __init__(self, parent_context=None):
        self.types_map = {}
        self.annotated_functions = {}
        self.parent_context = parent_context

    def get_type(self, var_name):
        """Get the type of `var_name` from this context (or a parent context)"""
        if var_name in self.types_map:
            return self.types_map[var_name]
        if self.parent_context is None:
            raise NameError("Name {} is not defined.".format(var_name))
        return self.parent_context.get_type(var_name)

    def set_type(self, var_name, var_type):
        """Sets the type of a variable in this context."""
        self.types_map[var_name] = var_type

    def delete_type(self, var_name):
        """Delete the variable `var_name` from this context (or a parent context)"""
        if var_name in self.types_map:
            del self.types_map[var_name]
        elif self.parent_context is None:
            raise NameError("Name {} is not defined.".format(var_name))
        else:
            self.parent_context.delete_type(var_name)

    def has_variable(self, var_name):
        """Check if this context (or parent context) has a variable `var_name`"""
        if var_name in self.types_map:
            return True
        if self.parent_context is None:
            return False
        return self.parent_context.has_variable(var_name)

    def has_annotated_func(self, func_name):
        """Check if this context (or parent context) has an annotated function `func_name`"""
        if func_name in self.annotated_functions:
            return True
        if self.parent_context is None:
            return False
        return self.parent_context.has_annotated_func(func_name)

    def get_annotated_func(self, func_name):
        """Get the annotated function `func_name` from this context (or a parent context)"""
        if func_name in self.annotated_functions:
            return self.annotated_functions[func_name]
        if self.parent_context is None:
            raise NameError("Name {} is not defined".format(func_name))
        return self.parent_context.get_annotated_func(func_name)
