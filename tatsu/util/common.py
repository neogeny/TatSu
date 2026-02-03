from __future__ import annotations

import datetime
import logging
import os
import os.path
import sys
from io import StringIO
from pathlib import Path
from typing import Any

logger = logging.getLogger('TatSu')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def program_name() -> str:
    import __main__ as main
    if package := main.__package__:
        return package
    elif isinstance(main.__file__, str):
        return Path(main.__file__).name
    else:
        return 'unknown'


def is_posix() -> bool:
    return os.name == 'posix'


def prints(*args, **kwargs: Any) -> str:
    with StringIO() as f:
        kwargs['file'] = f
        kwargs['end'] = ''
        print(*args, **kwargs)
        return f.getvalue()


def info(*args: Any, **kwargs: Any) -> None:
    logger.info(prints(*args, **kwargs))


def debug(*args: Any, **kwargs: Any) -> None:
    logger.debug(prints(*args, **kwargs))


def warning(*args: Any, **kwargs: Any) -> None:
    logger.warning(prints(*args, **kwargs))


def error(*args: Any, **kwargs: Any) -> None:
    logger.error(prints(*args, **kwargs))


def identity(*args: Any) -> Any:
    if len(args) == 1:
        return args[0]
    return args


def format_if(fmt, values):
    return fmt % values if values else ''


def timestamp():
    return '.'.join(
        '%2.2d' % t for t in datetime.datetime.now(datetime.UTC).utctimetuple()[:-2]
    )


try:
    import psutil
except ImportError:

    def memory_use():
        return 0

else:

    def memory_use():
        process = psutil.Process(os.getpid())
        return process.memory_info().rss


def try_read(filename):
    if isinstance(filename, Path):
        filename = str(filename)
    for e in ['utf-16', 'utf-8', 'latin-1', 'cp1252', 'ascii']:
        try:
            return Path(filename).read_text(encoding=e)
        except UnicodeError:
            pass
    raise ValueError(f"cannot find the encoding for '{filename}'")


def filelist_from_patterns(patterns, ignore=None, base='.', sizesort=False):
    ignore = ignore or ()
    base = Path(base or '.').expanduser()

    filenames = set()
    for pattern in patterns or []:
        path = base / pattern
        if path.is_file():
            filenames.add(path)
            continue

        if path.is_dir():
            path += '/*'

        parts = path.parts[1:] if path.is_absolute() else path.parts
        joined_pattern = str(Path().joinpath(*parts))
        filenames.update(
            p for p in Path(path.root).glob(joined_pattern) if not p.is_dir()
        )

    filenames = list(filenames)

    def excluded(path):
        if any(path.match(ex) for ex in ignore):
            return True

        return any(
            any(Path(part).match(ex) for ex in ignore or ()) for part in path.parts
        )

    if ignore:
        filenames = [path for path in filenames if not excluded(path)]
    if sizesort:
        filenames.sort(key=lambda f: f.stat().st_size)

    return filenames


def short_relative_path(path: str | Path, base: str | Path = '.') -> Path:
    path = Path(path)
    base = Path(base)
    common = Path(os.path.commonpath([base.resolve(), path.resolve()]))

    if common == path.root:
        return path
    elif common == Path.home():
        up = Path('~')
    elif common == base:
        up = Path()
    else:
        n = len(base.parts) - len(common.parts)
        up = Path('../' * n)

    rel = up / path.resolve().relative_to(common)
    if len(str(rel)) < len(str(path)):
        return rel
    else:
        return path
