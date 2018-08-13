from collections import defaultdict

# Based on https://github.com/ncellar/autumn_v1/

class Nullable(object):
    def __init__(self, children, resolved = False, nullable = False):
        self.resolved = resolved
        self.nullable = nullable
        self.children = children

    def resolve(self, nullabilities): pass

    def resolve_with(self, n):
        self.resolved = True
        self.nullable = n
        self.children = None

class _All(Nullable):
    def resolve(self):
        unresolved = []
        for c in self.children:
            n = c._nullability
            if n.resolved:
                if not n.nullable:
                    # Not nullable if any is not nullable
                    self.resolve_with(False)
                    return
            else: unresolved.append(c)
        if not unresolved:
            # Nullable if all are nullable
            self.resolve_with(True)
        else:
            # Otherwise still unresolved
            self.chilren = unresolved
        

class _Any(Nullable):
    def resolve(self):
        # Inverse of All
        unresolved = []
        for c in self.children:
            n = c._nullability
            if n.resolved:
                if n.nullable:
                    self.resolve_with(True)
                    return
            else: unresolved.append(c)
        if not unresolved:
            self.resolve_with(False)
        else: self.children = unresolved

class _Single(Nullable):
    def resolve(self):
        n = self.children[0]._nullability
        if not n.resolved: return
        self.resolve_with(n.nullable)

Nullable.all = _All     # Nullable if all children are nullable
Nullable.any = _Any     # Nullable if one child is nullable
Nullable.of  = lambda child: _Single([child])  # Nullable if the only child is nullable
Nullable.no  = lambda: Nullable(None, True, False)   # Not nullable
Nullable.yes = lambda: Nullable(None, True, True)    # Nullable

def resolve_nullability(grammar):
    dependants = defaultdict(list)
    rule_dict = {rule.name : rule for rule in grammar.rules}    # Required to resolve rule references
    visited = set()     # To prevent infinite recursion

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
            nullability.resolve()
            if nullability.resolved:
                for dependant in dependants[model]:
                    n = dependant._nullability
                    if not n.resolved:
                        resolve(dependant) # Resolve nodes that depend on this one
            else:
                for n in nullability.children:
                    dependants[n].append(model)

    walk(grammar)

    #for rule in grammar.children_list():
    #    print(rule, "Nullable?", rule.is_nullable)

# This breaks left recursive cycles by tagging
# left recursive rules
def find_left_recursion(grammar):

    # First we need to resolve nullable rules
    resolve_nullability(grammar) 

    visited = set()

    def walk(model):
        if model in visited:
            return
        
       

        visited.add(model)

    walk(grammar)

    return