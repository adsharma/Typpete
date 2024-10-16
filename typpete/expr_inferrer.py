"""Inference for python expressions.

Infers the types for the following expressions:
    - BinOp(expr left, operator op, expr right)
    - UnaryOp(unaryop op, expr operand)
    - Dict(expr* keys, expr* values)
    - Set(expr* elts)
    - Num(object n)
    - Str(string s)
    - NameConstant(singleton value)
    - List(expr* elts, expr_context ctx)
    - Tuple(expr* elts, expr_context ctx)
    - Bytes(bytes s)
    - IfExp(expr test, expr body, expr orelse)
    - Subscript(expr value, slice slice, expr_context ctx)
    - Await(expr value) --> Python 3.5+
    - Yield(expr? value)
    - Compare(expr left, cmpop* ops, expr* comparators)
    - Name(identifier id, expr_context ctx)
    - FormattedValue(expr value, int? conversion, expr? format_spec) --> Python 3.6+
    - JoinedStr(expr* values) --> Python 3.6+
    - ListComp(expr elt, comprehension* generators)
    - SetComp(expr elt, comprehension* generators)
    - DictComp(expr key, expr value, comprehension* generators)
    - Attribute(expr value, identifier attr, expr_context ctx)

TODO:
    - Lambda(arguments args, expr body)
    - GeneratorExp(expr elt, comprehension* generators)
    - YieldFrom(expr value)
    - Starred(expr value, expr_context ctx)
"""

import ast
import typpete.z3_axioms as axioms
import sys
import z3

from z3 import Or, And
from typpete.context import Context, AnnotatedFunction


def get_module(node):
    if isinstance(node, ast.Module):
        return node
    if hasattr(node, "_module"):
        return node._module
    if hasattr(node, "_parent"):
        return get_module(node._parent)
    assert False


def infer_numeric(node, solver):
    """Infer the type of a numeric node"""
    if type(node.n) == int:
        return solver.z3_types.int
    if type(node.n) == float:
        return solver.z3_types.float
    if type(node.n) == complex:
        return solver.z3_types.complex


def _get_elements_type(elts, context, lineno, solver):
    """Return the elements type of a collection"""
    elts_type = solver.new_z3_const("elts")
    if len(elts) == 0:
        return elts_type

    all_types = []
    for i in range(0, len(elts)):
        cur_type = infer(elts[i], context, solver)
        all_types.append(cur_type)

        solver.add(
            solver.z3_types.subtype(cur_type, elts_type),
            fail_message="List literal in line {}".format(lineno),
        )

    solver.optimize.add_soft(z3.Or([elts_type == elt for elt in all_types]))
    return elts_type


def infer_list(node, context, solver):
    """Infer the type of a homogeneous list

    Returns: TList(Type t), where t is the type of the list elements
    """
    return solver.z3_types.list(
        _get_elements_type(node.elts, context, node.lineno, solver)
    )


def infer_dict(node, context, solver):
    """Infer the type of a dictionary with homogeneous key set and value set

    Returns: TDictionary(Type k_t, Type v_t), where:
            k_t is the type of dictionary keys
            v_t is the type of dictionary values
    """
    keys_type = _get_elements_type(node.keys, context, node.lineno, solver)
    values_type = _get_elements_type(node.values, context, node.lineno, solver)
    return solver.z3_types.dict(keys_type, values_type)


def infer_tuple(node, context, solver):
    """Infer the type of a tuple

    Returns: TTuple(Type[] t), where t is a list of the tuple's elements types
    """
    tuple_types = ()
    for elem in node.elts:
        elem_type = infer(elem, context, solver)
        tuple_types = tuple_types + (elem_type,)

    # Instantiate the correct z3 tuple type based on length of tuple elements:
    # len(tuple_types) == 1 --> Tuple1(tuple_types)
    # len(tuple_types) == 2 --> Tuple2(tuple_types)
    # .....
    # len(tuple_types) == 5 --> Tuple5(tuple_types)

    if len(tuple_types) == 0:
        return solver.z3_types.tuples[0]

    return solver.z3_types.tuples[len(tuple_types)](tuple_types)


def infer_name_constant(node, solver):
    """Infer the type of name constants like: True, False, None"""
    if isinstance(node.value, bool):
        return solver.z3_types.bool
    elif node.value is None:
        return solver.z3_types.none
    raise NotImplementedError(
        "The inference for {} is not supported.".format(node.value)
    )


def infer_set(node, context, solver):
    """Infer the type of a homogeneous set

    Returns: TSet(Type t), where t is the type of the set elements
    """
    return solver.z3_types.set(
        _get_elements_type(node.elts, context, node.lineno, solver)
    )


def _infer_add(left_type, right_type, lineno, solver):
    """Infer the type of an addition operation, and add the corresponding axioms"""
    result_type = solver.new_z3_const("addition_result")
    solver.add(
        axioms.add(left_type, right_type, result_type, solver.z3_types),
        fail_message="Addition in line {}".format(lineno),
    )

    solver.optimize.add_soft(z3.Or(result_type == left_type, result_type == right_type))
    return result_type


def _infer_mult(left_type, right_type, lineno, solver):
    """Infer the type of a multiplication operation, and add the corresponding axioms"""
    result_type = solver.new_z3_const("multiplication_result")
    solver.add(
        axioms.mult(left_type, right_type, result_type, solver.z3_types),
        fail_message="Multiplication in line {}".format(lineno),
    )
    return result_type


def _infer_div(left_type, right_type, lineno, solver):
    """Infer the type of a division operation, and add the corresponding axioms"""
    result_type = solver.new_z3_const("division_result")
    solver.add(
        axioms.div(left_type, right_type, result_type, solver.z3_types),
        fail_message="Division in line {}".format(lineno),
    )
    return result_type


def _infer_arithmetic(left_type, right_type, op, lineno, solver):
    """Infer the type of an arithmetic operation, and add the corresponding axioms"""
    result_type = solver.new_z3_const("arithmetic_result")

    magic_method = ""
    if isinstance(op, ast.Sub):
        magic_method = "__sub__"
    elif isinstance(op, ast.FloorDiv):
        magic_method = "__floordiv__"
    elif isinstance(op, ast.Mod):
        magic_method = "__mod__"
    elif isinstance(op, ast.LShift):
        magic_method = "__lshift__"
    elif isinstance(op, ast.RShift):
        magic_method = "__rshift__"

    solver.add(
        axioms.arithmetic(
            left_type,
            right_type,
            result_type,
            magic_method,
            isinstance(op, ast.Mod),
            solver.z3_types,
        ),
        fail_message="Arithmetic operation in line {}".format(lineno),
    )
    return result_type


def _infer_bitwise(left_type, right_type, op, lineno, solver):
    """Infer the type of a bitwise operation, and add the corresponding axioms"""
    result_type = solver.new_z3_const("bitwise_result")

    magic_method = ""
    if isinstance(op, ast.BitOr):
        magic_method = "__or__"
    elif isinstance(op, ast.BitXor):
        magic_method = "__xor__"
    elif isinstance(op, ast.BitAnd):
        magic_method = "__and__"

    solver.add(
        axioms.bitwise(
            left_type, right_type, result_type, magic_method, solver.z3_types
        ),
        fail_message="Bitwise operation in line {}".format(lineno),
    )
    return result_type


def binary_operation_type(left_type, op, right_type, lineno, solver):
    """Infer the type of a binary operation result"""
    if isinstance(op, ast.Add):
        inference_func = _infer_add
    elif isinstance(op, ast.Mult):
        inference_func = _infer_mult
    elif isinstance(op, ast.Div):
        inference_func = _infer_div
    elif isinstance(op, (ast.BitOr, ast.BitXor, ast.BitAnd)):
        return _infer_bitwise(left_type, right_type, op, lineno, solver)
    else:
        return _infer_arithmetic(left_type, right_type, op, lineno, solver)

    return inference_func(left_type, right_type, lineno, solver)


def infer_binary_operation(node, context, solver):
    """Infer the type of binary operations

    Handled cases:
        - Sequence multiplication, ex: [1,2,3] * 2 --> [1,2,3,1,2,3]
        - Sequence concatenation, ex: [1,2,3] + [4,5,6] --> [1,2,3,4,5,6]
        - Arithmetic and bitwise operations, ex: (1 + 2) * 7 & (2 | -123) / 3
    """
    left_type = infer(node.left, context, solver)
    right_type = infer(node.right, context, solver)

    return binary_operation_type(left_type, node.op, right_type, node.lineno, solver)


def infer_boolean_operation(node, context, solver):
    """Infer the type of boolean operations

    Ex:
        - 2 and str --> object
        - False or 1 --> int
    """
    values_types = []
    for value in node.values:
        values_types.append(infer(value, context, solver))

    result_type = solver.new_z3_const("boolOp")
    solver.add(
        axioms.bool_op(values_types, result_type, solver.z3_types),
        fail_message="Boolean operation in line {}".format(node.lineno),
    )

    for value in values_types:
        solver.optimize.add_soft(value == result_type)
    return result_type


def infer_unary_operation(node, context, solver):
    """Infer the type for unary operations

    Examples: -5, not 1, ~2
    """
    unary_type = infer(node.operand, context, solver)
    if isinstance(node.op, ast.Not):  # (not expr) always gives bool type
        return solver.z3_types.bool

    if isinstance(node.op, ast.Invert):
        solver.add(
            axioms.unary_invert(unary_type, solver.z3_types),
            fail_message="Invert operation in line {}".format(node.lineno),
        )
        return solver.z3_types.int
    else:
        result_type = solver.new_z3_const("unary_result")
        solver.add(
            axioms.unary_other(unary_type, result_type, solver.z3_types),
            fail_message="Unary operation in line {}".format(node.lineno),
        )
        return result_type


def infer_if_expression(node, context, solver):
    """Infer expressions like: {(a) if (test) else (b)}.

    Return a union type of both (a) and (b) types.
    """
    a_type = infer(node.body, context, solver)
    b_type = infer(node.orelse, context, solver)

    result_type = solver.new_z3_const("if_expr")
    solver.add(
        axioms.if_expr(a_type, b_type, result_type, solver.z3_types),
        fail_message="If expression in line {}".format(node.lineno),
    )
    solver.optimize.add_soft(z3.Or(result_type == a_type, result_type == b_type))
    return result_type


def infer_subscript(node, context, solver):
    """Infer expressions like: x[1], x["a"], x[1:2], x[1:].
    Where x	may be: a list, dict, tuple, str

    Attributes:
        node: the subscript node to be inferred
    """

    indexed_type = infer(node.value, context, solver)

    if isinstance(node.slice, ast.Index):
        index_type = infer(node.slice.value, context, solver)
        result_type = solver.new_z3_const("index")
        hard, soft = axioms.index(
            indexed_type, index_type, result_type, solver.z3_types
        )
        solver.add(hard, fail_message="Indexing in line {}".format(node.lineno))
        solver.optimize.add_soft(soft)
        return result_type
    else:  # Slicing
        # Some slicing may contain 'None' bounds, ex: a[1:], a[::]. Make Int the default type.
        lower_type = upper_type = step_type = solver.z3_types.int
        if node.slice.lower:
            lower_type = infer(node.slice.lower, context, solver)
        if node.slice.upper:
            upper_type = infer(node.slice.upper, context, solver)
        if node.slice.step:
            step_type = infer(node.slice.step, context, solver)

        result_type = solver.new_z3_const("slice")

        solver.add(
            axioms.slicing(
                lower_type,
                upper_type,
                step_type,
                indexed_type,
                result_type,
                solver.z3_types,
            ),
            fail_message="Slicing in line {}".format(node.lineno),
        )
        return result_type


def infer_compare(node, context, solver):
    left_type = infer(node.left, context, solver)
    for i, comparator in enumerate(node.comparators):
        comp_type = infer(comparator, context, solver)
        if isinstance(node.ops[i], (ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
            method_name = None
            if isinstance(node.ops[i], ast.Lt):
                method_name = "__lt__"
            elif isinstance(node.ops[i], ast.Gt):
                method_name = "__gt__"
            elif isinstance(node.ops[i], ast.LtE):
                method_name = "__le__"
            else:
                method_name = "__ge__"
            solver.add(
                axioms.comparison_axioms(
                    left_type, comp_type, method_name, solver.z3_types
                ),
                fail_message="{} comparison in line {}".format(
                    method_name, node.lineno
                ),
            )
            left_type = comp_type

    return solver.z3_types.bool


def infer_name(node, context, solver):
    """Infer the type of a variable

    Attributes:
        node: the variable node whose type is to be inferred
        context: The context to look in for the variable type
    """
    if node.id == "__name__":
        return solver.z3_types.string
    try:
        return context.get_type(node.id)
    except NameError:
        raise NameError(
            "Name {} in line {} is not defined".format(node.id, node.lineno)
        )


def infer_generators(generators, local_context, lineno, solver):
    for gen in generators:
        iter_type = infer(gen.iter, local_context, solver)
        target_type = solver.new_z3_const("generator_target")
        solver.add(
            axioms.generator(iter_type, target_type, solver.z3_types),
            fail_message="Generator in line {}".format(lineno),
        )

        if not isinstance(gen.target, ast.Name):
            if not isinstance(gen.target, (ast.Tuple, ast.List)):
                raise TypeError("The iteration target should be only a variable name.")
            else:
                raise NotImplementedError(
                    "The inference doesn't support lists or tuples as iteration targets yet."
                )
        local_context.set_type(gen.target.id, target_type)


def infer_sequence_comprehension(node, sequence_type, context, solver):
    """Infer the type of a list comprehension

    Attributes:
        node: the comprehension AST node to be inferred
        sequence_type: Either TList or TSet
        context: The current context level

    Examples:
        - [c * 2 for c in [1,2,3]] --> [2,4,6]
        - [c for b in [[1,2],[3,4]] for c in b] --> [1,2,3,4]
        - [(c + 1, c * 2) for c in [1,2,3]] --> [(2,2),(3,4),(4,6)]

    Limitation:
        The iterable should always be a list or a set (not a tuple or a dict)
        The iteration target should be always a variable name.
    """
    local_context = Context(None, [], solver, parent_context=context)
    infer_generators(node.generators, local_context, node.lineno, solver)
    return sequence_type(infer(node.elt, local_context, solver))


def infer_dict_comprehension(node, context, solver):
    """Infer the type of a dictionary comprehension

    Attributes:
        node: the dict comprehension AST node to be inferred
        context: The current context level

    Examples:
        - {a:(2 * a) for a in [1,2,3]} --> {1:2, 2:4, 3:6}
        - {a:len(a) for a in ["a","ab","abc"]}--> {"a":1, "ab":2, "abc":3}

    Limitation:
        The iterable should always be a list or a set (not a tuple or a dict)
        The iteration target should be always a variable name.
    """
    local_context = Context(None, [], solver, parent_context=context)
    infer_generators(node.generators, local_context, node.lineno, solver)
    key_type = infer(node.key, local_context, solver)
    val_type = infer(node.value, local_context, solver)
    return solver.z3_types.dict(key_type, val_type)


def _get_args_types(args, context, instance, solver):
    """Return inferred types for function call arguments"""
    # TODO kwargs

    if instance is not None:
        # The instance represents the method receiver. It is a subtype of the first argument in the method.
        arg_type = solver.new_z3_const("call_arg")
        solver.add(
            solver.z3_types.subtype(instance, arg_type),
            fail_message="Method receiver subtyping in line {}",
        )
        solver.optimize.add_soft(instance == arg_type)
        args_types = (arg_type,)
    else:
        args_types = ()
    for arg in args:
        arg_type = solver.new_z3_const("call_arg")
        call_type = infer(arg, context, solver)

        if not isinstance(call_type, AnnotatedFunction):
            # The call arguments should be subtype of the corresponding function arguments
            solver.add(
                solver.z3_types.subtype(call_type, arg_type),
                fail_message="Call argument subtyping in line {}".format(arg.lineno),
            )
            solver.optimize.add_soft(call_type == arg_type)
        args_types += (arg_type,)
    return args_types


def _infer_annotated_function_call(args_types, solver, annotations, result_type):
    return solver.annotation_resolver.get_annotated_function_axioms(
        args_types, solver, annotations, result_type
    )


def _get_builtin_method_call_axioms(
    args_types, solver, context, result_type, method_name
):
    """Get the axioms of built-in method calls"""
    possible_methods = context.get_matching_methods(method_name)
    method_axioms = []
    for method in possible_methods:
        cur_method_axioms = _infer_annotated_function_call(
            args_types, solver, method, result_type
        )
        if cur_method_axioms is not None:
            method_axioms.append(cur_method_axioms)
    return method_axioms


def infer_func_call(node, context, solver):
    """Infer the type of a function call, and unify the call types with the function parameters"""
    result_type = solver.new_z3_const("call")

    # Check if it's direct class instantiation
    if isinstance(node.func, ast.Name):
        if node.func.id == "cast":
            if len(node.args) != 2:
                raise TypeError(
                    "Casts need two arguments (target type and expression)."
                )
            infer(node.args[1], context, solver)
            return solver.annotation_resolver.resolve(
                node.args[0], solver, get_module(node)
            )
        called = context.get_type(node.func.id)
        # check if the type has the manually added flag for class-types
        if hasattr(called, "is_class"):
            tvs = [
                solver.new_z3_const("ta" + str(i))
                for i in range(solver.z3_types.config.max_type_args)
            ]
            args_types = _get_args_types(node.args, context, None, solver)
            solver.add(
                axioms.one_type_instantiation(
                    node.func.id, args_types, result_type, solver.z3_types, tvs
                ),
                fail_message="Class instantiation {} in line {}.".format(
                    node.func.id, node.lineno
                ),
            )
            return result_type

    # instance represents the receiver in case of method calls.
    # It's none in all cases except method calls
    instance = None
    call_axioms = []
    target_context = context

    if isinstance(node.func, ast.Attribute):
        instance = infer(node.func.value, context, solver)
        if isinstance(instance, Context):
            # Module access; instance is a module, so don't add it as a receiver to `arg_types`
            target_context = instance
            instance = None

    args_types = _get_args_types(node.args, context, instance, solver)

    if isinstance(node.func, ast.Attribute):
        # Add axioms for built-in methods
        call_axioms += _get_builtin_method_call_axioms(
            args_types, solver, target_context, result_type, node.func.attr
        )

        if instance is not None:
            # Add disjunctions for staticmethod calls
            # Remove the first arg (which is the method receiver) from the call args types.
            call_axioms += axioms.staticmethod_call(
                instance, args_types[1:], result_type, node.func.attr, solver.z3_types
            )

            tvs = []
            for i in range(solver.z3_types.config.max_type_args):
                tv = solver.new_z3_const("ta" + str(i))
                tvs.append(tv)

            # Fixes #21: https://github.com/caterinaurban/Typpete/issues/21
            call_axioms += axioms.instancemethod_call(
                instance, args_types, result_type, node.func.attr, solver.z3_types, tvs
            )

            solver.add(
                Or(call_axioms),
                fail_message="Call to {} in line {}".format(
                    node.func.attr, node.lineno
                ),
            )
            return result_type
    called = infer(node.func, context, solver)
    if isinstance(called, AnnotatedFunction):
        func_axioms = solver.annotation_resolver.get_annotated_function_axioms(
            args_types, solver, called, result_type
        )
        if func_axioms is not None:
            call_axioms.append(func_axioms)
    else:
        tvs = []
        for i in range(solver.z3_types.config.max_type_args):
            tv = solver.new_z3_const("ta" + str(i))
            tvs.append(tv)
        call_axioms += axioms.call(
            called, args_types, result_type, solver.z3_types, tvs
        )

    solver.add(Or(call_axioms), fail_message="Call in line {}".format(node.lineno))

    return result_type


def _get_builtin_attr_access_axioms(instance_type, attr, result_type, context, solver):
    """Return axioms for built-in attribute access

    Return disjunctions of equalities with all possible built-in types that have a method matching
    the attribute we are trying to access.

    Example:
        x = [1, 2, 3]
        x.append
    """

    # get the built-in methods matching the attribute
    possible_methods = context.get_matching_methods(attr)

    attr_axioms = []
    for method in possible_methods:
        # The first argument in the method annotation will always be an annotation for the receiver
        # (i.e. the built-in type whose attributes we are trying to access)
        first_arg = method.args_annotations[0]

        # Resolve the annotation into a Z3 type
        resolved_type = solver.annotation_resolver.resolve(first_arg, solver, {})

        # Making result type to be none to prevent it from satisfying user-defined call axioms
        # in function call inference. Because built-ins are not handled with Z3.
        attr_axioms.append(
            And(resolved_type == instance_type, result_type == solver.z3_types.none)
        )

    return attr_axioms


def infer_attribute(node, context, from_call, solver):
    """Infer the type of attribute access

    Cases:
        - Instance attribute access. ex:
            class A:
                def f(self):
                    pass
            A().f()
        - Module access. ex:
            import A
            A.f()
    """
    # Check if it's a module access
    instance = infer(node.value, context, solver)
    if isinstance(instance, Context):
        # module import
        if from_call:
            return instance.get_type(node.attr), None
        else:
            return instance.get_type(node.attr)

    # Check if it's a special attribute access:
    if node.attr == "__dict__":
        return solver.z3_types.dict(solver.z3_types.string, solver.z3_types.object)
    elif node.attr == "__class__":
        return solver.z3_types.type(instance)
    elif node.attr == "__name__":
        return solver.z3_types.string

    result_type = solver.new_z3_const("attribute")

    # get axioms for built-in attribute access. Ex: x.append(sth)
    builtin_axioms = _get_builtin_attr_access_axioms(
        instance, node.attr, result_type, context, solver
    )

    # get axioms for user-defined attribute acces. Ex: A().sth
    user_defined_attribute_axioms = axioms.attribute(
        instance, node.attr, result_type, solver.z3_types
    )

    solver.add(
        Or([user_defined_attribute_axioms] + builtin_axioms),
        fail_message="Attribute access {} in line {}".format(node.attr, node.lineno),
    )

    if from_call:
        return result_type, instance
    return result_type


def _init_lambda_context(node, args, context, solver):
    """Initialize the local function scope, and the arguments types

    # TODO: Reuse the _init_func_context function
    """
    local_context = Context(None, [node.body], solver, parent_context=context)

    args_types = ()
    for arg in args:
        arg_type = solver.new_z3_const("func_arg")
        local_context.set_type(arg.arg, arg_type)
        args_types = args_types + (arg_type,)

    return local_context, args_types


def _infer_lambda(node, context, solver):
    """Infer the type of lambda functions

    Inferred as normal function definition where the body has a single node"""
    local_context, args = _init_lambda_context(node, node.args.args, context, solver)
    return_type = infer(node.body, local_context, solver)

    default_args = 0  # Lambdas cannot have default args
    return solver.z3_types.funcs[len(args)](*((default_args,) + args + (return_type,)))


def infer(node, context, solver, from_call=False):
    """Infer the type of a given AST node"""
    try:
        return context.get_isinstance_type(ast.dump(node, annotate_fields=False))
    except NameError:
        pass

    if isinstance(node, ast.Num):
        return infer_numeric(node, solver)
    elif isinstance(node, ast.Str):
        return solver.z3_types.string
    elif (
        sys.version_info[0] >= 3
        and sys.version_info[1] >= 6
        and (isinstance(node, ast.FormattedValue) or isinstance(node, ast.JoinedStr))
    ):
        # Formatted strings were introduced in Python 3.6
        return solver.z3_types.string
    elif isinstance(node, ast.Bytes):
        return solver.z3_types.bytes
    elif isinstance(node, ast.List):
        return infer_list(node, context, solver)
    elif isinstance(node, ast.Dict):
        return infer_dict(node, context, solver)
    elif isinstance(node, ast.Tuple):
        return infer_tuple(node, context, solver)
    elif isinstance(node, ast.NameConstant):
        return infer_name_constant(node, solver)
    elif isinstance(node, ast.Set):
        return infer_set(node, context, solver)
    elif isinstance(node, ast.BinOp):
        return infer_binary_operation(node, context, solver)
    elif isinstance(node, ast.BoolOp):
        return infer_boolean_operation(node, context, solver)
    elif isinstance(node, ast.UnaryOp):
        return infer_unary_operation(node, context, solver)
    elif isinstance(node, ast.IfExp):
        return infer_if_expression(node, context, solver)
    elif isinstance(node, ast.Subscript):
        return infer_subscript(node, context, solver)
    elif (
        sys.version_info[0] >= 3
        and sys.version_info[1] >= 5
        and isinstance(node, ast.Await)
    ):
        # Await and Async were introduced in Python 3.5
        return infer(node.value, context, solver)
    elif isinstance(node, ast.Yield):
        return infer(node.value, context, solver)
    elif isinstance(node, ast.Compare):
        return infer_compare(node, context, solver)
    elif isinstance(node, ast.Name):
        return infer_name(node, context, solver)
    elif isinstance(node, ast.ListComp):
        return infer_sequence_comprehension(node, solver.z3_types.list, context, solver)
    elif isinstance(node, ast.SetComp):
        return infer_sequence_comprehension(node, solver.z3_types.set, context, solver)
    elif isinstance(node, ast.DictComp):
        return infer_dict_comprehension(node, context, solver)
    elif isinstance(node, ast.Call):
        return infer_func_call(node, context, solver)
    elif isinstance(node, ast.Attribute):
        return infer_attribute(node, context, from_call, solver)
    elif isinstance(node, ast.Lambda):
        return _infer_lambda(node, context, solver)
    raise NotImplementedError(
        "Inference for expression {} is not implemented yet.".format(
            type(node).__name__
        )
    )
