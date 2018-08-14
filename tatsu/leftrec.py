# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

from collections import defaultdict
from tatsu import grammars

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
Nullable.of  = lambda child: _Single([child])       # Nullable if the only child is nullable
Nullable.no  = lambda: Nullable(None, True, False)  # Not nullable
Nullable.yes = lambda: Nullable(None, True, True)   # Nullable

def resolve_nullability(grammar, rule_dict):
    dependants = defaultdict(list)
    visited = set()     # To prevent infinite recursion

    def walk(model):    # TODO Write a walker for this?
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

# This breaks left recursive cycles by tagging
# left recursive rules
def find_left_recursion(grammar):
    rule_dict = {rule.name : rule for rule in grammar.rules} # Required to resolve rule references

    # First we need to resolve nullable rules
    resolve_nullability(grammar, rule_dict)

    # Traversable state
    FIRST   = 0
    CUTOFF  = 1
    VISITED = 2

    state = defaultdict(lambda: FIRST)
    stack_depth = [0] # nonlocal workaround 2.7
    stack_positions = {}
    lr_stack_positions = [-1]

    # Follow RuleRef
    def is_leftrec(model):
        return (isinstance(model, grammars.Rule) and model.is_leftrec or
            isinstance(model, grammars.RuleRef) and is_leftrec(rule_dict[model.name]))
    
    def set_leftrec(model):
        if isinstance(model, grammars.RuleRef):
            return set_leftrec(rule_dict[model.name])
        # It should be a Rule now
        assert isinstance(model, grammars.Rule)
        model.is_leftrec = True

    def children(model):
        if isinstance(model, grammars.RuleRef):
            return children(rule_dict[model.name])
        return model.at_same_pos()

    def walk(model):
        if state[model] == FIRST:
            state[model] = CUTOFF
        else: return

        #beforeNode
        leftrec = is_leftrec(model)
        if leftrec:
            lr_stack_positions.append(stack_depth[0])
        
        stack_positions[model] = stack_depth[0]
        stack_depth[0] += 1

        for child in children(model):
            walk(child)
            # afterEdge
            if state[child] == CUTOFF: # active cycle
                if stack_positions[child] > lr_stack_positions[-1]:
                    set_leftrec(model) # Set parent rule left recursive

        #afterNode
        if leftrec:
            lr_stack_positions.pop()
        
        del stack_positions[model]
        stack_depth[0] -= 1

        state[model] = VISITED

    for rule in grammar.children_list():
        walk(rule)

    print()
    for rule in grammar.children_list():
        print(rule)
        if rule.is_leftrec: print("-> Leftrec")
        if rule.is_nullable: print("-> Nullable")

    return