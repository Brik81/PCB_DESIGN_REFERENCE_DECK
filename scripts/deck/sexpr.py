"""Tiny S-expression reader/writer for KiCad files (stdlib only)."""


class Q(str):
    """A string that must be written quoted."""


def _num(v):
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, int):
        return str(v)
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def atom(v):
    if isinstance(v, Q):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if isinstance(v, (int, float)):
        return _num(v)
    return str(v)


def dumps(x, ind=0):
    if not isinstance(x, list):
        return atom(x)
    if not any(isinstance(c, list) for c in x):
        return "(" + " ".join(atom(c) for c in x) + ")"
    head = []
    i = 0
    while i < len(x) and not isinstance(x[i], list):
        head.append(atom(x[i]))
        i += 1
    pad = "\t" * (ind + 1)
    body = "\n".join(pad + dumps(c, ind + 1) for c in x[i:])
    return "(" + " ".join(head) + "\n" + body + "\n" + "\t" * ind + ")"


def loads(text):
    """Parse one S-expression. Quoted strings become Q, numbers stay str."""
    stack, cur, i, n = [], None, 0, len(text)
    while i < n:
        c = text[i]
        if c == "(":
            new = []
            if cur is not None:
                cur.append(new)
                stack.append(cur)
            cur = new
            i += 1
        elif c == ")":
            if not stack:
                return cur
            cur = stack.pop()
            i += 1
        elif c == '"':
            j, buf = i + 1, []
            while text[j] != '"':
                if text[j] == "\\":
                    j += 1
                    buf.append({"n": "\n"}.get(text[j], text[j]))
                else:
                    buf.append(text[j])
                j += 1
            cur.append(Q("".join(buf)))
            i = j + 1
        elif c.isspace():
            i += 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()"':
                j += 1
            cur.append(text[i:j])
            i = j
    return cur


def find(node, head):
    """All direct children lists whose first element == head."""
    return [c for c in node if isinstance(c, list) and c and c[0] == head]


def first(node, head, default=None):
    r = find(node, head)
    return r[0] if r else default


def walk(node):
    """Yield every list node (depth first)."""
    if isinstance(node, list):
        yield node
        for c in node:
            yield from walk(c)
