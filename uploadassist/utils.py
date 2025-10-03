# utils.py
"""
Utility functions for uploadassist.
"""

import re
import math
from urllib.request import urlopen as _urlopen


def target():
    """
    Placeholder for target function.
    """
    pass


def sizeof_fmt(num, suffix="B"):
    """
    Human-readable file size.
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Y", suffix)


def _eat(iterator):
    """
    Consume an iterator.
    """
    for _ in iterator:
        pass


def expect(condition, msg):
    """
    Raise an error if condition is False.
    """
    if not condition:
        raise RuntimeError(msg)


def expect_re(pattern, string, msg):
    """
    Raise an error if regex pattern does not match string.
    """
    if not re.search(pattern, string):
        raise RuntimeError(msg)


def urlopen(*args, **kwargs):
    """
    Wrapper for urllib.request.urlopen.
    """
    return _urlopen(*args, **kwargs)
