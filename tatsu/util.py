# -*- coding: utf-8 -*-
from __future__ import generator_stop

import sys
import os
import json
import datetime
import codecs
import keyword
import functools
import warnings
import logging
from io import StringIO
from collections import OrderedDict
from collections.abc import Mapping, Iterable
from itertools import zip_longest


logger = logging.getLogger('tatsu')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter(str('%(message)s'))
ch.setFormatter(formatter)
logger.addHandler(ch)


try:
    import regex as re
    WHITESPACE_RE = re.compile(r'\p{IsPattern_White_Space}+')
except ImportError:
    import re  # type: ignore
    WHITESPACE_RE = re.compile(r'(?s)\s+')
RETYPE = type(re.compile('.'))


_PY3 = sys.version_info[0] >= 3
PY35 = _PY3 and sys.version_info[1] >= 5
PY37 = _PY3 and sys.version_info[1] >= 7


def is_posix():
    return os.name == 'posix'


def _prints(*args, **kwargs):
    io = StringIO()
    kwargs['file'] = io
    kwargs['end'] = ''
    print(*args, **kwargs)
    return io.getvalue()


def info(*args, **kwargs):
    logger.info(_prints(*args, **kwargs))


def debug(*args, **kwargs):
    logger.debug(_prints(*args, **kwargs))


def warning(*args, **kwargs):
    logger.warning(_prints('WARNING:', *args, **kwargs))


def identity(*args):
    if len(args) == 1:
        return args[0]
    return args


def is_list(o):
    return type(o) == list


def to_list(o):
    if o is None:
        return []
    elif isinstance(o, list):
        return o
    else:
        return [o]


def simplify_list(x):
    if isinstance(x, list) and len(x) == 1:
        return simplify_list(x[0])
    return x


def extend_list(x, n, default=None):
    def _null():
        pass
    default = default or _null

    missing = max(0, 1 + n - len(x))
    x.extend(default() for _ in range(missing))


def contains_sublist(lst, sublst):
    n = len(sublst)
    return any(sublst == lst[i:i + n] for i in range(1 + len(lst) - n))


def join_lists(lists):
    return sum(lists, [])


def flatten(o):
    def _flatten(x):
        if not is_list(x):
            yield x
            return

        for item in o:
            for result in flatten(item):
                yield result

    return list(_flatten(o))


def compress_seq(seq):
    seen = set()
    result = []
    for x in seq:
        if x not in seen:
            result.append(x)
            seen.add(x)
    return result


def eval_escapes(s):
    """
    Given a string, evaluate escape sequences starting with backslashes as
    they would be evaluated in Python source code. For a list of these
    sequences, see: https://docs.python.org/3/reference/lexical_analysis.html

    This is not the same as decoding the whole string with the 'unicode-escape'
    codec, because that provides no way to handle non-ASCII characters that are
    literally present in the string.
    """
    # by Rob Speer

    escape_sequence_re = re.compile(
        r'''
        ( \\U........      # 8-digit Unicode escapes
        | \\u....          # 4-digit Unicode escapes
        | \\x..            # 2-digit Unicode escapes
        | \\[0-7]{1,3}     # Octal character escapes
        | \\N\{[^}]+\}     # Unicode characters by name
        | \\[\\'"abfnrtv]  # Single-character escapes
        )''',
        re.UNICODE | re.VERBOSE
    )

    def decode_match(match):
        return codecs.decode(match.group(0), 'unicode-escape')

    return escape_sequence_re.sub(decode_match, s)


def isiter(value):
    return (
        isinstance(value, Iterable) and
        not isinstance(value, str)
    )


def trim(text, tabwidth=4):
    """
    Trim text of common, leading whitespace.

    Based on the trim algorithm of PEP 257:
        http://www.python.org/dev/peps/pep-0257/
    """
    if not text:
        return ''
    lines = text.expandtabs(tabwidth).splitlines()
    maxindent = len(text)
    indent = maxindent
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    trimmed = (
        [lines[0].strip()] +
        [line[indent:].rstrip() for line in lines[1:]]
    )
    i = 0
    while i < len(trimmed) and not trimmed[i]:
        i += 1
    return '\n'.join(trimmed[i:])


def indent(text, indent=1, multiplier=4):
    """ Indent the given block of text by indent*4 spaces
    """
    if text is None:
        return ''
    text = str(text)
    if indent >= 0:
        sindent = ' ' * multiplier * indent
        text = '\n'.join((sindent + t).rstrip() for t in text.splitlines())
    return text


def format_if(fmt, values):
    return fmt % values if values else ''


def notnone(value, default=None):
    return value if value is not None else default


def timestamp():
    return '.'.join('%2.2d' % t for t in datetime.datetime.utcnow().utctimetuple()[:-2])


def asjson(obj, seen=None):
    if isinstance(obj, Mapping) or isiter(obj):
        # prevent traversal of recursive structures
        if seen is None:
            seen = set()
        elif id(obj) in seen:
            return '__RECURSIVE__'
        seen.add(id(obj))

    if hasattr(obj, '__json__') and type(obj) is not type:
        return obj.__json__()
    elif isinstance(obj, Mapping):
        result = OrderedDict()
        for k, v in obj.items():
            try:
                result[asjson(k, seen)] = asjson(v, seen)
            except TypeError:
                debug('Unhashable key?', type(k), str(k))
                raise
        return result
    elif isiter(obj):
        return [asjson(e, seen) for e in obj]
    else:
        return obj


def asjsons(obj):
    return json.dumps(asjson(obj), indent=2)


def prune_dict(d, predicate):
    """ Remove all items x where predicate(x, d[x]) """

    keys = [k for k, v in d.items() if predicate(k, v)]
    for k in keys:
        del d[k]


def safe_name(name):
    if keyword.iskeyword(name):
        return name + '_'
    return name


def chunks(iterable, size, fillvalue=None):
    return zip_longest(*[iter(iterable)] * size, fillvalue=fillvalue)


def generic_main(custom_main, parser_class, name='Unknown'):
    import argparse

    class ListRules(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            print('Rules:')
            for r in parser_class.rule_list():
                print(r)
            print()
            sys.exit(0)

    argp = argparse.ArgumentParser(description="Simple parser for %s." % name)
    addarg = argp.add_argument

    addarg('-c', '--color',
           help='use color in traces (requires the colorama library)',
           action='store_true'
           )
    addarg('-l', '--list', action=ListRules, nargs=0,
           help="list all rules and exit")
    addarg('-n', '--no-nameguard', action='store_true',
           dest='no_nameguard',
           help="disable the 'nameguard' feature")
    addarg('-t', '--trace', action='store_true',
           help="output trace information")
    addarg('-w', '--whitespace', type=str, default=None,
           help="whitespace specification")
    addarg('file',
           metavar="FILE",
           help="the input file to parse or '-' for standard input",
           nargs='?',
           default='-')
    addarg('startrule',
           metavar="STARTRULE",
           nargs='?',
           help="the start rule for parsing",
           default=None)

    args = argp.parse_args()
    try:
        return custom_main(
            args.file,
            start=args.startrule,
            trace=args.trace,
            whitespace=args.whitespace,
            nameguard=not args.no_nameguard,
            colorize=args.color
        )
    except KeyboardInterrupt:
        pass


# decorator
def deprecated(fun):
    @functools.wraps(fun)
    def wrapper(*args, **kwargs):
        warnings.filterwarnings('default', category=DeprecationWarning)
        msg = "Call to deprecated function {}."
        warnings.warn(
            msg.format(fun.__name__),
            category=DeprecationWarning,
            stacklevel=2,
        )
        return fun(*args, **kwargs)

    return wrapper


def left_assoc(elements):
    if not elements:
        return ()

    it = iter(elements)
    expre = next(it)
    for e in it:
        op = e
        expre = (op, expre, next(it))
    return expre


def right_assoc(elements):
    if not elements:
        return ()

    def assoc(it):
        left = next(it)
        try:
            op = next(it)
        except StopIteration:
            return left
        else:
            return (op, left, assoc(it))

    return assoc(iter(elements))
