from __future__ import annotations

from tatsu.util import re


class ParseException(Exception):
    pass


# alias
TatSuException = ParseException


class OptionSucceeded(ParseException):
    pass


class GrammarError(ParseException):
    pass


class SemanticError(ParseException):
    pass


class CodegenError(ParseException):
    pass


class MissingSemanticFor(SemanticError):
    pass


class ParseError(ParseException):
    pass


class FailedSemantics(ParseError):
    pass


class FailedKeywordSemantics(FailedSemantics):
    pass


class NoParseInfo(ParseException):
    pass


class FailedParse(ParseError):
    def __init__(self, tokenizer, stack, item):
        # note: pass all arguments to super() to avoid pickling problems
        #   https://stackoverflow.com/questions/27993567/
        super().__init__(tokenizer, stack, item)

        self.tokenizer = tokenizer
        self.stack = stack[:]
        self.pos = tokenizer.pos
        self.item = item

    @property
    def message(self):
        return self.item

    def __str__(self):
        info = self.tokenizer.line_info(self.pos)
        template = "{}({}:{}) {} :\n{}\n{}^\n{}"
        text = info.text.rstrip()
        leading = re.sub(r'[^\t]', ' ', text)[:info.col]

        text = text.expandtabs()
        leading = leading.expandtabs()
        return template.format(info.filename,
                               info.line + 1, info.col + 1,
                               self.message.rstrip(),
                               text,
                               leading,
                               '\n'.join(reversed(self.stack))
                               )


class FailedToken(FailedParse):
    def __init__(self, tokenizer, stack, token):
        super().__init__(tokenizer, stack, token)
        self.token = token

    @property
    def message(self):
        return "expecting %s" % repr(self.token).lstrip('u')


class FailedPattern(FailedParse):
    def __init__(self, tokenizer, stack, pattern):
        super().__init__(tokenizer, stack, pattern)
        self.pattern = pattern

    @property
    def message(self):
        return "expecting /%s/" % self.pattern


class FailedRef(FailedParse):
    def __init__(self, tokenizer, stack, name):
        super().__init__(tokenizer, stack, name)
        self.name = name

    @property
    def message(self):
        return "could not resolve reference to rule '%s'" % self.name


class FailedCut(FailedParse):
    def __init__(self, nested):
        super().__init__(nested.tokenizer, nested.stack, nested.item)
        self.pos = nested.pos
        self.nested = nested

    @property
    def message(self):
        return self.nested.message


class FailedChoice(FailedParse):
    @property
    def message(self):
        return 'no viable option'


class FailedLookahead(FailedParse):
    @property
    def message(self):
        return 'failed lookahead'


class FailedLeftRecursion(FailedParse):
    @property
    def message(self):
        return 'infinite left recursion'


class FailedExpectingEndOfText(FailedParse):
    pass


class FailedKeyword(FailedParse):
    pass
