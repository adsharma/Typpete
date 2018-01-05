BUILTINS = {
    'none': ['object'],
    'complex': ['object'],
    'float': ['complex'],
    'int': ['float'],
    'bool': ['int'],
    'sequence': ['object'],
    'str': ['sequence'],
    'bytes': ['sequence'],
    'tuple': ['sequence'],
    ('list', 'list_type'): ['sequence'],
    ('set', 'set_type'): ['object'],
    ('dict', 'dict_key_type', 'dict_value_type'): ['object'],
    ('type', 'instance'): ['object']
}
