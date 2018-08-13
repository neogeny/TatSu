from builtins import object

# Based on https://github.com/ncellar/autumn_v1/

class Nullable(object):
    def __init__(self, model, children, resolved = False, nullable = False):
        self.model = model
        self.resolved = resolved
        self.nullable = nullable
        self.children = children

    def __bool__(self):
        return self.resolved and self.nullable

    def resolve(self, nullabilities): pass
        
class _All(Nullable):
    def __init__(self, model, children):
        super(_All, self).__init__(model, children)

    def resolve(self, nullabilities):
        pass

class _Any(Nullable):
    def __init__(self, model, children):
        super(_Any, self).__init__(model, children)

    def resolve(self, nullabilities):
        pass

class _Single(Nullable):
    def __init__(self, model, child):
        super(_Single, self).__init__(model, [child])

    def resolve(self, nullabilities):
        pass

Nullable.all = _All     # Nullable if all children are nullable
Nullable.any = _Any     # Nullable if one child is nullable
Nullable.of  = _Single  # Nullable if the only child is nullable
Nullable.no  = lambda model: Nullable(model, [], True, False)   # Not nullable
Nullable.yes = lambda model: Nullable(model, [], True, True)    # Nullable

def resolve_nullability(grammar):
    # TODO
    return

# This breaks left recursive cycles by tagging
# left recursive rules
def find_left_recursion(grammar):
    # TODO
    return