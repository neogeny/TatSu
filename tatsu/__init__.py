from __future__ import annotations

from ._config import __version__
from ._config import __toolname__
from .tool import (  # pylint: disable=W0622
    main,
    compile,
    parse,
    to_python_sourcecode,
    to_python_model,
)

assert __version__
assert __toolname__
assert bool(compile)
assert bool(parse)
assert bool(to_python_sourcecode)
assert bool(to_python_model)


if __name__ == '__main__':
    main()
