from __future__ import annotations

from tatsu._config import __version__
from tatsu._config import __toolname__
from tatsu.tool import (  # pylint: disable=W0622
    main,
    compile,
    parse,
    to_python_sourcecode,
    to_python_model,
)

assert __version__
assert __toolname__
assert compile
assert parse
assert to_python_sourcecode
assert to_python_model


if __name__ == '__main__':
    main()
