a = 1 + 2 / 3
a += 0
b = -a
c = [1.2, 2.0, b]
d = [[1.1, 2.5], c]
e = {(i, i * 2) for j in d for i in j}
f = 2 & 3
g = d[f]
h = (g, 2.0, a)
i, j, (k, (l, m)) = {1: 2.0}, True, ((1, 2), (f, e))
n = a if True else "string"
o = (1 is 2) + 1
p = i[o]
condition = True
q = [3] if condition else ["st"]
r = [2.0] if condition else [1, 2]
s = q + r
t = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
u = 2
v = 8
w = t[u:v:u]
x = w[u]
