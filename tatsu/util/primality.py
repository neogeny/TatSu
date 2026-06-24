#!/usr/bin/env python
"""
Solution to Project Euler Problem
http://projecteuler.net/

by Apalala <apalala@gmail.com>
(cc) 2011 Attribution-ShareAlike
http://creativecommons.org/licenses/by-sa/3.0/

Prime numbers.
"""

from bisect import bisect_left as bisect
from itertools import count
from math import sqrt


__primes = [
    2,
    3,
    5,
    7,
    11,
    13,
    17,
    19,
    23,
    29,
    31,
    37,
    41,
    43,
    47,
    53,
    59,
    61,
    67,
    71,
    73,
    79,
    83,
    89,
    97,
]


def nth_prime(n):
    global __primes
    if not __primes:
        __primes = [2]

    if n <= len(__primes):
        return __primes[n - 1]

    i = __primes[-1]
    limit = 1 + bisect(__primes, int(sqrt(i)))
    while len(__primes) < n:
        i += 2
        while __primes[limit] ** 2 <= i:
            limit += 1
        if all(i % p for p in __primes[1:limit]):
            __primes.append(i)
    return __primes[-1]


def known_prime(n):
    if n <= __primes[-1]:
        i = bisect(__primes, n)
        return __primes[i] == n
    return False


def is_prime(n):
    n = abs(n)
    if n < 2:
        return False
    elif known_prime(n):
        return True
    else:
        return all(n % p for p in primes_upto(n))


def all_primes():
    for n in count(1):
        yield nth_prime(n)


def primes_upto(m, start=2):
    for p in all_primes():
        if p < start:
            continue
        if p > m:
            break
        yield p
