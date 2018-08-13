from builtins import object
from collections import defaultdict

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

    def resolve_with(self, n):
        self.resolved = True
        self.nullable = n
        self.children = None

class _All(Nullable):
    def __init__(self, model, children):
        super(_All, self).__init__(model, children)

    def resolve(self, nullabilities):
        unresolved = []
        for n in nullabilities:
            if n.resolved:
                if not n.nullable:
                    # Not nullable if any is not nullable
                    self.resolve_with(False)
                    return
            else: unresolved.append(n.model)
        if not unresolved:
            # Nullable if all are nullable
            self.resolve_with(True)
        else:
            # Otherwise still unresolved
            self.chilren = unresolved
        

class _Any(Nullable):
    def __init__(self, model, children):
        super(_Any, self).__init__(model, children)

    def resolve(self, nullabilities):
        # Inverse of All
        unresolved = []
        for n in nullabilities:
            if n.resolved:
                if n.nullable:
                    self.resolve_with(True)
                    return
            else: unresolved.append(n.model)
        if not unresolved:
            self.resolve_with(False)
        else: self.children = unresolved

class _Single(Nullable):
    def __init__(self, model, child):
        super(_Single, self).__init__(model, [child])

    def resolve(self, nullabilities):
        if not nullabilities[0].resolved: return
        self.resolve_with(nullabilities[0].nullable)

Nullable.all = _All     # Nullable if all children are nullable
Nullable.any = _Any     # Nullable if one child is nullable
Nullable.of  = _Single  # Nullable if the only child is nullable
Nullable.no  = lambda model: Nullable(model, None, True, False)   # Not nullable
Nullable.yes = lambda model: Nullable(model, None, True, True)    # Nullable

def resolve_nullability(grammar):
    dependants = defaultdict(list)
    rule_dict = {rule.name : rule for rule in grammar.rules}
    visited = set()

    def walk(model):    # TODO Write a walker for this
        if model in visited: 
            return

        model._init_nullability(rule_dict)
        
        for child in model.children_list():
            walk(child)

        resolve(model)

        visited.add(model)
    
    def resolve(model):
        nullability = model._nullability
        if not nullability.resolved:
            nullability.resolve([n._nullability for n in nullability.children])
            if nullability.resolved:
                for dependant in dependants[nullability.model]:
                    n = dependant._nullability
                    if not n.resolved:
                        resolve(dependant)
            else:
                for n in nullability.children:
                    dependants[n].append(nullability.model)

    walk(grammar)

    for rule in grammar.children_list():
        print(rule, "Nullable?", rule.is_nullable)

# This breaks left recursive cycles by tagging
# left recursive rules
def find_left_recursion(grammar):
    # First we need to resolve nullable rules
    resolve_nullability(grammar) 
    return