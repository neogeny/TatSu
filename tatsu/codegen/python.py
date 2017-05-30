# -*- coding: utf-8 -*-
"""
Python code generation for models defined with tatsu.model
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from tatsu.util import (
    indent,
    safe_name,
    trim,
    timestamp,
    urepr,
    ustr,
    compress_seq
)
from tatsu.exceptions import CodegenError
from tatsu.objectmodel import Node
from tatsu.objectmodel import BASE_CLASS_TOKEN
from tatsu.codegen.cgbase import ModelRenderer, CodeGenerator


class PythonCodeGenerator(CodeGenerator):
    def _find_renderer_class(self, item):
        if not isinstance(item, Node):
            return None

        name = item.__class__.__name__
        renderer = globals().get(name)
        if not renderer or not issubclass(renderer, Base):
            raise CodegenError('Renderer for %s not found' % name)
        return renderer


def codegen(model):
    return PythonCodeGenerator().render(model)


class Base(ModelRenderer):
    def defines(self):
        return self.node.defines()


class Void(Base):
    template = 'self._void()'


class Any(Base):
    template = 'self._any()'


class Fail(Base):
    template = 'self._fail()'


class Comment(Base):
    def render_fields(self, fields):
        lines = '\n'.join(
            '# %s' % ustr(c) for c in self.node.comment.splitlines()
        )
        fields.update(lines=lines)

    template = '\n{lines}\n'


class EOLComment(Comment):
    pass


class EOF(Base):
    template = 'self._check_eof()'


class _Decorator(Base):
    template = '{exp}'


class Group(_Decorator):
    template = '''\
                with self._group():
                {exp:1::}\
                '''


class Token(Base):
    def render_fields(self, fields):
        fields.update(token=urepr(self.node.token))

    template = "self._token({token})"


class Constant(Base):
    def render_fields(self, fields):
        fields.update(literal=urepr(self.node.literal))

    template = "self._constant({literal})"


class Pattern(Base):
    def render_fields(self, fields):
        raw_repr = 'r' + urepr(self.node.pattern).replace("\\\\", '\\')
        fields.update(pattern=raw_repr)

    template = 'self._pattern({pattern})'


class Lookahead(_Decorator):
    template = '''\
                with self._if():
                {exp:1::}\
                '''


class NegativeLookahead(_Decorator):
    template = '''\
                with self._ifnot():
                {exp:1::}\
                '''


class Sequence(Base):
    def render_fields(self, fields):
        fields.update(seq='\n'.join(self.rend(s) for s in self.node.sequence))

    template = '{seq}'


class Choice(Base):
    def render_fields(self, fields):
        template = trim(self.option_template)
        options = [
            template.format(
                option=indent(self.rend(o))) for o in self.node.options
        ]
        options = '\n'.join(o for o in options)
        firstset = ' '.join(f[0] for f in sorted(self.node.lookahead()) if f)
        if firstset:
            error = 'expecting one of: ' + firstset
        else:
            error = 'no available options'
        fields.update(n=self.counter(),
                      options=indent(options),
                      error=urepr(error)
                      )

    def render(self, **fields):
        if len(self.node.options) == 1:
            return self.rend(self.options[0], **fields)
        else:
            return super(Choice, self).render(**fields)

    option_template = '''\
                    with self._option():
                    {option}\
                    '''

    template = '''\
                with self._choice():
                {options}
                    self._error({error})\
                '''


class Closure(_Decorator):
    def render_fields(self, fields):
        fields.update(n=self.counter())

    def render(self, **fields):
        if {()} in self.node.exp.lookahead():
            raise CodegenError('may repeat empty sequence')
        return '\n' + super(Closure, self).render(**fields)

    template = '''\
                def block{n}():
                {exp:1::}
                self._closure(block{n})\
                '''


class PositiveClosure(Closure):
    template = '''\
                def block{n}():
                {exp:1::}
                self._positive_closure(block{n})\
                '''


class Join(_Decorator):
    def render_fields(self, fields):
        fields.update(n=self.counter())

    def render(self, **fields):
        if {()} in self.node.exp.lookahead():
            raise CodegenError('may repeat empty sequence')
        return '\n' + super(Join, self).render(**fields)

    template = '''\
                def sep{n}():
                {sep:1::}

                def block{n}():
                {exp:1::}
                self._join(block{n}, sep{n})\
                '''


class PositiveJoin(Join):
    template = '''\
                def sep{n}():
                {sep:1::}

                def block{n}():
                {exp:1::}
                self._positive_join(block{n}, sep{n})\
                '''


class Gather(Join):
    template = '''\
                def sep{n}():
                {sep:1::}

                def block{n}():
                {exp:1::}
                self._gather(block{n}, sep{n})\
                '''


class PositiveGather(Join):
    template = '''\
                def sep{n}():
                {sep:1::}

                def block{n}():
                {exp:1::}
                self._positive_gather(block{n}, sep{n})\
                '''


class LeftJoin(PositiveJoin):
    template = '''\
                def sep{n}():
                {sep:1::}

                def block{n}():
                {exp:1::}
                self._left_join(block{n}, sep{n})\
                '''


class RightJoin(PositiveJoin):
    template = '''\
                def sep{n}():
                {sep:1::}

                def block{n}():
                {exp:1::}
                self._right_join(block{n}, sep{n})\
                '''


class EmptyClosure(Base):
    template = 'self._empty_closure()'


class SkipTo(Closure):
    template = '''\
                def block{n}():
                {exp:1::}
                self._skip_to(block{n})\
    '''


class Optional(_Decorator):
    template = '''\
                with self._optional():
                {exp:1::}\
                '''


class Cut(Base):
    template = 'self._cut()'


class Named(_Decorator):
    def __str__(self):
        return '%s:%s' % (self.name, self.rend(self.exp))

    def render_fields(self, fields):
        fields.update(n=self.counter(),
                      name=safe_name(self.node.name)
                      )

    template = '''
                {exp}
                self.name_last_node('{name}')\
                '''


class NamedList(Named):
    template = '''
                {exp}
                self.add_last_node_to_name('{name}')\
                '''


class Override(Named):
    pass


class OverrideList(NamedList):
    pass


class Special(Base):
    pass


class RuleRef(Base):
    template = "self._{name}_()"


class RuleInclude(_Decorator):
    def render_fields(self, fields):
        super(RuleInclude, self).render_fields(fields)
        fields.update(exp=self.rend(self.node.rule.exp))

    template = '''
                {exp}
                '''


class Rule(_Decorator):
    @staticmethod
    def param_repr(p):
        if isinstance(p, (int, float)):
            return ustr(p)
        else:
            return urepr(p.split(BASE_CLASS_TOKEN)[0])

    def render_fields(self, fields):
        self.reset_counter()

        params = kwparams = ''
        if self.node.params:
            params = ', '.join(
                self.param_repr(self.rend(p))
                for p in self.node.params
            )
        if self.node.kwparams:
            kwparams = ', '.join(
                '%s=%s'
                %
                (k, self.param_repr(self.rend(v)))
                for k, v in self.kwparams.items()
            )

        if params and kwparams:
            params = params + ', ' + kwparams
        elif kwparams:
            params = kwparams

        fields.update(params=params)

        defines = compress_seq(self.defines())
        ldefs = set(safe_name(d) for d, l in defines if l)
        sdefs = set(safe_name(d) for d, l in defines if not l and d not in ldefs)

        if not (sdefs or ldefs):
            sdefines = ''
        else:
            sdefs = '[%s]' % ', '.join(urepr(d) for d in sorted(sdefs))
            ldefs = '[%s]' % ', '.join(urepr(d) for d in sorted(ldefs))
            if not ldefs:
                sdefines = '\n\n    self.ast._define(%s, %s)' % (sdefs, ldefs)
            else:
                sdefines = indent(
                    '\n' +
                    trim(self.define_template % (sdefs, ldefs))
                )

        fields.update(defines=sdefines)
        fields.update(
            check_name='\n    self._check_name()' if self.is_name else '',
        )

    template = '''
        @tatsumasu({params})
        def _{name}_(self):  # noqa
        {exp:1::}{check_name}{defines}
        '''

    define_template = '''\
            self.ast._define(
                %s,
                %s
            )\
        '''


class BasedRule(Rule):
    def defines(self):
        return self.rhs.defines()

    def render_fields(self, fields):
        super(BasedRule, self).render_fields(fields)
        fields.update(exp=self.rhs)


class Grammar(Base):
    def render_fields(self, fields):
        abstract_template = trim(self.abstract_rule_template)
        abstract_rules = [
            abstract_template.format(name=safe_name(rule.name))
            for rule in self.node.rules
        ]
        abstract_rules = indent('\n'.join(abstract_rules))

        if self.node.whitespace is not None:
            whitespace = urepr(self.node.whitespace)
        elif self.node.directives.get('whitespace') is not None:
            whitespace = 're.compile({0})'.format(urepr(self.node.directives.get('whitespace')))
        else:
            whitespace = 'None'

        if self.node.nameguard is not None:
            nameguard = urepr(self.node.nameguard)
        elif self.node.directives.get('nameguard') is not None:
            nameguard = self.node.directives.get('nameguard')
        else:
            nameguard = 'None'

        comments_re = urepr(self.node.directives.get('comments'))
        eol_comments_re = urepr(self.node.directives.get('eol_comments'))
        ignorecase = self.node.directives.get('ignorecase', 'None')
        left_recursion = self.node.directives.get('left_recursion', True)
        parseinfo = self.node.directives.get('parseinfo', True)

        namechars = urepr(self.node.directives.get('namechars') or '')

        rules = '\n'.join([
            self.get_renderer(rule).render() for rule in self.node.rules
        ])

        version = str(tuple(int(n) for n in str(timestamp()).split('.')))

        keywords = '\n'.join("    %s," % urepr(k) for k in sorted(self.keywords))
        if keywords:
            keywords = '\n%s\n' % keywords

        fields.update(rules=indent(rules),
                      abstract_rules=abstract_rules,
                      version=version,
                      whitespace=whitespace,
                      nameguard=nameguard,
                      ignorecase=ignorecase,
                      comments_re=comments_re,
                      eol_comments_re=eol_comments_re,
                      left_recursion=left_recursion,
                      parseinfo=parseinfo,
                      keywords=keywords,
                      namechars=namechars,
                      )

    abstract_rule_template = '''
            def {name}(self, ast):  # noqa
                return ast
            '''

    template = '''\
                #!/usr/bin/env python
                # -*- coding: utf-8 -*-

                # CAVEAT UTILITOR
                #
                # This file was automatically generated by TatSu.
                #
                #    https://pypi.python.org/pypi/tatsu/
                #
                # Any changes you make to it will be overwritten the next time
                # the file is generated.


                from __future__ import print_function, division, absolute_import, unicode_literals

                from tatsu.buffering import Buffer
                from tatsu.parsing import Parser
                from tatsu.parsing import tatsumasu
                from tatsu.util import re, generic_main  # noqa


                KEYWORDS = {{{keywords}}}  # type: ignore


                class {name}Buffer(Buffer):
                    def __init__(
                        self,
                        text,
                        whitespace={whitespace},
                        nameguard={nameguard},
                        comments_re={comments_re},
                        eol_comments_re={eol_comments_re},
                        ignorecase={ignorecase},
                        namechars={namechars},
                        **kwargs
                    ):
                        super({name}Buffer, self).__init__(
                            text,
                            whitespace=whitespace,
                            nameguard=nameguard,
                            comments_re=comments_re,
                            eol_comments_re=eol_comments_re,
                            ignorecase=ignorecase,
                            namechars=namechars,
                            **kwargs
                        )


                class {name}Parser(Parser):
                    def __init__(
                        self,
                        whitespace={whitespace},
                        nameguard={nameguard},
                        comments_re={comments_re},
                        eol_comments_re={eol_comments_re},
                        ignorecase={ignorecase},
                        left_recursion={left_recursion},
                        parseinfo={parseinfo},
                        keywords=None,
                        namechars={namechars},
                        buffer_class={name}Buffer,
                        **kwargs
                    ):
                        if keywords is None:
                            keywords = KEYWORDS
                        super({name}Parser, self).__init__(
                            whitespace=whitespace,
                            nameguard=nameguard,
                            comments_re=comments_re,
                            eol_comments_re=eol_comments_re,
                            ignorecase=ignorecase,
                            left_recursion=left_recursion,
                            parseinfo=parseinfo,
                            keywords=keywords,
                            namechars=namechars,
                            buffer_class=buffer_class,
                            **kwargs
                        )

                {rules}


                class {name}Semantics(object):
                {abstract_rules}


                def main(filename, startrule, **kwargs):
                    with open(filename) as f:
                        text = f.read()
                    parser = {name}Parser()
                    return parser.parse(text, startrule, filename=filename, **kwargs)


                if __name__ == '__main__':
                    import json
                    from tatsu.util import asjson

                    ast = generic_main(main, {name}Parser, name='{name}')
                    print('AST:')
                    print(ast)
                    print()
                    print('JSON:')
                    print(json.dumps(asjson(ast), indent=2))
                    print()
                '''
