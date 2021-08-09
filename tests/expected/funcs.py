from typing import Dict, List, Set


def f1(a: Dict[str, int]) -> int:
    a["foo"] = 10
    return a["foo"]


def f2(a: Set[str]) -> Set[str]:
    a.add("foo")
    return a


def f3(a: List[str]) -> List[str]:
    a.append("foo")
    return a
