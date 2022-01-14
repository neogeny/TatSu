from __future__ import annotations

import re

from ._common import RETYPE

_undefined = object()  # unique object for when None is not a good default


def first(iterable, default=_undefined):
    """Return the first item of *iterable*, or *default* if *iterable* is
    empty.

        >>> first([0, 1, 2, 3])
        0
        >>> first([], 'some default')
        'some default'

    If *default* is not provided and there are no items in the iterable,
    raise ``ValueError``.

    :func:`first` is useful when you have a generator of expensive-to-retrieve
    values and want any arbitrary one. It is marginally shorter than
    ``next(iter(iterable), default)``.

    """
    # NOTE: https://more-itertools.readthedocs.io/en/stable/_modules/more_itertools/more.html#first
    try:
        return next(iter(iterable))
    except StopIteration:
        # I'm on the edge about raising ValueError instead of StopIteration. At
        # the moment, ValueError wins, because the caller could conceivably
        # want to do something different with flow control when I raise the
        # exception, and it's weird to explicitly catch StopIteration.
        if default is _undefined:
            raise ValueError('first() was called on an empty iterable, and no '
                             'default value was provided.')
        return default


def match_to_find(m: re.Match):
    if m is None:
        return None
    g = m.groups(default=m.string[0:0])
    if len(g) == 1:
        return g[0]
    elif g:
        return g
    else:
        return m.group()


def findalliter(pattern, string, pos=None, endpos=None, flags=0):
    '''
        like finditer(), but with return values like findall()

        implementation taken from cpython/Modules/_sre.c/findall()
    '''
    if isinstance(pattern, RETYPE):
        r = pattern
    else:
        r = re.compile(pattern, flags=flags)
    if endpos is not None:
        iterator = r.finditer(string, pos=pos, endpos=endpos)
    elif pos is not None:
        iterator = r.finditer(string, pos=pos)
    else:
        iterator = r.finditer(string)
    for m in iterator:
        yield match_to_find(m)


def findfirst(pattern, string, pos=None, endpos=None, flags=0, default=_undefined):
    """
    Avoids using the inefficient findall(...)[0], or first(findall(...))
    """
    return first(findalliter(pattern, string, pos=pos, endpos=endpos, flags=flags), default=default)
