import io
from contextlib import contextmanager

from ..util import trim


class IndentPrintMixin:
    def __init__(self, default_indent: int = 4):
        self.default_indent = default_indent
        self.indent_stack: list[int] = [0]
        self.output_stream = io.StringIO()

    def printed_text(self):
        return self.output_stream.getvalue()

    def print(self, *args, **kwargs):
        args = [trim(str(arg)) for arg in args if arg is not None]
        lines = self.as_printed_lines(*args, **kwargs)
        self._do_print_lines(lines, **kwargs)

    def as_printed(self, *args, **kwargs):
        lines = self.as_printed_lines(*args, **kwargs)
        return '\n'.join(lines)

    def as_printed_lines(self, *args, **kwargs):
        text = self.io_print(*args, **kwargs)
        return self.indented_lines(text)

    @contextmanager
    def indent(self, amount: int | None = None):
        assert amount is None or amount >= 0
        if amount is None:
            amount = self.default_indent

        self.indent_stack.append(amount + self.indent_stack[-1])
        try:
            yield
        finally:
            self.indent_stack.pop()

    @property
    def current_indentation(self):
        return ' ' * self.indent_stack[-1]

    @staticmethod
    def io_print(*args, **kwargs):
        kwargs.pop('file', None)  # do not allow redirection of output
        with io.StringIO() as output:
            print(*args, file=output, **kwargs)
            return output.getvalue()

    def _do_print_lines(self, lines: list[str] | None = None, **kwargs):
        if not lines:
            print(file=self.output_stream, **kwargs)
            return

        for line in lines:
            print(line, file=self.output_stream, **kwargs)

    def indented_lines(self, text):
        text = trim(text)
        return [
            (self.current_indentation + line).rstrip()
            for line in text.splitlines(keepends=False)
        ]
