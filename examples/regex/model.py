# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from tatsu.rendering import Renderer


class Model(Renderer):
    def __init__(self):
        self.n = None

    def set_rule_numbers(self):
        self._set_rule_numbers(0)

    def _set_rule_numbers(self, s):
        self.n = s
        return s + 1

    template = '''\
        S{n} = {exp} ;

        '''


class Regex(Model):
    def __init__(self, exp):
        super(Regex, self).__init__()
        self.exp = exp

    def _set_rule_numbers(self, s):
        s = super(Regex, self)._set_rule_numbers(s)
        return self.exp._set_rule_numbers(s)

    def render_fields(self, fields):
        fields.update(startn=self.exp.n)

    template = '''\
        S{n} = S{startn} $ ;

        {exp}
        '''


class Choice(Model):
    def __init__(self, options):
        super(Choice, self).__init__()
        self.options = options

    def _set_rule_numbers(self, s):
        s = super(Choice, self)._set_rule_numbers(s)
        for opt in self.options:
            s = opt._set_rule_numbers(s)
        return s

    def render_fields(self, fields):
        fields.update(exp=[o.n for o in self.options])

    template = '''\
        S{n} = {exp:: |  :S%s} ;

        {options}

        '''


class Sequence(Model):
    def __init__(self, terms):
        super(Sequence, self).__init__()
        self.terms = terms

    def _set_rule_numbers(self, s):
        s = super(Sequence, self)._set_rule_numbers(s)
        for term in self.terms:
            s = term._set_rule_numbers(s)
        return s

    def render_fields(self, fields):
        fields.update(exp=[t.n for t in self.terms])

    template = '''\
        S{n} = {exp:: :S%s} ;

        {terms}

        '''


class Closure(Model):
    def __init__(self, atom):
        super(Closure, self).__init__()
        self.atom = atom

    def _set_rule_numbers(self, s):
        s = super(Closure, self)._set_rule_numbers(s)
        return self.atom._set_rule_numbers(s)

    def render_fields(self, fields):
        fields.update(atomn=self.atom.n)

    template = '''\
            S{n} = {{ S{atomn} }} ;

            {atom}

            '''


class Literal(Model):
    def __init__(self, exp):
        super(Literal, self).__init__()
        self.exp = exp

    template = '''
            S{n} = ?/{exp}/? ;

            '''


class Empty(Model):
    def __init__(self):
        super(Empty, self).__init__()

    template = '''
            S{n} = () ;

            '''
