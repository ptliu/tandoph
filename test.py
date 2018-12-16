d = dict()
d[1] = "x"
d[2] = "y"
print(d)
inv_map = {v: k for k, v in d.items()}
print(inv_map)
