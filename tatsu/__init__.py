from __future__ import annotations

from ._config import __toolname__, __version__
from .tool import (  # pylint: disable=W0622
    compile,
    main,
    parse,
    to_python_model,
    to_python_sourcecode,
)

assert __version__
assert __toolname__
assert bool(compile)
assert bool(parse)
assert bool(to_python_sourcecode)
assert bool(to_python_model)


if __name__ == '__main__':
    main()
