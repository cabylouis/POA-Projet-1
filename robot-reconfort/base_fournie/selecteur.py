from typing import List, Tuple

Casier = Tuple[int, int]

def mouv_horizontaux(c: int, c2: int, n: int) -> List[List[str]]:
    a = (c2 - c) % n
    if a == 0:
        return [[]]
    options = []
    if a <= n - a:
        options.append(["E"] * a)
    if n - a <= a:
        options.append(["O"] * (n - a))
    return options