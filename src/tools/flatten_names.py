import re
def flatten_names(name_set):
    flat_names = []
    for n in name_set:
        if isinstance(n, list):
            flat_names.extend(flatten_names(n)) 
        else:
            flat_names.append(n)
    return flat_names

