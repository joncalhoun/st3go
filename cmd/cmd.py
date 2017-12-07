import subprocess

def must(cmd, stdin=None):
    out, err = run(cmd, stdin)
    if err:
        raise err
    return out

def run(cmd, stdin=None):
    p = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    # out, err = p.communicate()
    if stdin:
        out, err = p.communicate(input=stdin.encode())
    else:
        out, err = p.communicate()
    out = out.decode("utf-8")
    if err:
        msg = "Error while running an external command.\nCommand: %s\nError: %s" % (" ".join(cmd), err.decode("utf-8"))
        return out, Error(msg)

    return out, None

class Error(Exception):
    """cmd errors are always of this type"""
    pass
