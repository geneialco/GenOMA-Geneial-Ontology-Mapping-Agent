"""
Utility functions for flattening nested data structures.
"""

from typing import Any


def flatten_names(name_set: list[Any]) -> list[Any]:
    """
    Recursively flatten a nested list structure.

    Args:
        name_set: A list that may contain nested lists

    Returns:
        A flat list with all nested elements extracted
    """
    flat_names = []
    for item in name_set:
        if isinstance(item, list):
            flat_names.extend(flatten_names(item))
        else:
            flat_names.append(item)
    return flat_names
