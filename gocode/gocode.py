import json
import re
import cmd

def autocomplete(position, source):
    out = cmd.must(
        ["gocode", "-f=json", "autocomplete", str(position)],
        source
    )
    ret = json.loads(out)
    return ret

def parse_func(src):
    """
    parse_func is used to parse a Go function into (name, type) tuples that are easier to use for autocompletion.
    
    Some examples help illustrate it best, so a few are shown below.
    
    Given:
        "func(a int) error"
    parse_func returns:
        ([("a", "int")], [(None, "error")])
    
    Given:
        "func(a, b int, c chan int, d func(e error) error) (int, error)"
    parse_func returns:
        (
            [
                ("a", "int"),
                ("b", "int"),
                ("c", "chan int"),
                ("d", "func(e error) error")
            ], [
                (None, "int"),
                (None, "error")
            ]
        )
    
    Given:
        "func(a int) (num int, den int)"
    parse_func returns:
        (
            [
                ("a", "int")
            ], [
                ("num", "int"),
                ("den", "int")
            ]
        )
    """
    if not src.startswith("func("):
        raise Error("invalid function source: %s" % src)
    
    start = len("func")
    depth = 0
    for i in range(start, len(src)):
        if src[i] == "(":
            depth += 1
        elif src[i] == ")":
            depth -= 1
        if depth == 0:
            return (parse_params(src[start:i+1]), parse_params(src[i+1:].strip()))
    raise Error("invalid function source: %s" % src)


def parse_params(src):
    """
    Parsed a Go parameter or return value list into
        (name, type)
    tuples and returns an array of those.  If the name is not present it will be set to None.
    
    Notes: It is possible to get the following inputs, all of which need to be treated differently:
        error
        (int, error)
        (a, b int, e error)
    
    In the last use case it is possible to have what looks like just a type, but it is really a param name with the type declared in the next section.
    
    It is also possible to get a few types with spaces in them. Most notably, channels and functions, along with any types that can embed other types (slices, maps, funcs, channels).
    
    The approah I am using here is roughly:
    
    1. Look for enclosing parens. If none, return (None, src) because it can't be named.
    
    2. Look at every entry to see if *any* contain a space that is not part of one of the types that can contain a space.
    
    This is done by converting all "chan " into "chan_" to handle the spaces used in channel types, and then functions are handled by ignoring any spaces inside of nested parenthesis. This approach should cover containers (slices, etc) as well.
    
    3. If any entries contain a space then we know we have named variables and we need to treat any single entry between commas as a variable name, not a type.
    
    4. If no entries contian a space then we know we have just types and we will need to return None for the variable names.
    
    Long term the ideal solution here might be to write a parser to ensure correctness, but for now this works (I think!)
    """
    if not src.startswith("("):
        return [(None, src)]
    parts = parse_param_parts(src)
    just_types = True
    for part in parts:
        if is_named(part):
            just_types = False
            break

    ret = []
    if just_types:
        for part in parts:
            ret.append((None, part))
        return ret
    
    names = []
    for part in parts:
        tmp = remove_type_spaces(part)
        name, _, tipe = tmp.strip().partition(" ")
        names.append(name)
        if tipe:
            real_type = part.strip().partition(" ")[2]
            for n in names:
                ret.append((n, real_type))
            names = []
    return ret
            
            
def remove_type_spaces(part):
    """
    Trims whitespace from types that can have it. This will alter types, so the resulting strings shoudln't be used to deduce types. The results are intended to make it easier to parse out param names.
    """
    ret = re.sub(r"func\(.*\)\s+", "func()_", part)
    ret = re.sub(r"chan\s+", "chan_", ret)
    return ret

def is_named(part):
    """
    Given a piece of a param, determine if is a named param for certain. That means given:
        "a int"
    is_named will return true, but given:
        "a"
    We can't be certain this isn't a type, so false will be returned.
    """
    part = remove_type_spaces(part)
    depth = 0
    for char in part:
        if depth == 0 and re.match("\s", char):
            return True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
    return False


def parse_param_parts(src):
    """
    Given an input src or params or returns like this:
        (a, b int, err error)
        
    parse_param_parts will split this into individual components separated by the commas and trimmed of excess whitespace. That is, the above example would return:
        ["a", "b int", "err error"]
    
    Note: This does not add data types or do any parsing of that sort, but it *will* handle function types correctly. eg:
        (a, b int, f func(c, d string) error)
    will return the following three entries:
        ["a", "b int", "f func(c, d string) error"]
    
    This function is intended to be used by the parse_parms function to break some of the work out into a more easily testable piece.
    """
    if not src.startswith("("):
        return [src]
    ret = []
    depth = 0
    lastI = 1
    for i in range(0, len(src)):
        char = src[i]
        # TODO(joncalhoun): Research whether there are more separators that need considered.
        if char in (",", ")") and depth == 1:
            ret.append(src[lastI:i].strip())
            lastI = i + 1
        
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
    return ret

# def parse_params(src):
#     """
#     Assuming we have input like one of the following:
#         (a int)
#         (a, b int, c string, f func(int, int) error)
#     Parse it and return an array of tuples in the format:
#         [(name, type), (name, type)]
#     """
#     if not (src.startswith("(") and src.endswith(")")):
#         raise Error("invalid params: %s" % src)
    
#     ret = []
#     depth = 0
#     lastI = 1
#     names = []
#     for i in range(0, len(src)):
#         char = src[i]
#         if char in (",", ")") and depth == 1:
#             # End of a param - parse it
#             name, _, tipe = src[lastI:i].strip().partition(" ")
#             names.append(name)
#             lastI = i + 1
#             if tipe:
#                 # Go supports (a, b string) so if we get a
#                 # type we may need to backfill types
#                 for n in names:
#                     ret.append((n, tipe))
#                     names = []
#         if char == "(":
#             depth += 1
#         elif char == ")":
#             depth -= 1
#     return ret

# def parse_returns(src):
#     """
#     Assuming we have input like one of the following:
#         error
#         func() error
#         (int, error)
#         (i int, e error)
#         (a, b int, e error)
#         (i int, e error, f func(int, string) error)
#     Parse it into individual pieces and return them. This is NOT the same as
#     the parse params and will not return tuples of (name, type) because this is
#     insanely annoying to do when returns can be:
#         - Types with a space in them (eg `chan int` or `func(a, b string) error`)
#         - Named and unnamed (eg `error` or `(i int, e error)`)
#         - And the list goes on...
#     This could probably eventually be supported, but it isn't useful for now.
#     """
#     if not src.startswith("("):
#         # both named returns and multiple returns req parens
#         return [src]
    
#     depth = 0
#     lastI = 1
#     ret = []
#     for i in range(0, len(src)):
#         char = src[i]
#         if char in (",", ")") and depth == 1:
#             ret.append(src[lastI:i].strip())
#             lastI = i + 1
#         if char == "(":
#             depth += 1
#         elif char == ")":
#             depth -= 1
#     return ret

class Error(Exception):
    """gocode errors are always of this type"""
    pass
