def f1(a):
    a["foo"] = 10
    return a["foo"]

def f2(a):
    a.add("foo")
    return a

def f3(a):
    a.append("foo")
    return a
