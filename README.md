# Typpete


<p align="left">
  <img src ="https://raw.githubusercontent.com/caterinaurban/Typpete/master/typpete/typpete.png" width="30%"/>
</p>

## **SMT-based Static Type Inference for Python 3.x**


### Installation
Typpete has been tested with Python 3.5+
To install, follow these steps:
- `pip install z3-solver`
- `pip install .`

### Usage
You can run the inference with the following command
```
$ typpete --help
$ typpete [flags] <filename>
```

Example:

```
$ typpete test.py  # writes output to inference_output
$ typpete -l DEBUG test.py  # additional log messages
$ typpete -i test.py  # overwrite source. WARNING: This could lose comments and formatting!
```

```
# test.py
def foo(a):
    i = 200
    a["foo"] = 10
    return i
```

produces:

```
from typing import Dict

def foo(a: Dict[(str, int)]) -> int:
    i: int = 200
    a['foo'] = 10
    return i
```

