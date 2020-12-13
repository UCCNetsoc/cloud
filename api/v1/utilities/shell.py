
def escape(arg: str):
    return "'%s'" % (arg.replace(r"'", r"'\''"), )