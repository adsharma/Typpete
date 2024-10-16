BUILTINS = {
    "none": ["object"],
    "complex": ["object"],
    "float": ["complex"],
    "int": ["float"],
    "i64": ["int"],
    "i32": ["i64"],
    "i16": ["i32"],
    "i8": ["i16"],
    "u64": ["int"],
    "u32": ["u64"],
    "u16": ["u32"],
    "u8": ["u16"],
    "bool": ["int"],
    "sequence": ["object"],
    "str": ["sequence"],
    "bytes": ["sequence"],
    "tuple": ["sequence"],
    ("list", "list_arg_0"): ["sequence"],
    ("set", "set_arg_0"): ["object"],
    ("dict", "dict_arg_0", "dict_arg_1"): ["object"],
    ("type", "type_arg_0"): ["object"],
}

ALIASES = {"Dict": "dict", "Set": "set", "List": "list", "str": "str"}
