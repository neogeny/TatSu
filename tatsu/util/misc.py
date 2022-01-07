from __future__ import annotations

import re

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


def findalliter(pattern, string, flags=0):
    '''
        like finditer(), but with return values like findall()

        implementation taken from cpython/Modules/_sre.c/findall()
    '''
    for m in re.finditer(pattern, string, flags=flags):
        default = string[0:0]
        g = m.groups(default=default)
        if len(g) == 1:
            yield g[0]
        elif g:
            yield g
        else:
            yield m.group()


def findfirst(pattern, string, flags=0, default=_undefined):
    """
    Avoids using the inefficient findall(...)[0], or first(findall(...))
    """
    return first(findalliter(pattern, string, flags=flags), default=default)
